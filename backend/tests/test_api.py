import asyncio
import base64
import io
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from PIL import Image

from backend.app import COOKIE, create_app
from backend.errors import GenError
from backend.store import Store


def png():
    b = io.BytesIO()
    Image.new('RGB', (64, 64), '#315a92').save(b, 'PNG')
    return b.getvalue()


class API(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / 'state')
        self.app = create_app(store=self.store, origins=['http://127.0.0.1:8080'])
        self.a = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url='http://127.0.0.1:8080')
        self.b = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url='http://127.0.0.1:8080')
        for c in (self.a, self.b):
            s = (await c.get('/api/generation/session')).json()
            c.headers.update({'origin': 'http://127.0.0.1:8080', 'x-csrf-token': s['csrf']})
        self.base = '/api/generation'
        self.secret = 'test-key-never-return'

    async def asyncTearDown(self):
        await self.app.state.jobs.close()
        await self.a.aclose()
        await self.b.aclose()
        self.store.close()
        self.tmp.cleanup()

    async def profile(self, **kw):
        v = dict(kind='relay', display_name='Test provider', base_url='https://provider.example',
                 api_key=self.secret, model='image-model', timeout=300)
        v.update(kw)
        r = await self.a.put(self.base + '/profiles/p1', json=v)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertNotIn(self.secret, r.text)
        self.assertTrue(r.json()['api_key_present'])
        return r.json()

    async def wait_job(self, jid):
        for _ in range(100):
            j = (await self.a.get(self.base + '/jobs/' + jid)).json()
            if j['state'] not in ('queued', 'running'):
                return j
            await asyncio.sleep(.01)
        self.fail('Job did not finish')

    async def test_secret_storage_and_isolation(self):
        await self.profile()
        r = await self.a.get(self.base + '/profiles')
        self.assertNotIn(self.secret, r.text)
        self.assertEqual((await self.b.get(self.base + '/profiles')).json()['profiles'], [])
        self.assertEqual((await self.b.delete(self.base + '/profiles/p1')).status_code, 404)
        owner = self.store.session(self.a.cookies[COOKIE])[0]['id']
        self.assertEqual(self.store.profile(owner, 'p1')['api_key'], self.secret)
        for p in self.store.path.glob('*.sqlite3*'):
            self.assertNotIn(self.secret.encode(), p.read_bytes())
        r = await self.a.put(self.base + '/profiles/p1', json={'api_key': '', 'timeout': 400})
        self.assertTrue(r.json()['api_key_present'])
        r = await self.a.put(self.base + '/profiles/p1', json={'base_url': 'https://other.example'})
        self.assertEqual(r.status_code, 422)
        r = await self.a.put(self.base + '/profiles/p1', json={'remove_api_key': True})
        self.assertFalse(r.json()['api_key_present'])

    async def test_csrf_origin_host_and_cookie(self):
        r = await self.a.get(self.base + '/session')
        self.assertEqual(r.headers['cache-control'], 'no-store')
        self.assertEqual((await self.a.put(self.base + '/profiles/x', json={}, headers={'x-csrf-token': 'wrong'})).status_code, 403)
        self.assertEqual((await self.a.put(self.base + '/profiles/x', json={}, headers={'origin': 'https://other.example'})).status_code, 403)
        self.assertEqual((await self.a.get(self.base + '/profiles', headers={'host': 'bad.example'})).status_code, 403)
        s = (await self.a.get(self.base + '/session')).json()
        self.assertNotIn('api_key', s)
        self.assertFalse(s['proxy_enabled'])
        self.assertNotIn('set-cookie', r.headers)
        changed = await self.profile()
        self.assertIn('Max-Age=604800', (await self.a.put(self.base + '/profiles/p1', json={'timeout': 300})).headers['set-cookie'])

    async def test_jobs_snapshot_idempotency_and_download(self):
        await self.profile()
        calls = []
        async def generate(p, prompt, params, images, callback):
            calls.append((p['api_key'], len(images), params['model']))
            await asyncio.sleep(.02)
            return [(png(), 'image/png')]
        data = dict(request_id='test-request-001', profile_id='p1', prompt='Draw a character', n=2,
                    parameters={'ratio': '3:4'}, images=[{'data': base64.b64encode(png()).decode()}] * 3)
        with patch('backend.jobs.providers.generate', generate):
            r = await self.a.post(self.base + '/jobs', json=data)
            self.assertEqual(r.status_code, 200, r.text)
            jid = r.json()['id']
            repeated = await self.a.post(self.base + '/jobs', json=data)
            self.assertEqual(repeated.json()['id'], jid)
            changed = dict(data, prompt='Different')
            self.assertEqual((await self.a.post(self.base + '/jobs', json=changed)).status_code, 409)
            await self.a.delete(self.base + '/profiles/p1')
            j = await self.wait_job(jid)
        self.assertEqual(j['state'], 'done', j)
        self.assertEqual(len(j['out']), 2)
        self.assertEqual(calls, [(self.secret, 3, 'image-model')] * 2)
        self.assertNotIn(self.secret, json.dumps(j))
        self.assertEqual((await self.b.get(self.base + '/jobs/' + jid)).status_code, 404)
        url = j['out'][0]['url']
        self.assertEqual((await self.a.get(url)).content, png())
        self.assertEqual((await self.b.get(url)).status_code, 404)

    async def test_cancel_cannot_be_overwritten_and_session_erase(self):
        await self.profile()
        started = asyncio.Event()
        async def slow(p, prompt, params, images, callback):
            started.set()
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                return [(png(), 'image/png')]
        with patch('backend.jobs.providers.generate', slow):
            j = (await self.a.post(self.base + '/jobs', json=dict(request_id='cancel-request-01', profile_id='p1', prompt='draw', n=1))).json()
            await started.wait()
            r = await self.a.post(self.base + '/jobs/' + j['id'] + '/cancel')
            self.assertEqual(r.json()['state'], 'canceled')
            self.assertEqual(self.store.jobs(self.store.session(self.a.cookies[COOKIE])[0]['id'])[0]['state'], 'canceled')
        self.assertEqual((await self.a.delete(self.base + '/session')).status_code, 200)
        self.assertEqual((await self.a.get(self.base + '/profiles')).status_code, 403)

    async def test_partial_success(self):
        await self.profile()
        calls = 0
        async def mixed(*args):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise GenError('auth', 'Key rejected', 401)
            return [(png(), 'image/png')]
        with patch('backend.jobs.providers.generate', mixed):
            j = (await self.a.post(self.base + '/jobs', json=dict(request_id='partial-request-1', profile_id='p1', prompt='draw', n=2))).json()
            j = await self.wait_job(j['id'])
        self.assertEqual(j['state'], 'done')
        self.assertEqual(len(j['out']), 1)
        self.assertEqual(j['errors'][0]['k'], 'auth')

    async def test_idle_expiry(self):
        await self.profile()
        owner = self.store.session(self.a.cookies[COOKIE])[0]['id']
        self.store.db.execute('UPDATE sessions SET touched=? WHERE id=?', (time.time() - 8 * 86400, owner))
        self.store.db.commit()
        self.assertEqual((await self.a.get(self.base + '/profiles')).status_code, 403)
        self.assertEqual(self.store.profiles(owner), [])

    async def test_restart_interrupts_without_replay(self):
        await self.profile()
        owner = self.store.session(self.a.cookies[COOKIE])[0]['id']
        job = dict(id='restart-job', state='running', out=[], at=0, request_id='restart-001')
        self.store.create_job(owner, 'restart-001', 'hash', job)
        self.store.close()
        self.store = Store(Path(self.tmp.name) / 'state')
        self.app.state.store = self.store
        self.assertEqual(self.store.job(owner, job['id'])['state'], 'error')
        self.assertEqual(self.store.job(owner, job['id'])['err']['k'], 'interrupted')
        self.assertEqual(self.store.profile(owner, 'p1')['api_key'], self.secret)
        self.assertEqual(self.app.state.jobs.tasks, {})

    async def test_model_refresh_preserves_cache_on_error(self):
        await self.profile(models=['known-model'])
        async def fail(*args):
            raise GenError('network', 'Unavailable', 502)
        with patch('backend.app.list_models', fail):
            response = await self.a.post(self.base + '/profiles/p1/models/refresh')
        self.assertEqual(response.status_code, 502)
        self.assertEqual((await self.a.get(self.base + '/profiles')).json()['profiles'][0]['models'], ['known-model'])

    async def test_timeout_does_not_retry(self):
        await self.profile(timeout=1)
        calls = 0
        async def stalled(*args):
            nonlocal calls
            calls += 1
            await asyncio.sleep(10)
        with patch('backend.jobs.providers.generate', stalled):
            j = (await self.a.post(self.base + '/jobs', json=dict(request_id='timeout-request-1', profile_id='p1', prompt='draw', n=1))).json()
            await asyncio.sleep(1.1)
            j = await self.wait_job(j['id'])
        self.assertEqual(j['err']['k'], 'timeout')
        self.assertEqual(calls, 1)



if __name__ == '__main__':
    unittest.main()
