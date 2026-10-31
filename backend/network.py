"""Restricted outbound HTTP for providers and unauthenticated image downloads.

Proxy modes are disabled by default. An operator may set PHOTOAI_ALLOW_PROXIES
as a JSON array of exact proxy endpoints without credentials or paths, e.g.
["http://127.0.0.1:7890", "socks5://proxy.example:1080"]. Listing an endpoint
attests that this trusted proxy itself enforces public-only target DNS/egress,
including redirects and DNS rebinding. Do not list an unrestricted proxy.
Credentials in a visitor proxy URL do not participate in endpoint comparison.
Environment mode reads HTTP_PROXY, HTTPS_PROXY, ALL_PROXY and NO_PROXY (also
lowercase), from this server environment only, never Windows system settings.

Direct connections validate all A/AAAA answers and connect to a numeric address.
httpcore retains the original hostname for Host and TLS SNI/certificate checks.
Proxy targets also undergo public DNS validation; remote resolution is trusted
only under the explicit operator contract above. TLS verification, no redirects
and zero connection retries apply to every mode. Tests can inject MockTransport;
there is deliberately no production switch permitting local upstream servers.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import ipaddress
import json
import os
import socket
import ssl
from urllib.parse import urlsplit, urlunsplit
from urllib.request import proxy_bypass_environment

import certifi
import httpcore
import httpx

try:
    from httpcore._backends.auto import AutoBackend
except ImportError:  # httpcore before 1.x, useful in existing test environments.
    from httpcore.backends.auto import AutoBackend

from backend.errors import GenError

MAX_URL_LENGTH = 4096
_TRANSITION_NETWORKS = tuple(ipaddress.ip_network(cidr) for cidr in (
    "64:ff9b::/96", "64:ff9b:1::/48", "2001::/32", "2002::/16",
))


def _clean_url(value, *, proxy=False):
    if not isinstance(value, str) or len(value) > MAX_URL_LENGTH:
        raise GenError("network", "Invalid outbound address.")
    if any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in value) or "\\" in value:
        raise GenError("network", "Invalid outbound address.")
    value = value.strip()
    try:
        parsed = urlsplit(value)
        schemes = ("http", "https", "socks5", "socks5h") if proxy else ("http", "https")
        if parsed.scheme.lower() not in schemes or not parsed.hostname or parsed.fragment:
            raise ValueError
        if not proxy and (parsed.username is not None or parsed.password is not None):
            raise ValueError
        if "%" in parsed.hostname or any(char.isspace() for char in parsed.netloc):
            raise ValueError
        if parsed.port is not None and not 1 <= parsed.port <= 65535:
            raise ValueError
        parsed.hostname.encode("idna")
        if proxy and (parsed.query or parsed.path not in ("", "/")):
            raise ValueError
    except (ValueError, UnicodeError):
        raise GenError("network", "Invalid outbound address.") from None
    return parsed


def validate_url(value: str) -> str:
    """Check HTTP URL syntax; DNS checks occur at the transport boundary."""
    return urlunsplit(_clean_url(value))


def normalize_proxy_url(value: str) -> str:
    parsed = _clean_url(value, proxy=True)
    return urlunsplit((parsed.scheme.lower(), parsed.netloc, "", "", ""))


def proxy_endpoint(value: str) -> str:
    """Credential-free canonical endpoint used by the operator allowlist."""
    parsed = _clean_url(value, proxy=True)
    host = parsed.hostname.encode("idna").decode("ascii").lower().rstrip(".")
    if ":" in host:
        host = "[" + host + "]"
    port = parsed.port or {"http": 80, "https": 443, "socks5": 1080, "socks5h": 1080}[parsed.scheme]
    return f"{parsed.scheme}://{host}:{port}"


def public_address(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    if isinstance(address, ipaddress.IPv6Address):
        if address.ipv4_mapped is not None:
            return public_address(str(address.ipv4_mapped))
        if address.is_site_local:
            return False
        if any(address in network for network in _TRANSITION_NETWORKS):
            return False
    return bool(address.is_global and not (
        address.is_private or address.is_loopback or address.is_link_local
        or address.is_multicast or address.is_reserved or address.is_unspecified
    ))


async def resolve_public(host: str, port: int, timeout: float = 10.0) -> list[str]:
    """Reject the entire DNS answer if any record is nonpublic."""
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        addresses = [str(literal)]
    else:
        if host.rstrip(".").lower() in ("localhost", "localhost.localdomain") or "%" in host:
            raise GenError("network", "Private or local outbound addresses are not allowed.")
        try:
            records = await asyncio.wait_for(
                asyncio.get_running_loop().getaddrinfo(
                    host, port, family=socket.AF_UNSPEC,
                    type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP,
                ), timeout=timeout,
            )
            addresses = list(dict.fromkeys(record[4][0] for record in records))
        except (OSError, UnicodeError, asyncio.TimeoutError):
            raise GenError("network", "Could not resolve a public upstream address.", 502) from None
    if not addresses or any(not public_address(address) for address in addresses):
        raise GenError("network", "Private or local outbound addresses are not allowed.")
    return addresses


class PinnedBackend(AutoBackend):
    async def connect_tcp(self, host, port, timeout=None, local_address=None, **kwargs):
        if isinstance(host, bytes):
            host = host.decode("ascii")
        addresses = await resolve_public(host, port, min(timeout or 10.0, 10.0))
        # The connector receives only a numeric address, eliminating DNS rebinding.
        # Pick one address only: connection retries are deliberately disabled.
        return await super().connect_tcp(
            addresses[0], port, timeout=timeout, local_address=local_address, **kwargs,
        )

    async def connect_unix_socket(self, *args, **kwargs):
        raise GenError("network", "Unix socket outbound connections are not allowed.")


def tls_context():
    return ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE") or certifi.where(),
                                      capath=os.environ.get("SSL_CERT_DIR"))


class PinnedTransport(httpx.AsyncHTTPTransport):
    def __init__(self):
        super().__init__(verify=True, trust_env=False, retries=0)
        self._pool = httpcore.AsyncConnectionPool(
            ssl_context=tls_context(), network_backend=PinnedBackend(),
            retries=0, max_connections=10, max_keepalive_connections=5,
            keepalive_expiry=5.0, http1=True, http2=False,
        )

    async def handle_async_request(self, request):
        validate_url(str(request.url))
        return await super().handle_async_request(request)


def _allowed_proxy_endpoints() -> set[str]:
    try:
        value = json.loads(os.environ.get("PHOTOAI_ALLOW_PROXIES", ""))
        if not isinstance(value, list) or not value or len(value) > 32:
            raise ValueError
        endpoints = set()
        for entry in value:
            parsed = _clean_url(entry, proxy=True)
            if parsed.username is not None or parsed.password is not None:
                raise ValueError
            endpoints.add(proxy_endpoint(entry))
        return endpoints
    except (ValueError, TypeError, GenError):
        raise GenError(
            "network", "Proxy mode is unavailable: the operator must configure trusted proxy endpoints in PHOTOAI_ALLOW_PROXIES.",
            409,
        ) from None


class ProxyTransport(httpx.AsyncHTTPTransport):
    def __init__(self, proxy_url, allowed):
        if proxy_endpoint(proxy_url) not in allowed:
            raise GenError("network", "This proxy endpoint is not allowed by the operator.", 409)
        if proxy_url.startswith("socks5h://"):
            proxy_url = "socks5://" + proxy_url[len("socks5h://"):]
        try:
            super().__init__(verify=True, trust_env=False, retries=0, proxy=httpx.Proxy(proxy_url))
        except (ValueError, ImportError):
            raise GenError("network", "The configured proxy protocol is unavailable.", 409) from None

    async def handle_async_request(self, request):
        parsed = _clean_url(str(request.url))
        await resolve_public(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
        return await super().handle_async_request(request)


class EnvironmentTransport(httpx.AsyncBaseTransport):
    def __init__(self, allowed):
        self.direct = PinnedTransport()
        self.routes = {}
        self.no_proxy = os.environ.get("no_proxy", os.environ.get("NO_PROXY", ""))
        all_proxy = os.environ.get("all_proxy", os.environ.get("ALL_PROXY", ""))
        for scheme in ("http", "https"):
            value = os.environ.get(scheme + "_proxy", os.environ.get(scheme.upper() + "_PROXY", all_proxy))
            if value:
                self.routes[scheme] = ProxyTransport(normalize_proxy_url(value), allowed)

    async def handle_async_request(self, request):
        if proxy_bypass_environment(request.url.host, {"no": self.no_proxy}):
            transport = self.direct
        else:
            transport = self.routes.get(request.url.scheme, self.direct)
        return await transport.handle_async_request(request)

    async def aclose(self):
        await self.direct.aclose()
        for transport in self.routes.values():
            await transport.aclose()


@asynccontextmanager
async def safe_client(profile: dict, *, transport: httpx.MockTransport | None = None):
    """Yield a guarded client. Explicit MockTransport injection is for tests only."""
    if transport is not None:
        if not isinstance(transport, httpx.MockTransport):
            raise TypeError("Only MockTransport can bypass outbound network validation.")
        selected = transport
    else:
        mode = profile.get("network_mode", "direct")
        if mode == "direct":
            selected = PinnedTransport()
        elif mode == "proxy":
            allowed = _allowed_proxy_endpoints()
            selected = ProxyTransport(normalize_proxy_url(profile.get("proxy_url", "")), allowed)
        elif mode == "environment":
            selected = EnvironmentTransport(_allowed_proxy_endpoints())
        else:
            raise GenError("network", "Unknown network mode.")
    timeout = profile.get("timeout", 300)
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 1800:
        raise GenError("profile", "Timeout must be an integer from 1 to 1800 seconds.")
    async with httpx.AsyncClient(
        transport=selected, trust_env=False, follow_redirects=False,
        timeout=httpx.Timeout(timeout, connect=min(timeout, 30)),
        headers={"User-Agent": "photoai-generation/1"},
    ) as client:
        yield client
