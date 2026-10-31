"""Focused adapter/network tests. No live network or upstream billing."""
import asyncio
import base64
from contextlib import contextmanager
from email.parser import BytesParser
from email.policy import default
from io import BytesIO
import json
import os
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from PIL import Image

# Supports running this file directly as well as unittest discovery from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend import network, providers
from backend.errors import GenError


def image_bytes(fmt="PNG", color="red"):
    stream = BytesIO()
    Image.new("RGB", (3, 4), color).save(stream, format=fmt)
    return stream.getvalue()


PNG = image_bytes()
B64 = base64.b64encode(PNG).decode("ascii")
REFS = [{"data": image_bytes("JPEG", color), "mime": "image/jpeg"} for color in ("red", "blue", "green")]
PROFILE = {"kind": "openai", "base_url": "https://upstream.example", "api_key": "sk-private-test"}


class Chunks(httpx.AsyncByteStream):
    def __init__(self, data, sizes=(1, 2, 7, 3, 11)):
        self.data, self.sizes = data, sizes

    async def __aiter__(self):
        offset = index = 0
        while offset < len(self.data):
            size = self.sizes[index % len(self.sizes)]
            yield self.data[offset:offset + size]
            offset += size
            index += 1


def sse(kind, **values):
    return ("event: " + kind + "\r\ndata: " + json.dumps(values, ensure_ascii=False) + "\r\n\r\n").encode("utf-8")


@contextmanager
def upstream(handler):
    factory = network.safe_client
    transport = httpx.MockTransport(handler)
    with patch.object(providers, "safe_client", lambda profile: factory(profile, transport=transport)):
        yield


class NormalizationTests(unittest.TestCase):
    def test_base_url_versioning_and_custom(self):
        self.assertEqual(providers.normalize_base_url(" https://EXAMPLE.com/proxy/v1/v1/ "), "https://example.com/proxy/v1")
        self.assertEqual(providers.normalize_base_url("https://example.com/api/v2/", "custom"), "https://example.com/api/v2")
        self.assertEqual(providers.normalize_base_url("https://example.com", "custom"), "https://example.com")
        self.assertEqual(providers.normalize_profile({"kind": "gemini", "base_url": "https://gemini.example"})["base_url"], "https://gemini.example/v1beta")

    def test_invalid_base_urls(self):
        for value in ("https://name:secret@example.com", "https://example.com?key=x", "https://example.com#x", "https://example.com/images/generations", "https://example.com/v1/images/edits/", "https://example.com/%69mages/edits", "https://example.com/\napi", "https://example.com/\x85api", "file:///etc/passwd", "https://example.com:99999", "https://example.com\\@127.0.0.1"):
            with self.subTest(value=value), self.assertRaises(GenError):
                providers.normalize_base_url(value)

    def test_profiles_defaults_whitelist_and_types(self):
        profile = providers.normalize_profile({"kind": "relay", "model": "", "unexpected": {"api_key": "hidden"}, "clear_api_key": True})
        self.assertEqual(profile["model"], "")
        self.assertEqual(profile["timeout"], 300)
        self.assertEqual(profile["network_mode"], "direct")
        self.assertFalse(profile["stream"])
        self.assertNotIn("unexpected", profile)
        self.assertNotIn("clear_api_key", profile)
        self.assertEqual(providers.normalize_profile({"kind": "openai"})["model"], "gpt-image-2")
        self.assertEqual(providers.normalize_profile({"kind": "seedream"})["model"], "doubao-seedream-4-0-250828")
        for values in ({"timeout": True}, {"timeout": 1801}, {"stream": "false"}, {"partial_images": -1}, {"models": "foo"}, {"network_mode": "auto"}):
            with self.subTest(values=values), self.assertRaises(GenError):
                providers.normalize_profile(values)
        serialized = json.dumps(providers.DEFAULTS)
        self.assertNotIn("api_key", serialized)

    def test_parameters_whitelist_and_compression(self):
        params = providers.normalize_image_parameters({"ratio": "3:4", "output_compression": 80, "n": 4, "api_key": "secret", "arbitrary": True}, "gpt-image-2")
        self.assertEqual(params["quality"], "low")
        self.assertEqual(params["ratio"], "3:4")
        self.assertNotIn("output_compression", params)
        self.assertNotIn("arbitrary", params)
        self.assertNotIn("n", params)
        self.assertEqual(providers.normalize_image_parameters({"output_format": "webp", "output_compression": 0})["output_compression"], 0)
        for params in ({"size": "0x1024"}, {"size": "1024*1024"}, {"size": "-1x12"}, {"quality": "best"}, {"output_compression": True}, {"output_compression": 101}, {"output_format": "jpeg", "background": "transparent"}, {"moderation": "off"}):
            with self.subTest(params=params), self.assertRaises(GenError):
                providers.normalize_image_parameters(params)

    def test_image_validation(self):
        for fmt, mime in (("PNG", "image/png"), ("JPEG", "image/jpeg"), ("WEBP", "image/webp")):
            self.assertEqual(providers.validate_image(image_bytes(fmt)), mime)
        for data in (b"", b"not an image", image_bytes("GIF"), PNG[:30]):
            with self.subTest(data=data[:8]), self.assertRaises(GenError):
                providers.validate_image(data)
        with patch.object(providers, "MAX_IMAGE_PIXELS", 10), self.assertRaises(GenError):
            providers.validate_image(PNG)
        with patch.object(providers, "MAX_IMAGE_BYTES", 10), self.assertRaises(GenError):
            providers.validate_image(PNG)


class ProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_openai_text_json_single_request_multiple_results(self):
        requests = []
        async def handle(request):
            requests.append(request)
            body = json.loads(await request.aread())
            self.assertEqual(request.url.path, "/v1/images/generations")
            self.assertEqual(request.headers["authorization"], "Bearer sk-private-test")
            self.assertEqual(body["n"], 1)
            self.assertEqual(body["quality"], "low")
            self.assertNotIn("response_format", body)
            self.assertNotIn("stream", body)
            self.assertNotIn("partial_images", body)
            self.assertNotIn("ratio", body)
            self.assertNotIn("arbitrary", body)
            self.assertNotIn("output_compression", body)
            return httpx.Response(200, json={"data": [{"b64_json": B64}, {"b64_json": B64}]})
        with upstream(handle):
            result = await providers.generate(PROFILE, "first line\n第二行", {"n": 4, "arbitrary": 3}, [], None)
        self.assertEqual(result, [(PNG, "image/png"), (PNG, "image/png")])
        self.assertEqual(len(requests), 1)

    async def test_openai_edits_three_repeated_multipart_images(self):
        async def handle(request):
            self.assertEqual(request.url.path, "/v1/images/edits")
            message = BytesParser(policy=default).parsebytes(b"Content-Type: " + request.headers["content-type"].encode() + b"\r\n\r\n" + await request.aread())
            parts = list(message.iter_parts())
            files = [part for part in parts if part.get_param("name", header="content-disposition") == "image[]"]
            self.assertEqual([part.get_payload(decode=True) for part in files], [ref["data"] for ref in REFS])
            fields = {part.get_param("name", header="content-disposition"): part.get_payload(decode=True) for part in parts if not part.get_filename()}
            self.assertEqual(fields["n"], b"1")
            self.assertEqual(fields["stream"], b"true")
            self.assertEqual(fields["partial_images"], b"3")
            self.assertEqual(fields["response_format"], b"b64_json")
            return httpx.Response(200, json={"data": [{"b64_json": B64}]})
        with upstream(handle):
            result = await providers.generate(dict(PROFILE, stream=True, partial_images=3, response_format="b64_json"), "prompt", {}, REFS, None)
        self.assertEqual(result[0][0], PNG)

    async def test_relay_explicit_json_three_refs_and_alternative_field(self):
        requests = []
        async def handle(request):
            requests.append(request)
            if request.url.path.endswith("generations"):
                body = json.loads(await request.aread())
                self.assertEqual(len(body["image"]), 3)
                self.assertTrue(all(uri.startswith("data:image/jpeg;base64,") for uri in body["image"]))
                self.assertEqual(body["n"], 1)
            else:
                message = BytesParser(policy=default).parsebytes(b"Content-Type: " + request.headers["content-type"].encode() + b"\r\n\r\n" + await request.aread())
                self.assertEqual(sum(part.get_param("name", header="content-disposition") == "image" for part in message.iter_parts()), 3)
            return httpx.Response(200, json={"data": [{"b64_json": B64}]})
        with upstream(handle):
            for proto in ("json", "edits"):
                await providers.generate(dict(PROFILE, kind="relay", model="custom-image", proto=proto, field="image"), "prompt", {}, REFS, None)
        self.assertEqual(len(requests), 2)

    async def test_gemini_native_three_refs_and_auto_ratio(self):
        count = 0
        async def handle(request):
            nonlocal count
            count += 1
            self.assertEqual(request.headers["x-goog-api-key"], PROFILE["api_key"])
            self.assertNotIn("authorization", request.headers)
            self.assertIn("custom%2Fimage%3Fmodel:generateContent", request.url.raw_path.decode())
            body = json.loads(await request.aread())
            parts = body["contents"][0]["parts"]
            self.assertEqual(parts[0], {"text": "prompt"})
            self.assertEqual([base64.b64decode(part["inline_data"]["data"]) for part in parts[1:]], [ref["data"] for ref in REFS])
            self.assertEqual(body["generationConfig"]["responseModalities"], ["TEXT", "IMAGE"])
            if count == 1:
                self.assertEqual(body["generationConfig"]["imageConfig"]["aspectRatio"], "3:4")
            else:
                self.assertNotIn("imageConfig", body["generationConfig"])
            return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "done"}, {"inlineData": {"data": B64}}, {"inline_data": {"data": B64}}]}}]})
        with upstream(handle):
            for params in ({"ratio": "3:4"}, {}):
                result = await providers.generate(dict(PROFILE, kind="gemini", model="custom/image?model"), "prompt", params, REFS, None)
                self.assertEqual(len(result), 2)
        self.assertEqual(count, 2)

    async def test_seedream_native_three_refs(self):
        async def handle(request):
            body = json.loads(await request.aread())
            self.assertEqual(request.url.path, "/images/generations")
            self.assertEqual(body["n"], 1)
            self.assertEqual(len(body["image"]), 3)
            self.assertEqual(body["size"], "1728x2304")
            self.assertEqual(body["response_format"], "b64_json")
            self.assertFalse(body["watermark"])
            self.assertEqual(body["sequential_image_generation"], "disabled")
            return httpx.Response(200, json={"data": [{"b64_json": B64}]})
        with upstream(handle):
            await providers.generate(dict(PROFILE, kind="seedream"), "prompt", {"ratio": "3:4"}, REFS, None)

    async def test_qwen_native_three_refs(self):
        async def handle(request):
            if request.method == "GET":
                self.assertNotIn("authorization", request.headers)
                return httpx.Response(200, content=PNG)
            self.assertEqual(request.url.path, "/services/aigc/multimodal-generation/generation")
            body = json.loads(await request.aread())
            content = body["input"]["messages"][0]["content"]
            self.assertEqual(sum("image" in item for item in content), 3)
            self.assertEqual(content[-1], {"text": "prompt"})
            self.assertEqual(body["parameters"], {"n": 1, "size": "1536*2048", "watermark": False, "prompt_extend": True})
            return httpx.Response(200, json={"output": {"choices": [{"message": {"content": [{"image": "https://images.example/result.png"}]}}]}})
        with upstream(handle):
            self.assertEqual(await providers.generate(dict(PROFILE, kind="qwen"), "prompt", {"ratio": "3:4"}, REFS, None), [(PNG, "image/png")])

    async def test_sse_fragmentation_multiline_unicode_dedupe_and_completed(self):
        partial = sse("image_edit.partial_image", partial_image_index=0, b64_json=B64, message="预览")
        # JSON whitespace between lines is legal and SSE joins data lines using LF.
        completed = ("event: image_edit.completed\r\ndata: {\r\ndata: \"b64_json\": \"" + B64 + "\"}\r\n\r\n").encode()
        data = b": heartbeat\r\n\r\n" + partial + partial + completed + b"data: [DONE]\r\n\r\n"
        previews = []
        async def preview(*args):
            previews.append(args)
        with upstream(lambda request: httpx.Response(200, headers={"content-type": "text/event-stream; charset=utf-8"}, stream=Chunks(data))):
            result = await providers.generate(dict(PROFILE, stream=True), "prompt", {}, [], preview)
        self.assertEqual(previews, [(PNG, "image/png", 0)])
        self.assertEqual(result, [(PNG, "image/png")])

    async def test_sse_preview_arrives_before_stream_finishes(self):
        observed = asyncio.Event()
        class LiveStream(httpx.AsyncByteStream):
            async def __aiter__(self):
                yield sse("image_generation.partial_image", partial_image_index=1, b64_json=B64)
                await asyncio.wait_for(observed.wait(), 1)
                yield sse("image_generation.completed", b64_json=B64)
        async def preview(*args):
            observed.set()
        with upstream(lambda request: httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=LiveStream())):
            await providers.generate(dict(PROFILE, stream=True), "prompt", {}, [], preview)
        self.assertTrue(observed.is_set())

    async def test_stream_errors_missing_completed_invalid_index_and_error_event(self):
        cases = (
            sse("image_generation.partial_image", partial_image_index=0, b64_json=B64),
            sse("image_generation.partial_image", partial_image_index=3, b64_json=B64),
            sse("image_generation.completed", url="https://images.example/a.png"),
            sse("error", error={"message": "sk-private-test user:proxy-password"}),
        )
        for data in cases:
            with self.subTest(data=data[:80]), upstream(lambda request: httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=Chunks(data))):
                with self.assertRaises(GenError) as caught:
                    await providers.generate(dict(PROFILE, stream=True), "prompt", {}, [], None)
                self.assertNotIn("sk-private-test", str(caught.exception))
                self.assertNotIn("proxy-password", str(caught.exception))

    async def test_stream_bounds_json_fallback_no_retry(self):
        calls = 0
        async def handle(request):
            nonlocal calls
            calls += 1
            return httpx.Response(200, json={"data": [{"b64_json": B64}]})
        with upstream(handle):
            self.assertEqual(await providers.generate(dict(PROFILE, stream=True), "prompt", {}, [], None), [(PNG, "image/png")])
        self.assertEqual(calls, 1)
        with patch.object(providers, "MAX_SSE_LINE_BYTES", 8), upstream(lambda request: httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=Chunks(b"data: " + b"x" * 40))):
            with self.assertRaises(GenError):
                await providers.generate(dict(PROFILE, stream=True), "prompt", {}, [], None)

    async def test_url_download_no_upstream_key_and_no_redirect_follow(self):
        seen = []
        async def handle(request):
            seen.append(request)
            if request.method == "POST":
                return httpx.Response(200, json={"data": [{"url": "https://images.example/result?sig=public"}]})
            self.assertNotIn("authorization", request.headers)
            self.assertNotIn("x-goog-api-key", request.headers)
            return httpx.Response(200, content=PNG, headers={"content-type": "text/plain"})
        with upstream(handle):
            self.assertEqual(await providers.generate(PROFILE, "prompt", {}, [], None), [(PNG, "image/png")])
        self.assertEqual([request.method for request in seen], ["POST", "GET"])
        with upstream(lambda request: httpx.Response(302, headers={"location": "http://127.0.0.1/secret"})):
            with self.assertRaises(GenError) as caught:
                await providers.generate(PROFILE, "prompt", {}, [], None)
            self.assertEqual(caught.exception.kind, "network")

    async def test_upstream_failure_is_sanitized_and_never_retried(self):
        calls = 0
        async def handle(request):
            nonlocal calls
            calls += 1
            return httpx.Response(401, json={"error": {"message": "sk-private-test http://user:proxy-password@proxy.example:1234"}})
        with upstream(handle), self.assertRaises(GenError) as caught:
            await providers.generate(dict(PROFILE, proxy_url="http://user:proxy-password@proxy.example:1234"), "prompt", {}, REFS, None)
        self.assertEqual(calls, 1)
        self.assertEqual(caught.exception.kind, "auth")
        self.assertNotIn("sk-private-test", str(caught.exception))
        self.assertNotIn("proxy-password", str(caught.exception))
        with upstream(lambda request: (_ for _ in ()).throw(httpx.ConnectError("sk-private-test proxy-password"))), self.assertRaises(GenError) as caught:
            await providers.generate(PROFILE, "prompt", {}, [], None)
        self.assertNotIn("sk-private-test", str(caught.exception))
        self.assertNotIn("proxy-password", str(caught.exception))

    async def test_models_endpoints_and_seedream_unavailable(self):
        async def handle(request):
            self.assertEqual(request.method, "GET")
            if "x-goog-api-key" in request.headers:
                return httpx.Response(200, json={"models": [{"name": "models/gemini-2.5-flash-image"}, {"name": "models/gemini-2.5-flash-image"}]})
            return httpx.Response(200, json={"data": [{"id": "custom-image"}]})
        with upstream(handle):
            self.assertEqual(await providers.list_models(PROFILE), ["custom-image"])
            self.assertEqual(await providers.list_models(dict(PROFILE, kind="gemini")), ["gemini-2.5-flash-image"])
        with upstream(lambda request: self.fail("Seedream must not probe a guessed model endpoint")), self.assertRaises(GenError) as caught:
            await providers.list_models(dict(PROFILE, kind="seedream"))
        self.assertEqual((caught.exception.kind, caught.exception.status), ("model_list", 409))

    async def test_safety_and_missing_model_fail_before_request(self):
        with upstream(lambda request: httpx.Response(200, json={"promptFeedback": {"blockReason": "SAFETY"}})), self.assertRaises(GenError) as caught:
            await providers.generate(dict(PROFILE, kind="gemini"), "prompt", {}, [], None)
        self.assertEqual(caught.exception.kind, "safety")
        with upstream(lambda request: self.fail("Blank relay model must not make a request")), self.assertRaises(GenError):
            await providers.generate(dict(PROFILE, kind="relay", model=""), "prompt", {}, [], None)

    async def test_invalid_references_and_bounded_download(self):
        with upstream(lambda request: self.fail("Invalid refs must not make a request")):
            for refs in (REFS + REFS, [{"data": PNG, "mime": "image/jpeg"}]):
                with self.assertRaises(GenError):
                    await providers.generate(PROFILE, "prompt", {}, refs, None)
        async def handle(request):
            if request.method == "POST":
                return httpx.Response(200, json={"data": [{"url": "https://images.example/x"}]})
            return httpx.Response(200, stream=Chunks(PNG))
        with patch.object(providers, "MAX_IMAGE_BYTES", 20), upstream(handle), self.assertRaises(GenError):
            await providers.generate(PROFILE, "prompt", {}, [], None)


class NetworkTests(unittest.IsolatedAsyncioTestCase):
    async def test_private_and_transition_addresses_rejected(self):
        for address in ("127.0.0.1", "10.1.2.3", "169.254.169.254", "192.168.0.1", "0.0.0.0", "224.0.0.1", "::1", "fe80::1", "fc00::1", "fec0::1", "ff02::1", "::ffff:127.0.0.1", "64:ff9b::a00:1", "2002:7f00:1::"):
            with self.subTest(address=address), self.assertRaises(GenError):
                await network.resolve_public(address, 443)
        self.assertEqual(await network.resolve_public("8.8.8.8", 443), ["8.8.8.8"])
        self.assertFalse(network.public_address("240.0.0.1"))

    async def test_all_dns_answers_checked(self):
        loop = asyncio.get_running_loop()
        records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)), (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", 443, 0, 0))]
        with patch.object(loop, "getaddrinfo", AsyncMock(return_value=records)) as lookup:
            with self.assertRaises(GenError):
                await network.resolve_public("mixed.example", 443)
            lookup.assert_awaited_once()

    async def test_numeric_connect_and_original_host_sni(self):
        backend = network.PinnedBackend()
        sentinel = object()
        with patch.object(network, "resolve_public", AsyncMock(return_value=["8.8.8.8"])) as resolve, patch.object(network.AutoBackend, "connect_tcp", AsyncMock(return_value=sentinel)) as connect:
            self.assertIs(await backend.connect_tcp("upstream.example", 443), sentinel)
            resolve.assert_awaited_once()
            self.assertEqual(connect.await_args.args[:2], ("8.8.8.8", 443))
        transport = network.PinnedTransport()
        with patch.object(httpx.AsyncHTTPTransport, "handle_async_request", AsyncMock(return_value=httpx.Response(200))) as handle:
            request = httpx.Request("GET", "https://upstream.example/models")
            await transport.handle_async_request(request)
            passed = handle.await_args.args[0]
            self.assertEqual(passed.url.host, "upstream.example")
            self.assertEqual(passed.headers["host"], "upstream.example")
        await transport.aclose()

    async def test_direct_ignores_proxy_environment_and_tls_stays_enabled(self):
        with patch.dict(os.environ, {"HTTP_PROXY": "http://user:secret@127.0.0.1:7890", "HTTPS_PROXY": "http://127.0.0.1:7890"}):
            async with network.safe_client({"network_mode": "direct"}) as client:
                self.assertIsInstance(client._transport, network.PinnedTransport)
                self.assertFalse(client._trust_env)
                self.assertFalse(client.follow_redirects)
                context = client._transport._pool._ssl_context
                self.assertTrue(context.check_hostname)
                self.assertEqual(context.verify_mode, 2)

    async def test_proxy_disabled_and_exact_operator_allowlist(self):
        for mode in ("proxy", "environment"):
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(GenError) as caught:
                    async with network.safe_client({"network_mode": mode, "proxy_url": "http://127.0.0.1:7890"}):
                        pass
                self.assertEqual(caught.exception.status, 409)
        with patch.dict(os.environ, {"PHOTOAI_ALLOW_PROXIES": '["http://127.0.0.1:7890"]'}, clear=True):
            async with network.safe_client({"network_mode": "proxy", "proxy_url": "http://user:secret@127.0.0.1:7890"}) as client:
                self.assertIsInstance(client._transport, network.ProxyTransport)
            with self.assertRaises(GenError):
                async with network.safe_client({"network_mode": "proxy", "proxy_url": "http://127.0.0.1:7891"}):
                    pass
        self.assertEqual(network.proxy_endpoint("http://user:secret@PROXY.example/"), "http://proxy.example:80")

    async def test_environment_proxy_and_no_proxy_routes(self):
        values = {"PHOTOAI_ALLOW_PROXIES": '["http://127.0.0.1:7890"]', "HTTPS_PROXY": "http://127.0.0.1:7890", "NO_PROXY": "bypass.example"}
        with patch.dict(os.environ, values, clear=True):
            async with network.safe_client({"network_mode": "environment"}) as client:
                transport = client._transport
                with patch.object(transport.direct, "handle_async_request", AsyncMock(return_value=httpx.Response(200))) as direct, patch.object(transport.routes["https"], "handle_async_request", AsyncMock(return_value=httpx.Response(200))) as proxy:
                    await client.get("https://upstream.example/models")
                    await client.get("https://bypass.example/models")
                    proxy.assert_awaited_once()
                    direct.assert_awaited_once()

    async def test_proxy_validates_target_public_dns(self):
        transport = network.ProxyTransport("http://127.0.0.1:7890", {"http://127.0.0.1:7890"})
        with patch.object(httpx.AsyncHTTPTransport, "handle_async_request", AsyncMock()) as send:
            with self.assertRaises(GenError):
                await transport.handle_async_request(httpx.Request("GET", "http://127.0.0.1/private"))
            send.assert_not_awaited()
        await transport.aclose()

    async def test_only_mock_transport_can_bypass_network(self):
        async with network.safe_client({}, transport=httpx.MockTransport(lambda request: httpx.Response(200, text="mock"))) as client:
            self.assertEqual((await client.get("http://127.0.0.1/test")).text, "mock")
        with self.assertRaises(TypeError):
            async with network.safe_client({}, transport=network.PinnedTransport()):
                pass


if __name__ == "__main__":
    unittest.main()
