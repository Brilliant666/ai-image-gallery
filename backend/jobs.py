"""Bounded in-process dispatcher. Run exactly one application worker."""
import asyncio
import base64
import hashlib
import json
import time
import uuid

from .errors import GenError
from . import providers


class Jobs:
    def __init__(self, store):
        self.store = store
        self.tasks = {}
        self.limit = asyncio.Semaphore(4)

    async def submit(self, owner, data):
        if not isinstance(data, dict):
            raise GenError('bad', '任务参数需要是对象')
        rid = data.get('request_id')
        if not isinstance(rid, str) or not 8 <= len(rid) <= 100:
            raise GenError('bad', '请求编号无效')
        fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        # Resolve an existing idempotent submission before profile/key checks.
        for j in self.store.jobs(owner):
            if j.get('request_id') == rid:
                if j.get('fingerprint') != fingerprint:
                    raise GenError('conflict', '请求编号已用于另一项生成', 409)
                return self.public(j)
        if sum(j['state'] in ('queued', 'running') for j in self.store.jobs(owner)) >= 2:
            raise GenError('rate', '已有两项生成，请等待完成', 429)
        if len(self.tasks) >= 20:
            raise GenError('rate', '生成服务正忙，请稍后重试', 429)
        p = self.store.profile(owner, data.get('profile_id', ''))
        if not p.get('api_key'):
            raise GenError('nokey', '先保存服务商 API Key')
        prompt = data.get('prompt', '')
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 20000:
            raise GenError('bad', '请填写有效的提示词（最多 20000 字）')
        n = data.get('n', 1)
        if type(n) is not int or not 1 <= n <= 4:
            raise GenError('bad', '生成张数范围为 1–4')
        params = data.get('parameters', {})
        if not isinstance(params, dict):
            raise GenError('bad', '生成参数需要是对象')
        params = providers.normalize_image_parameters(params, p.get('model', ''))
        refs = data.get('images', [])
        if not isinstance(refs, list) or len(refs) > 3:
            raise GenError('bad', '最多发送三张参考图')
        images = []
        for im in refs:
            try:
                raw = base64.b64decode(im['data'], validate=True)
                if len(raw) > 5 * 1024**2:
                    raise ValueError()
                mime = providers.validate_image(raw)
            except (ValueError, TypeError, KeyError):
                raise GenError('bad', '参考图格式或大小无效')
            images.append({'data': raw, 'mime': mime})
        jid = uuid.uuid4().hex
        j = dict(id=jid, at=int(time.time() * 1000), profile_id=p['id'], p=p['kind'], model=params['model'],
                 ratio=params.get('ratio', '3:4'), n=n, prompt=prompt.strip(), refs=[], state='queued',
                 out=[], preview=None, errors=[], request_id=rid, fingerprint=fingerprint)
        j, new = self.store.create_job(owner, rid, fingerprint, j)
        if new:
            task = asyncio.create_task(self.run(owner, j, p, params, images))
            self.tasks[jid] = (owner, task)
            task.add_done_callback(lambda _: self.tasks.pop(jid, None))
        return self.public(j)

    @staticmethod
    def public(j):
        return {k: v for k, v in j.items() if k not in ('request_id', 'fingerprint')}

    async def run(self, owner, job, profile, params, images):
        jid = job['id']
        out, errors = [], []
        try:
            async with self.limit:
                if not self.store.update_job(owner, jid, {'state': 'running'}):
                    return
                for i in range(job['n']):
                    if not self.store.update_job(owner, jid, {}):
                        return
                    async def preview(raw, mime, index):
                        value = self.store.add_image(owner, jid, raw, mime, preview=True)
                        if value:
                            self.store.update_job(owner, jid, {'preview': value, 'partial_index': index})
                    try:
                        async with asyncio.timeout(profile.get('timeout', 300)) if hasattr(asyncio, 'timeout') else _timeout(profile.get('timeout', 300)):
                            got = await providers.generate(profile, job['prompt'], params, images, preview)
                        for raw, mime in got:
                            value = self.store.add_image(owner, jid, raw, mime)
                            if value:
                                out.append(value)
                        self.store.update_job(owner, jid, {'out': out, 'completed': i + 1})
                    except GenError as e:
                        errors.append({'k': e.kind, 'msg': e.message})
                    except (asyncio.TimeoutError, TimeoutError):
                        errors.append({'k': 'timeout', 'msg': '服务商响应超时，请检查生成记录后再试'})
                    except Exception:
                        errors.append({'k': 'server', 'msg': '生成请求失败，请检查服务配置'})
                self.store.update_job(owner, jid, {'state': 'done' if out else 'error', 'out': out, 'errors': errors,
                                                  'preview': None, 'err': errors[0] if errors else None})
        except asyncio.CancelledError:
            # cancel() writes canceled first, so completion can never overwrite it.
            pass

    async def cancel(self, owner, jid):
        j = self.store.job(owner, jid)
        if j['state'] in ('queued', 'running'):
            self.store.update_job(owner, jid, {'state': 'canceled', 'preview': None})
            entry = self.tasks.get(jid)
            if entry and entry[0] == owner:
                entry[1].cancel()
                await asyncio.gather(entry[1], return_exceptions=True)
        return self.public(self.store.job(owner, jid))

    async def erase(self, owner):
        for jid, (sid, _) in list(self.tasks.items()):
            if sid == owner:
                await self.cancel(owner, jid)
        self.store.erase(owner)

    async def close(self):
        tasks = [t for _, t in self.tasks.values()]
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


class _timeout:
    """Python 3.10 equivalent of asyncio.timeout."""
    def __init__(self, seconds):
        self.seconds, self.expired = seconds, False

    async def __aenter__(self):
        self.task = asyncio.current_task()
        def stop():
            self.expired = True
            self.task.cancel()
        self.timer = asyncio.get_running_loop().call_later(self.seconds, stop)

    async def __aexit__(self, typ, value, tb):
        self.timer.cancel()
        if typ is asyncio.CancelledError and self.expired:
            raise asyncio.TimeoutError() from None
