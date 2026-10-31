"""Validated native image-provider adapters, one upstream generation per call."""
from __future__ import annotations

import base64
import binascii
from io import BytesIO
import json
import re
import ssl
from urllib.parse import quote, unquote, urlsplit, urlunsplit
import warnings

import httpx
from PIL import Image, UnidentifiedImageError

from backend.errors import GenError
from backend.network import normalize_proxy_url, safe_client, validate_url

MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
MAX_RESPONSE_BYTES = 120 * 1024 * 1024
MAX_SSE_LINE_BYTES = 30 * 1024 * 1024
MAX_SSE_EVENT_BYTES = 30 * 1024 * 1024
MAX_SSE_TOTAL_BYTES = 160 * 1024 * 1024
MAX_RESULT_IMAGES = 8
MAX_BASE64_CHARS = ((MAX_IMAGE_BYTES + 2) // 3) * 4

DEFAULTS = {
    "openai": {"display_name": "OpenAI GPT Image", "base_url": "https://api.openai.com/v1", "model": "gpt-image-2", "models": ["gpt-image-2"]},
    "relay": {"display_name": "OpenAI compatible relay", "base_url": "", "model": "", "models": []},
    "gemini": {"display_name": "Google Gemini", "base_url": "https://generativelanguage.googleapis.com/v1beta", "model": "gemini-2.5-flash-image", "models": ["gemini-2.5-flash-image", "gemini-3-pro-image-preview", "gemini-3.1-flash-image"]},
    "seedream": {"display_name": "Seedream", "base_url": "https://ark.cn-beijing.volces.com/api/v3", "model": "doubao-seedream-4-0-250828", "models": ["doubao-seedream-4-0-250828", "doubao-seedream-4-5-251128", "doubao-seedream-5-0-flash-260915"]},
    "qwen": {"display_name": "Qwen Image", "base_url": "https://dashscope.aliyuncs.com/api/v1", "model": "qwen-image-2.0-pro", "models": ["qwen-image-2.0-pro", "qwen-image-2.0"]},
}
RATIOS = ("3:4", "2:3", "1:1", "4:3", "9:16", "16:9")
SEEDREAM_SIZES = {"3:4": "1728x2304", "2:3": "1664x2496", "9:16": "1440x2560", "1:1": "2048x2048", "4:3": "2304x1728", "16:9": "2560x1440"}
QWEN_SIZES = {"3:4": "1536*2048", "2:3": "1344*2016", "9:16": "1152*2048", "1:1": "1664*1664", "4:3": "2048*1536", "16:9": "2048*1152"}


def _text(value, name, maximum=256, *, empty=True):
    if not isinstance(value, str) or len(value) > maximum or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in value):
        raise GenError("profile", f"Invalid {name}.")
    result = value.strip()
    if not result and not empty:
        raise GenError("profile", f"{name} is required.")
    return result


def _choice(value, choices, name):
    if not isinstance(value, str) or value not in choices:
        raise GenError("parameters", f"Invalid {name}.")
    return value


def _integer(value, low, high, name):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise GenError("parameters", f"{name} must be an integer from {low} to {high}.")
    return value


def normalize_base_url(base, mode="versioned") -> str:
    _choice(mode, ("versioned", "custom"), "base URL mode")
    base = _text(base, "base URL", 4096, empty=False)
    if "?" in base or "#" in base:
        raise GenError("profile", "Base URL cannot contain a query or fragment.")
    try:
        validate_url(base)
        parsed = urlsplit(base)
        path = parsed.path.rstrip("/")
        if re.search(r"/images/(?:generations|edits)(?:/|$)", unquote(path), re.I):
            raise GenError("profile", "Enter the API base URL, without the full Images endpoint.")
        if mode == "versioned":
            path = re.sub(r"(?:/v1)+$", "", path, flags=re.I) + "/v1"
        host = parsed.hostname.encode("idna").decode("ascii").lower()
        if ":" in host:
            host = "[" + host + "]"
        if parsed.port and parsed.port != (443 if parsed.scheme.lower() == "https" else 80):
            host += ":" + str(parsed.port)
        return urlunsplit((parsed.scheme.lower(), host, path, "", ""))
    except (ValueError, UnicodeError):
        raise GenError("profile", "Invalid base URL.") from None


def normalize_profile(profile: dict) -> dict:
    """Return only known config fields, including secrets for private storage.

    This function does not implement patch/removal semantics; the store merges
    before calling it and is responsible for serializing a secret-free view.
    """
    if not isinstance(profile, dict):
        raise GenError("profile", "Provider profile must be an object.")
    kind = _choice(profile.get("kind", "openai"), DEFAULTS, "provider")
    defaults = DEFAULTS[kind]
    mode = _choice(profile.get("base_url_mode", "versioned"), ("versioned", "custom"), "base URL mode")
    base = _text(profile.get("base_url", defaults["base_url"]), "base URL", 4096)
    if base:
        base = normalize_base_url(base, mode if kind in ("openai", "relay") else "custom")
        # Native Gemini domain-only configuration needs its native API version.
        if kind == "gemini" and not urlsplit(base).path:
            base += "/v1beta"
    models = profile.get("models", defaults["models"])
    if not isinstance(models, list) or len(models) > 500:
        raise GenError("profile", "Model list must contain at most 500 model names.")
    models = list(dict.fromkeys(_text(model, "model", 256, empty=False) for model in models))
    stream = profile.get("stream", False)
    if not isinstance(stream, bool):
        raise GenError("profile", "Stream must be a boolean.")
    proxy = _text(profile.get("proxy_url", ""), "proxy URL", 4096)
    if proxy:
        proxy = normalize_proxy_url(proxy)
    result = {
        "kind": kind,
        "display_name": _text(profile.get("display_name", defaults["display_name"]), "display name", 120),
        "base_url": base,
        "api_key": _text(profile.get("api_key", ""), "API key", 16384),
        "model": _text(profile.get("model", defaults["model"]), "model", 256),
        "models": models,
        "base_url_mode": mode,
        "timeout": _integer(profile.get("timeout", 300), 1, 1800, "Timeout"),
        "network_mode": _choice(profile.get("network_mode", "direct"), ("direct", "environment", "proxy"), "network mode"),
        "proxy_url": proxy,
        "stream": stream,
        "partial_images": _integer(profile.get("partial_images", 0), 0, 3, "Partial images"),
        "response_format": _choice(profile.get("response_format", "auto"), ("auto", "b64_json"), "response format"),
        "proto": _choice(profile.get("proto", "edits"), ("edits", "json"), "relay protocol"),
        "field": _choice(profile.get("field", "image[]"), ("image[]", "image"), "reference field"),
    }
    if "id" in profile:
        result["id"] = _text(profile["id"], "profile ID", 128)
    return result


def normalize_image_parameters(params, default_model="") -> dict:
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise GenError("parameters", "Image parameters must be an object.")
    size = params.get("size", "auto")
    if not isinstance(size, str) or (size != "auto" and not re.fullmatch(r"[1-9][0-9]{0,4}x[1-9][0-9]{0,4}", size)):
        raise GenError("parameters", "Size must be auto or positive WIDTHxHEIGHT.")
    output = _choice(params.get("output_format", "png"), ("png", "jpeg", "webp"), "output format")
    background = _choice(params.get("background", "auto"), ("auto", "opaque", "transparent"), "background")
    if output == "jpeg" and background == "transparent":
        raise GenError("parameters", "JPEG cannot have a transparent background.")
    result = {
        "model": _text(params.get("model", default_model), "model", 256),
        "size": size,
        "quality": _choice(params.get("quality", "low"), ("auto", "low", "medium", "high", "xhigh", "max"), "quality"),
        "background": background,
        "output_format": output,
        "ratio": _choice(params.get("ratio", "auto"), ("auto",) + RATIOS, "aspect ratio"),
    }
    if "output_compression" in params:
        compression = _integer(params["output_compression"], 0, 100, "Output compression")
        if output != "png":
            result["output_compression"] = compression
    if "moderation" in params:
        result["moderation"] = _choice(params["moderation"], ("auto", "low"), "moderation")
    return result


def validate_image(data: bytes) -> str:
    if not isinstance(data, bytes) or not data or len(data) > MAX_IMAGE_BYTES:
        raise GenError("image", "Image is empty or exceeds the 20 MiB byte limit.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as image:
                mime = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}.get(image.format)
                if not mime or image.width * image.height > MAX_IMAGE_PIXELS:
                    raise GenError("image", "Only PNG, JPEG and WebP up to 40 million pixels are accepted.")
                if getattr(image, "n_frames", 1) != 1:
                    raise GenError("image", "Animated image output is not supported.")
                image.verify()
            # verify() does not decode every format; load catches truncated JPEG/WebP.
            with Image.open(BytesIO(data)) as image:
                image.load()
        return mime
    except GenError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise GenError("image", "The provider returned an invalid or oversized image.", 502) from None


def _decode_image(value):
    if not isinstance(value, str) or not value or len(value) > MAX_BASE64_CHARS:
        raise GenError("image", "Invalid or oversized base64 image.", 502)
    try:
        data = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error):
        raise GenError("image", "The provider returned invalid base64 image data.", 502) from None
    return data, validate_image(data)


async def _read_bounded(response, limit=MAX_RESPONSE_BYTES):
    body = bytearray()
    async for chunk in response.aiter_bytes(chunk_size=64 * 1024):
        if len(body) + len(chunk) > limit:
            raise GenError("upstream", "The upstream response exceeds the allowed byte limit.", 502)
        body.extend(chunk)
    return bytes(body)


def _json(data):
    try:
        value = json.loads(data)
        if not isinstance(value, dict):
            raise ValueError
        return value
    except (ValueError, UnicodeError, RecursionError):
        raise GenError("upstream", "The provider returned an invalid JSON response.", 502) from None


def _error_tokens(payload):
    """Inspect bounded machine codes/text, never repeat upstream text publicly."""
    if not isinstance(payload, dict):
        return ""
    error = payload.get("error")
    if isinstance(error, dict):
        values = [error.get("code"), error.get("type"), error.get("message"), error.get("status")]
    else:
        values = [error, payload.get("code"), payload.get("message")]
    return " ".join(value[:4096] for value in values if isinstance(value, str)).lower()


def _raise_upstream(status, payload=None):
    tokens = _error_tokens(payload)
    if re.search(r"safety|moderation|content.?policy|sensitive|inspection|inappropriate|prohibited|blocked|违规|敏感|审核", tokens):
        raise GenError("safety", "The provider blocked this request under its content policy.", 422)
    if status in (401, 403):
        raise GenError("auth", "The provider rejected the API key or its permissions.", 401)
    if status == 429 or re.search(r"quota|balance|insufficient|resource_exhausted|余额|额度", tokens):
        raise GenError("rate", "The provider rate limit or account quota was exceeded.", 429)
    if status == 404:
        raise GenError("model", "The model or API endpoint was not found.", 502)
    if 300 <= status < 400:
        raise GenError("network", "Upstream redirects are not followed.", 502)
    if status >= 500:
        raise GenError("server", "The provider is temporarily unavailable.", 502)
    raise GenError("upstream", "The provider rejected the generation request.", 502)


async def _check_response(response):
    if not 200 <= response.status_code < 300:
        body = await _read_bounded(response, 256 * 1024)
        try:
            payload = json.loads(body)
        except (ValueError, UnicodeError, RecursionError):
            payload = None
        _raise_upstream(response.status_code, payload)


async def _download(client, url):
    if not isinstance(url, str):
        raise GenError("image", "The provider returned an invalid image URL.", 502)
    if url.startswith("data:"):
        match = re.fullmatch(r"data:image/(?:png|jpeg|webp);base64,([A-Za-z0-9+/=]+)", url)
        if not match:
            raise GenError("image", "The provider returned an invalid image data URL.", 502)
        return _decode_image(match.group(1))
    validate_url(url)
    # Authentication is per-request, never installed as an AsyncClient default.
    async with client.stream("GET", url, headers={"Accept": "image/png,image/jpeg,image/webp"}) as response:
        await _check_response(response)
        data = await _read_bounded(response, MAX_IMAGE_BYTES)
    return data, validate_image(data)


async def _openai_images(payload, client):
    if payload.get("error"):
        _raise_upstream(400, payload)
    items = payload.get("data")
    if not isinstance(items, list):
        raise GenError("no_image", "The provider returned no final image.", 502)
    if len(items) > MAX_RESULT_IMAGES:
        raise GenError("image", "The provider returned too many images.", 502)
    results = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("b64_json"):
            results.append(_decode_image(item["b64_json"]))
        elif item.get("url"):
            results.append(await _download(client, item["url"]))
    if not results:
        raise GenError("no_image", "The provider returned no final image.", 502)
    return results


async def _sse_events(response):
    """Incremental UTF-8 SSE framing, including CRLF, split bytes and multiline data."""
    buffer = bytearray()
    data = []
    event = ""
    event_bytes = total = 0

    def process(line):
        nonlocal event, data, event_bytes
        if not line:
            result = (event, b"\n".join(data)) if data else None
            event, data, event_bytes = "", [], 0
            return result
        if line.startswith(b":"):
            return None
        field, separator, value = line.partition(b":")
        if value.startswith(b" "):
            value = value[1:]
        if field == b"event":
            if len(value) > 128:
                raise GenError("stream", "Invalid upstream event name.", 502)
            try:
                event = value.decode("utf-8")
            except UnicodeError:
                raise GenError("stream", "Invalid upstream event encoding.", 502) from None
        elif field == b"data":
            event_bytes += len(value) + 1
            if event_bytes > MAX_SSE_EVENT_BYTES:
                raise GenError("stream", "Upstream stream event exceeds the byte limit.", 502)
            data.append(value)
        return None

    async for chunk in response.aiter_bytes():
        total += len(chunk)
        if total > MAX_SSE_TOTAL_BYTES:
            raise GenError("stream", "Upstream stream exceeds the total byte limit.", 502)
        buffer.extend(chunk)
        while True:
            positions = [position for position in (buffer.find(b"\n"), buffer.find(b"\r")) if position >= 0]
            if not positions:
                break
            position = min(positions)
            if buffer[position] == 13 and position + 1 == len(buffer):
                break  # CR may be the first half of a split CRLF.
            if position > MAX_SSE_LINE_BYTES:
                raise GenError("stream", "Upstream stream line exceeds the byte limit.", 502)
            consumed = position + (2 if buffer[position:position + 2] == b"\r\n" else 1)
            line = bytes(buffer[:position])
            del buffer[:consumed]
            value = process(line)
            if value is not None:
                yield value
        if len(buffer) > MAX_SSE_LINE_BYTES:
            raise GenError("stream", "Upstream stream line exceeds the byte limit.", 502)
    if buffer:
        value = process(bytes(buffer).rstrip(b"\r"))
        if value is not None:
            yield value
    value = process(b"")
    if value is not None:
        yield value


async def _stream_images(response, on_preview):
    seen = set()
    final = None
    async for event, raw in _sse_events(response):
        if raw.strip() == b"[DONE]":
            continue
        payload = _json(raw)
        event = payload.get("type", event)
        if payload.get("error") or event in ("error", "image_generation.error", "image_edit.error"):
            _raise_upstream(400, payload)
        if event in ("image_generation.partial_image", "image_edit.partial_image"):
            index = payload.get("partial_image_index")
            if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index <= 2:
                raise GenError("stream", "The provider returned an invalid preview index.", 502)
            if index in seen:
                continue
            data, mime = _decode_image(payload.get("b64_json"))
            seen.add(index)
            if on_preview is not None:
                await on_preview(data, mime, index)
        elif event in ("image_generation.completed", "image_edit.completed"):
            # A preview or a URL is not a completed event; a final b64_json is required.
            final = _decode_image(payload.get("b64_json"))
    if final is None:
        raise GenError("stream", "The upstream stream ended without a completed final image.", 502)
    return [final]


async def _gemini_images(payload):
    if payload.get("error"):
        _raise_upstream(400, payload)
    feedback = payload.get("promptFeedback") or payload.get("prompt_feedback") or {}
    if isinstance(feedback, dict) and (feedback.get("blockReason") or feedback.get("block_reason")):
        raise GenError("safety", "Gemini blocked this request under its content policy.", 422)
    results = []
    blocked = False
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list) or len(candidates) > 16:
        raise GenError("upstream", "Gemini returned an invalid candidate list.", 502)
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        if candidate.get("finishReason", candidate.get("finish_reason")) in ("SAFETY", "IMAGE_SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "RECITATION"):
            blocked = True
        content = candidate.get("content") or {}
        parts = content.get("parts", []) if isinstance(content, dict) else []
        if not isinstance(parts, list):
            continue
        for part in parts:
            if not isinstance(part, dict) or part.get("thought"):
                continue
            inline = part.get("inlineData") or part.get("inline_data")
            if isinstance(inline, dict) and inline.get("data"):
                results.append(_decode_image(inline["data"]))
                if len(results) > MAX_RESULT_IMAGES:
                    raise GenError("image", "Gemini returned too many images.", 502)
    if not results:
        if blocked:
            raise GenError("safety", "Gemini blocked this request under its content policy.", 422)
        raise GenError("no_image", "Gemini returned no image. Try a different prompt or image model.", 502)
    return results


async def _qwen_images(payload, client):
    if payload.get("error") or payload.get("code"):
        _raise_upstream(400, payload)
    output = payload.get("output") or {}
    choices = output.get("choices", []) if isinstance(output, dict) else []
    results = []
    if isinstance(choices, list):
        for choice in choices[:16]:
            message = choice.get("message", {}) if isinstance(choice, dict) else {}
            content = message.get("content", []) if isinstance(message, dict) else []
            if not isinstance(content, list):
                continue
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("image"), str):
                    results.append(await _download(client, part["image"]))
                    if len(results) > MAX_RESULT_IMAGES:
                        raise GenError("image", "Qwen returned too many images.", 502)
    if not results:
        raise GenError("no_image", "Qwen returned no image.", 502)
    return results


def _references(images):
    if not isinstance(images, list) or len(images) > 3:
        raise GenError("parameters", "At most three reference images are allowed.")
    result = []
    for image in images:
        if not isinstance(image, dict):
            raise GenError("image", "Invalid reference image.")
        data = image.get("data")
        mime = validate_image(data)
        if image.get("mime") != mime:
            raise GenError("image", "Reference image MIME type does not match its bytes.")
        result.append({"data": data, "mime": mime, "uri": f"data:{mime};base64," + base64.b64encode(data).decode("ascii")})
    return result


async def generate(profile, prompt, parameters, images, on_preview=None) -> list[tuple[bytes, str]]:
    profile = normalize_profile(profile)
    parameters = normalize_image_parameters(parameters, profile["model"])
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 32000 or any((ord(c) < 32 and c not in "\n\r\t") or 127 <= ord(c) <= 159 for c in prompt):
        raise GenError("parameters", "Prompt must contain 1 to 32000 text characters.")
    prompt = prompt.strip()
    if not profile["base_url"] or not profile["api_key"]:
        raise GenError("profile", "Set the provider base URL and API key before generating.")
    if not parameters["model"]:
        raise GenError("model", "Choose an image model before generating.")
    refs = _references(images)
    kind, base, model = profile["kind"], profile["base_url"], parameters["model"]
    headers = {"Authorization": "Bearer " + profile["api_key"]}
    request = {}
    if kind in ("openai", "relay"):
        body = {key: value for key, value in parameters.items() if key != "ratio"}
        body.update({"prompt": prompt, "n": 1})
        if profile["stream"]:
            body.update({"stream": True, "partial_images": profile["partial_images"]})
        if profile["response_format"] == "b64_json":
            body["response_format"] = "b64_json"
        json_refs = kind == "relay" and profile["proto"] == "json"
        if refs and not json_refs:
            url = base + "/images/edits"
            request["data"] = {key: str(value).lower() if isinstance(value, bool) else str(value) for key, value in body.items()}
            request["files"] = [(profile["field"] if kind == "relay" else "image[]", (f"ref{index + 1}." + {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[ref["mime"]], ref["data"], ref["mime"])) for index, ref in enumerate(refs)]
        else:
            url = base + "/images/generations"
            if json_refs and refs:
                body["image"] = [ref["uri"] for ref in refs]
            request["json"] = body
    elif kind == "gemini":
        url = base + "/models/" + quote(model, safe="") + ":generateContent"
        headers = {"x-goog-api-key": profile["api_key"]}
        config = {"responseModalities": ["TEXT", "IMAGE"]}
        if parameters["ratio"] != "auto":
            config["imageConfig"] = {"aspectRatio": parameters["ratio"]}
        request["json"] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}] + [{"inline_data": {"mime_type": ref["mime"], "data": ref["uri"].split(",", 1)[1]}} for ref in refs]}],
            "generationConfig": config,
        }
    elif kind == "seedream":
        url = base + "/images/generations"
        request["json"] = {
            "model": model, "prompt": prompt, "n": 1,
            "size": parameters["size"] if parameters["size"] != "auto" else SEEDREAM_SIZES.get(parameters["ratio"], "2048x2048"),
            "response_format": "b64_json", "watermark": False, "sequential_image_generation": "disabled",
        }
        if refs:
            request["json"]["image"] = [ref["uri"] for ref in refs]
    else:  # Qwen native multimodal API.
        url = base + "/services/aigc/multimodal-generation/generation"
        request["json"] = {
            "model": model,
            "input": {"messages": [{"role": "user", "content": [{"image": ref["uri"]} for ref in refs] + [{"text": prompt}]}]},
            "parameters": {"n": 1, "size": parameters["size"].replace("x", "*") if parameters["size"] != "auto" else QWEN_SIZES.get(parameters["ratio"], "1664*1664"), "watermark": False, "prompt_extend": True},
        }
    try:
        async with safe_client(profile) as client:
            async with client.stream("POST", url, headers=headers, **request) as response:
                await _check_response(response)
                if kind in ("openai", "relay") and response.headers.get("content-type", "").split(";", 1)[0].strip().lower() == "text/event-stream":
                    return await _stream_images(response, on_preview)
                payload = _json(await _read_bounded(response))
            if kind == "gemini":
                return await _gemini_images(payload)
            if kind == "qwen":
                return await _qwen_images(payload, client)
            return await _openai_images(payload, client)
    except GenError:
        raise
    except httpx.TimeoutException:
        raise GenError("timeout", "The provider request timed out. It was not retried.", 504) from None
    except (httpx.HTTPError, OSError, ssl.SSLError, ValueError, UnicodeError):
        # Never expose exception text: it may contain credentials or request URLs.
        raise GenError("network", "The provider connection failed. It was not retried.", 502) from None


async def list_models(profile) -> list[str]:
    profile = normalize_profile(profile)
    if profile["kind"] == "seedream":
        raise GenError("model_list", "Seedream model discovery is unavailable. Enter the model or inference endpoint ID manually.", 409)
    if profile["kind"] == "qwen":
        raise GenError("model_list", "Qwen model discovery is unavailable. Enter a supported image model manually.", 409)
    if not profile["base_url"] or not profile["api_key"]:
        raise GenError("profile", "Set the provider base URL and API key before listing models.")
    headers = {"x-goog-api-key": profile["api_key"]} if profile["kind"] == "gemini" else {"Authorization": "Bearer " + profile["api_key"]}
    try:
        async with safe_client(profile) as client:
            async with client.stream("GET", profile["base_url"] + "/models", headers=headers) as response:
                await _check_response(response)
                payload = _json(await _read_bounded(response, 2 * 1024 * 1024))
        if payload.get("error"):
            _raise_upstream(400, payload)
        rows = payload.get("models") if profile["kind"] == "gemini" else payload.get("data")
        if not isinstance(rows, list) or len(rows) > 10000:
            raise GenError("model_list", "The provider returned an invalid model list.", 502)
        result = []
        for row in rows:
            name = row.get("name" if profile["kind"] == "gemini" else "id") if isinstance(row, dict) else None
            if isinstance(name, str) and name.startswith("models/") and profile["kind"] == "gemini":
                name = name[len("models/"):]
            if isinstance(name, str) and name and len(name) <= 256 and not any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in name):
                result.append(name)
        return list(dict.fromkeys(result))[:500]
    except GenError:
        raise
    except httpx.TimeoutException:
        raise GenError("timeout", "Model discovery timed out.", 504) from None
    except (httpx.HTTPError, OSError, ssl.SSLError, ValueError, UnicodeError):
        raise GenError("network", "The model discovery connection failed.", 502) from None
