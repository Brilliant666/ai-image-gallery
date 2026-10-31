# Optional generation backend / 可选生图服务

The galleries remain static and the Python 3.8 build has no new dependencies. Generation needs Python 3.10+ and an always-running API. Gemini and Seedream requests follow PoseWear's image protocols; OpenAI compatibility follows the four image API files specified by the owner in image-prompt-library. These integrations do not include agents, conversations, Responses API or ComfyUI.

## Local preview

Create a dedicated virtual environment, then install the optional dependencies:

```bash
python -m venv .venv-generation
```

```bash
.venv-generation/Scripts/python -m pip install -r backend/requirements.txt
```

```bash
.venv-generation/Scripts/python tools/serve.py --generation --port 8080
```

On Linux the environment's interpreter is `.venv-generation/bin/python`. The original `python tools/serve.py` remains a static-only preview; generation displays an unavailable notice there. Never place the state directory inside the checkout or `dist/`.

## Visitor data and requests

Each visitor supplies their own key. Tabs sharing the HttpOnly cookie share profiles and jobs. Saving a key sends it once to this server; API responses return only `api_key_present`. Blank input preserves a key; clear-key explicitly deletes it. Changing the effective provider address requires a newly entered key. Proxy credentials follow the same write-only rule.

Credentials are encrypted at rest with a server master key. SQLite, the master key, temporary state and results live outside the static root: by default `%LOCALAPPDATA%/photoai-generation` on Windows, or `~/.local/share/photoai-generation` on Linux. `PHOTOAI_STATE_DIR` overrides that path. Restrict its owner and filesystem permissions; on Windows use an account-private directory and ACLs. Database and master-key backups must be protected together. Deleting live state does not erase backups controlled by the operator.

Profiles expire after seven days without an explicit API mutation, or thirty days after session creation. Passive polling does not extend that deadline. Server result files expire after 24 hours; completed results are cached in the browser's most recent 30 jobs, scoped by session ID. Clearing the session cancels work and deletes profiles, keys, jobs, images and the current browser cache. Losing the cookie prevents recovery; inaccessible server data still expires. Clearing only the key does not delete past results.

Reference images and prompts travel through this backend to the selected provider. Long requests run as server jobs, so API creation returns promptly and navigating between galleries does not interrupt generation. Cancellation aborts the local upstream connection, but cannot guarantee that the provider stops billing. No failure triggers automatic paid retries. A service restart marks unfinished jobs interrupted rather than replaying them.

## Provider settings

OpenAI-compatible: Base URL, versioned `/v1` or custom root, model, timeout (1–1800 seconds, default 300), direct/environment/proxy networking, streaming (default off), partial images (0–3), and auto/Base64 response format. Auto omits `response_format`. Standard text requests use JSON `/images/generations`; references use multipart `/images/edits` with `image[]`. The relay compatibility options explicitly support singular `image` and JSON multireference requests. They never silently remove references or resend requests.

Advanced image options include size, quality, PNG/JPEG/WebP output, background, JPEG/WebP compression and optional moderation. Support depends on the provider. JPEG plus transparency is invalid. PNG omits compression. Refreshing `/models` uses the saved configuration and preserves the last successful list on failure; a model-list success does not verify generation.

Gemini uses `generateContent`, default model `gemini-2.5-flash-image`, text plus `inline_data`, `responseModalities: [TEXT, IMAGE]` and the selected aspect ratio. Seedream uses `/images/generations`, default `doubao-seedream-4-0-250828`, reference data-URI arrays, disabled watermark and disabled sequential generation. The UI's Seedream is image generation, not Seedance video.

## Network policy

Direct ignores HTTP proxy environment variables. HTTPS uses the HTTPX CA bundle by default; an operator can set SSL_CERT_FILE / SSL_CERT_DIR for an approved CA, with certificate verification still mandatory. Environment means the **server's** environment, not the visitor's machine. TLS verification stays enabled, redirects and automatic retries stay disabled. Model discovery and returned-image downloads follow the same destination rules; image downloads never receive the provider's authorization header.

Direct requests resolve and pin validated public destinations while preserving the original Host/SNI. Local, private, mapped-private, link-local and reserved targets are rejected. Environment and custom proxy modes are disabled until the operator explicitly configures approved proxy endpoints in `PHOTOAI_ALLOW_PROXIES` (JSON array of full endpoint URLs without credentials). The approved gateway must itself enforce public-only destinations; allowing a gateway is an operator assertion of that enforcement. Do not approve a generic local proxy which can reach private addresses. Custom proxy credentials remain server-only. No OS proxy, network adapter or local Clash settings are changed.

## Production installation (not performed by static deployment)

Run one Uvicorn worker under an unprivileged account. The dispatcher is process-local; multiple workers require a shared dispatcher and must not be enabled with this implementation. Set `PHOTOAI_ORIGINS=https://photoai.life` and a private `PHOTOAI_STATE_DIR`, install `backend/requirements.txt` in a dedicated environment, and adapt [photoai-generation.service](photoai-generation.service). The service listens only on loopback port 8090.

Add the location from [generation-nginx.conf](generation-nginx.conf) to the existing HTTPS virtual host. This is an additive snippet, not a replacement for the live nginx configuration. Back up the live config, validate with `nginx -t`, then reload smoothly only after deployment approval. API responses and image results must bypass all CDN caches; do not add Cache Everything rules for `/api/generation/`.

Static release must include the inert `gen-sw.js` at its existing URL so installed forwarding workers can update and unregister. Keep it through the migration period with revalidation. Upload limits are 24 MiB per request, returned images are independently bounded, concurrency and per-session storage are limited. Monitor disk and process memory.

Rollback: stop the optional backend and remove only its nginx API location, validate/reload nginx, then roll back static pages through the normal release procedure. Keep private state outside release swaps; do not overwrite the master key. Existing SSH, certificates and other services are unaffected by this optional setup.

## Verification

```bash
python -m unittest discover -s backend/tests -v
```

```bash
python tests/run.py
```

Protocol tests mock providers and do not spend API credits. A real-key test should be performed on the local preview before production activation.
