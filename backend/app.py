"""Same-origin generation API plus optional local static preview."""
import asyncio
import json
import os
import secrets
import time
from collections import deque
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .errors import GenError
from .jobs import Jobs
from .providers import DEFAULTS, list_models, normalize_profile
from .store import ABSOLUTE, IDLE, Store

PREFIX = '/api/generation'
COOKIE = 'photoai_session'
MAX_BODY = 24 * 1024**2


class Rates:
    def __init__(self):
        self.entries = {}

    def check(self, key, maximum=30, window=60):
        now = time.monotonic()
        if len(self.entries) > 10000:
            self.entries = {k: v for k, v in self.entries.items() if v and v[-1] > now - 3600}
            if len(self.entries) > 10000:
                raise GenError('rate', '请求过多，请稍后重试', 429)
        q = self.entries.setdefault(key, deque())
        while q and q[0] < now - window:
            q.popleft()
        if len(q) >= maximum:
            raise GenError('rate', '请求过多，请稍后重试', 429)
        q.append(now)


async def body(req):
    raw = bytearray()
    async for part in req.stream():
        raw.extend(part)
        if len(raw) > MAX_BODY:
            raise GenError('bad', '请求图片过大', 413)
    try:
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except (ValueError, UnicodeDecodeError):
        raise GenError('bad', 'JSON 参数无效')


def create_app(static_root=None, state_dir=None, origins=None, store=None):
    origins = set(origins or os.environ.get('PHOTOAI_ORIGINS', 'http://127.0.0.1:8080,http://localhost:8080').split(','))
    origins = {o.strip().rstrip('/') for o in origins if o.strip()}
    hosts = {urlsplit(o).netloc for o in origins}
    if not origins:
        raise RuntimeError('PHOTOAI_ORIGINS is required')
    secure_cookie = not all(urlsplit(o).scheme == 'http' and urlsplit(o).hostname in ('127.0.0.1', 'localhost', '::1') for o in origins)
    private = store or Store(state_dir, static_root)
    jobs, rates = Jobs(private), Rates()

    async def cleanup():
        while True:
            await asyncio.sleep(300)
            expired = private.cleanup()
            for jid, (sid, task) in list(jobs.tasks.items()):
                if sid in expired:
                    task.cancel()

    @asynccontextmanager
    async def lifespan(app):
        private.cleanup()
        cleaner = asyncio.create_task(cleanup())
        yield
        cleaner.cancel()
        await asyncio.gather(cleaner, return_exceptions=True)
        await jobs.close()
        private.close()

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.store, app.state.jobs = private, jobs

    @app.exception_handler(GenError)
    async def error(req, e):
        return JSONResponse({'error': {'k': e.kind, 'msg': e.message}}, status_code=e.status)

    @app.middleware('http')
    async def guard(req, call_next):
        if not req.url.path.startswith(PREFIX):
            return await call_next(req)
        try:
            if req.headers.get('host') not in hosts:
                raise GenError('host', '访问地址未被生图服务允许', 403)
            origin = req.headers.get('origin')
            if origin and origin.rstrip('/') not in origins:
                raise GenError('origin', '请从本站打开生图服务', 403)
            if req.headers.get('sec-fetch-site') == 'cross-site':
                raise GenError('origin', '请从本站打开生图服务', 403)
            if int(req.headers.get('content-length') or 0) > MAX_BODY:
                raise GenError('bad', '请求图片过大', 413)
            if req.method not in ('GET', 'HEAD'):
                if not origin or origin.rstrip('/') not in origins:
                    raise GenError('origin', '缺少有效来源', 403)
                session, _ = private.session(req.cookies.get(COOKIE), touch=False)
                if not session or not secrets.compare_digest(req.headers.get('x-csrf-token', ''), session['csrf']):
                    raise GenError('session', '会话已过期，请刷新页面', 403)
                rates.check('write:' + session['id'], 60)
                private.session(req.cookies.get(COOKIE), touch=True)
                req.state.session = session
            response = await call_next(req)
        except GenError as e:
            response = JSONResponse({'error': {'k': e.kind, 'msg': e.message}}, status_code=e.status)
        except ValueError:
            response = JSONResponse({'error': {'k': 'bad', 'msg': '请求参数无效'}}, status_code=400)
        current = getattr(req.state, 'session', None)
        if current and response.status_code < 400 and req.url.path != PREFIX + '/session':
            remaining = min(IDLE, max(0, int(current['created'] + ABSOLUTE - time.time())))
            response.set_cookie(COOKIE, req.cookies[COOKIE], max_age=remaining, httponly=True, secure=secure_cookie, samesite='strict', path=PREFIX)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Vary'] = 'Cookie'
        return response

    def visitor(req):
        current = getattr(req.state, 'session', None)
        if not current:
            current, _ = private.session(req.cookies.get(COOKIE))
        if not current:
            raise GenError('session', '会话已过期，请刷新页面', 403)
        return current

    @app.get(PREFIX + '/session')
    async def session(req: Request):
        rates.check('session:' + (req.client.host if req.client else 'unknown'), 60)
        current, token = private.session(req.cookies.get(COOKIE), create=True)
        response = JSONResponse(dict(session_id=current['id'], csrf=current['csrf'],
                                     default_profile_id=current['default_profile'], defaults=DEFAULTS,
                                     retention=dict(idle_days=7, absolute_days=30, result_hours=24),
                                     proxy_enabled=bool(os.environ.get('PHOTOAI_ALLOW_PROXIES'))))
        if token:
            response.set_cookie(COOKIE, token, max_age=IDLE, httponly=True, secure=secure_cookie, samesite='strict', path=PREFIX)
        return response

    @app.delete(PREFIX + '/session')
    async def erase_session(req: Request):
        await jobs.erase(visitor(req)['id'])
        response = JSONResponse({'ok': True})
        response.delete_cookie(COOKIE, path=PREFIX)
        return response

    @app.get(PREFIX + '/profiles')
    async def profiles(req: Request):
        s = visitor(req)
        return dict(profiles=private.profiles(s['id']), default_profile_id=s['default_profile'])

    @app.put(PREFIX + '/profiles/{pid}')
    async def save_profile(pid: str, req: Request):
        return private.save_profile(visitor(req)['id'], pid, await body(req), normalize_profile)

    @app.delete(PREFIX + '/profiles/{pid}')
    async def remove_profile(pid: str, req: Request):
        private.delete_profile(visitor(req)['id'], pid)
        return {'ok': True}

    @app.put(PREFIX + '/profiles/{pid}/default')
    async def set_default(pid: str, req: Request):
        private.default(visitor(req)['id'], pid)
        return {'ok': True}

    @app.post(PREFIX + '/profiles/{pid}/models/refresh')
    async def refresh(pid: str, req: Request):
        owner = visitor(req)['id']
        rates.check('models:' + owner, 10)
        p = private.profile(owner, pid)
        models = await list_models(p)
        return private.update_models(owner, pid, p['version'], models)

    @app.get(PREFIX + '/jobs')
    async def list_jobs(req: Request):
        return {'jobs': [jobs.public(j) for j in private.jobs(visitor(req)['id'])]}

    @app.post(PREFIX + '/jobs')
    async def submit(req: Request):
        owner = visitor(req)['id']
        rates.check('jobs:' + owner, 12)
        return await jobs.submit(owner, await body(req))

    @app.get(PREFIX + '/jobs/{jid}')
    async def get_job(jid: str, req: Request):
        return jobs.public(private.job(visitor(req)['id'], jid))

    @app.post(PREFIX + '/jobs/{jid}/cancel')
    async def cancel(jid: str, req: Request):
        return await jobs.cancel(visitor(req)['id'], jid)

    @app.delete(PREFIX + '/jobs/{jid}')
    async def delete_job(jid: str, req: Request):
        private.delete_job(visitor(req)['id'], jid)
        return {'ok': True}

    @app.delete(PREFIX + '/jobs')
    async def clear_jobs(req: Request):
        owner = visitor(req)['id']
        for j in private.jobs(owner):
            await jobs.cancel(owner, j['id'])
            private.delete_job(owner, j['id'])
        return {'ok': True}

    @app.get(PREFIX + '/images/{iid}')
    async def image(iid: str, req: Request):
        mime, data = private.image(visitor(req)['id'], iid)
        return Response(data, media_type=mime)

    if static_root:
        app.mount('/', StaticFiles(directory=static_root, html=True), name='gallery')
    return app


def production_app():
    return create_app()
