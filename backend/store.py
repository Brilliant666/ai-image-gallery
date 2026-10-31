"""Visitor-scoped state outside the static release."""
import hashlib
import json
import os
import secrets
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit

from cryptography.fernet import Fernet
from .errors import GenError

IDLE = 7 * 86400
ABSOLUTE = 30 * 86400
RESULT_TTL = 86400


def state_directory():
    if os.environ.get('PHOTOAI_STATE_DIR'):
        return Path(os.environ['PHOTOAI_STATE_DIR']).expanduser().resolve()
    base = Path(os.environ.get('LOCALAPPDATA', Path.home() / '.local' / 'share'))
    return (base / 'photoai-generation').resolve()


def public_profile(p):
    value = {k: v for k, v in p.items() if k not in ('api_key', 'proxy_url')}
    value['api_key_present'] = bool(p.get('api_key'))
    value['proxy_url_present'] = bool(p.get('proxy_url'))
    u = urlsplit(p.get('proxy_url') or '')
    host = u.hostname or ''
    if ':' in host:
        host = '[' + host + ']'
    value['proxy_endpoint'] = (u.scheme + '://' + host + (':' + str(u.port) if u.port else '')) if host else ''
    return value


class Store:
    def __init__(self, path=None, static_root=None):
        self.path = Path(path or state_directory()).resolve()
        forbidden = [Path(__file__).resolve().parent.parent]
        if static_root:
            forbidden.append(Path(static_root).resolve())
        if any(self.path == x or x in self.path.parents for x in forbidden):
            raise RuntimeError('Generation state must be outside the repository and static root')
        self.path.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.lock = threading.RLock()
        key_path = self.path / 'master.key'
        if not key_path.exists():
            try:
                with open(key_path, 'xb') as f:
                    f.write(Fernet.generate_key())
                os.chmod(key_path, 0o600)
            except FileExistsError:
                pass
        self.cipher = Fernet(key_path.read_bytes())
        self.db = sqlite3.connect(self.path / 'state.sqlite3', check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        os.chmod(self.path / 'state.sqlite3', 0o600)
        self.db.executescript('''
        PRAGMA journal_mode=WAL;
        PRAGMA secure_delete=ON;
        CREATE TABLE IF NOT EXISTS sessions (
          id TEXT PRIMARY KEY, token TEXT UNIQUE, csrf TEXT, created REAL, touched REAL, default_profile TEXT);
        CREATE TABLE IF NOT EXISTS profiles (
          owner TEXT, id TEXT, value BLOB, PRIMARY KEY(owner,id));
        CREATE TABLE IF NOT EXISTS jobs (
          owner TEXT, id TEXT PRIMARY KEY, request_id TEXT, fingerprint TEXT, value TEXT, created REAL,
          UNIQUE(owner,request_id));
        CREATE TABLE IF NOT EXISTS images (
          owner TEXT, job TEXT, id TEXT PRIMARY KEY, mime TEXT, value BLOB, preview INTEGER, created REAL);
        ''')
        for row in self.db.execute('SELECT id,value FROM jobs').fetchall():
            j = json.loads(row['value'])
            if j['state'] in ('queued', 'running'):
                j.update(state='error', err={'k': 'interrupted', 'msg': '生成服务已重启，请检查服务商记录后再试'})
                self.db.execute('UPDATE jobs SET value=? WHERE id=?', (json.dumps(j), row['id']))
        self.db.commit()

    def close(self):
        self.db.close()

    def _seal(self, value):
        return self.cipher.encrypt(json.dumps(value, ensure_ascii=False).encode())

    def _open(self, value):
        return json.loads(self.cipher.decrypt(value))

    def session(self, token, create=False, touch=False):
        now = time.time()
        digest = hashlib.sha256((token or '').encode()).hexdigest()
        with self.lock:
            row = self.db.execute('SELECT * FROM sessions WHERE token=?', (digest,)).fetchone()
            if row and (row['touched'] < now - IDLE or row['created'] < now - ABSOLUTE):
                self.erase(row['id'])
                row = None
            if row:
                if touch:
                    self.db.execute('UPDATE sessions SET touched=? WHERE id=?', (now, row['id']))
                    self.db.commit()
                return dict(row), None
            if not create:
                return None, None
            token = secrets.token_urlsafe(32)
            sid, csrf = uuid.uuid4().hex, secrets.token_urlsafe(32)
            self.db.execute('INSERT INTO sessions VALUES(?,?,?,?,?,NULL)',
                            (sid, hashlib.sha256(token.encode()).hexdigest(), csrf, now, now))
            self.db.commit()
            return dict(id=sid, csrf=csrf, created=now, touched=now, default_profile=None), token

    def profiles(self, owner):
        with self.lock:
            return [public_profile(self._open(r['value'])) for r in self.db.execute('SELECT value FROM profiles WHERE owner=? ORDER BY rowid', (owner,))]

    def profile(self, owner, pid):
        with self.lock:
            row = self.db.execute('SELECT value FROM profiles WHERE owner=? AND id=?', (owner, pid)).fetchone()
            if not row:
                raise GenError('missing', '配置不存在', 404)
            return self._open(row['value'])

    def save_profile(self, owner, pid, changes, normalize):
        if not pid or len(pid) > 80 or any(not (c.isascii() and (c.isalnum() or c in '_-')) for c in pid):
            raise GenError('bad', '配置 ID 无效')
        with self.lock:
            try:
                old = self.profile(owner, pid)
            except GenError:
                old = {}
            if not old and len(self.profiles(owner)) >= 10:
                raise GenError('rate', '每个访客最多保存 10 个服务配置', 429)
            merged = dict(old)
            for k, v in changes.items():
                if k in ('id', 'remove_api_key', 'remove_proxy_url', 'api_key_present', 'proxy_url_present', 'proxy_endpoint'):
                    continue
                if k in ('api_key', 'proxy_url') and not v:
                    continue
                merged[k] = v
            for k in ('api_key', 'proxy_url'):
                if changes.get('remove_' + k) is True:
                    merged[k] = ''
            value = normalize(merged)
            if old.get('api_key') and (value['base_url'] != old.get('base_url') or value['kind'] != old.get('kind')) and not changes.get('api_key') and not changes.get('remove_api_key'):
                raise GenError('key_reentry', '修改服务地址时请重新输入 Key', 422)
            value.update(id=pid, version=uuid.uuid4().hex)
            self.db.execute('INSERT OR REPLACE INTO profiles VALUES(?,?,?)', (owner, pid, self._seal(value)))
            self.db.execute('UPDATE sessions SET default_profile=COALESCE(default_profile,?) WHERE id=?', (pid, owner))
            self.db.commit()
            return public_profile(value)

    def delete_profile(self, owner, pid):
        with self.lock:
            self.profile(owner, pid)
            self.db.execute('DELETE FROM profiles WHERE owner=? AND id=?', (owner, pid))
            first = self.db.execute('SELECT id FROM profiles WHERE owner=? ORDER BY rowid LIMIT 1', (owner,)).fetchone()
            self.db.execute('UPDATE sessions SET default_profile=? WHERE id=? AND default_profile=?', (first['id'] if first else None, owner, pid))
            self.db.commit()

    def default(self, owner, pid):
        with self.lock:
            self.profile(owner, pid)
            self.db.execute('UPDATE sessions SET default_profile=? WHERE id=?', (pid, owner))
            self.db.commit()

    def update_models(self, owner, pid, version, models):
        with self.lock:
            p = self.profile(owner, pid)
            if p['version'] != version:
                raise GenError('conflict', '配置已修改，请重新刷新', 409)
            p['models'] = list(dict.fromkeys(models))[:100]
            p['version'] = uuid.uuid4().hex
            self.db.execute('UPDATE profiles SET value=? WHERE owner=? AND id=?', (self._seal(p), owner, pid))
            self.db.commit()
            return public_profile(p)

    def jobs(self, owner):
        with self.lock:
            return self.jobs_all(owner)[:30]

    def jobs_all(self, owner):
        return [json.loads(r['value']) for r in self.db.execute('SELECT value FROM jobs WHERE owner=? ORDER BY created DESC', (owner,))]

    def job(self, owner, jid):
        with self.lock:
            r = self.db.execute('SELECT value FROM jobs WHERE owner=? AND id=?', (owner, jid)).fetchone()
            if not r:
                raise GenError('missing', '任务不存在', 404)
            return json.loads(r['value'])

    def create_job(self, owner, request_id, fingerprint, value):
        with self.lock:
            row = self.db.execute('SELECT id,fingerprint FROM jobs WHERE owner=? AND request_id=?', (owner, request_id)).fetchone()
            if row:
                if row['fingerprint'] != fingerprint:
                    raise GenError('conflict', '请求编号已用于另一项生成', 409)
                return self.job(owner, row['id']), False
            self.db.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?)', (owner, value['id'], request_id, fingerprint, json.dumps(value), time.time()))
            self.db.commit()
            for j in self.jobs_all(owner)[30:]:
                if j['state'] not in ('queued', 'running'):
                    self.delete_job(owner, j['id'])
            return value, True

    def update_job(self, owner, jid, update, active_only=True):
        with self.lock:
            try:
                j = self.job(owner, jid)
            except GenError:
                return None
            if active_only and j['state'] not in ('queued', 'running'):
                return None
            j.update(update)
            self.db.execute('UPDATE jobs SET value=? WHERE owner=? AND id=?', (json.dumps(j), owner, jid))
            self.db.commit()
            return j

    def image(self, owner, iid):
        with self.lock:
            row = self.db.execute('SELECT mime,value FROM images WHERE owner=? AND id=?', (owner, iid)).fetchone()
            if not row:
                raise GenError('missing', '图片已过期或不存在', 404)
            return row['mime'], bytes(row['value'])

    def add_image(self, owner, jid, data, mime, preview=False):
        with self.lock:
            j = self.job(owner, jid)
            if j['state'] not in ('queued', 'running'):
                return None
            used = self.db.execute('SELECT COALESCE(SUM(LENGTH(value)),0) FROM images WHERE owner=?', (owner,)).fetchone()[0]
            total = self.db.execute('SELECT COALESCE(SUM(LENGTH(value)),0) FROM images').fetchone()[0]
            if used + len(data) > 128 * 1024**2 or total + len(data) > 1024**3:
                raise GenError('rate', '生成记录存储已满，请清空记录', 429)
            iid = uuid.uuid4().hex
            self.db.execute('INSERT INTO images VALUES(?,?,?,?,?,?,?)', (owner, jid, iid, mime, data, int(preview), time.time()))
            if preview:
                self.db.execute('DELETE FROM images WHERE owner=? AND job=? AND preview=1 AND id<>?', (owner, jid, iid))
            self.db.commit()
            return {'url': '/api/generation/images/' + iid, 'mime': mime}

    def delete_job(self, owner, jid):
        with self.lock:
            j = self.job(owner, jid)
            if j['state'] in ('queued', 'running'):
                raise GenError('busy', '请先取消正在执行的任务', 409)
            self.db.execute('DELETE FROM images WHERE owner=? AND job=?', (owner, jid))
            self.db.execute('DELETE FROM jobs WHERE owner=? AND id=?', (owner, jid))
            self.db.commit()

    def erase(self, owner):
        with self.lock:
            for table in ('images', 'jobs', 'profiles'):
                self.db.execute('DELETE FROM ' + table + ' WHERE owner=?', (owner,))
            self.db.execute('DELETE FROM sessions WHERE id=?', (owner,))
            self.db.commit()

    def cleanup(self):
        with self.lock:
            now = time.time()
            expired = [r['id'] for r in self.db.execute('SELECT id FROM sessions WHERE touched<? OR created<?', (now - IDLE, now - ABSOLUTE))]
            for sid in expired:
                self.erase(sid)
            self.db.execute('DELETE FROM images WHERE created<?', (now - RESULT_TTL,))
            self.db.execute('DELETE FROM jobs WHERE created<?', (now - RESULT_TTL,))
            self.db.commit()
            return expired
