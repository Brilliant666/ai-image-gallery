/* photoai.life 生图中继（Service Worker）
 *
 * 只做一件事：替页面发出生图请求，并把响应写进 IndexedDB，这样用户在请求进行中切换图库，
 * 请求也不会被中断，结果在任何一页都能读到。
 *   - 没有 fetch 事件处理：不拦截、不缓存任何页面和图片，不会出现旧版本
 *   - 只接受 https 地址；API Key 只在请求头里用一次，不写进存储
 *   - 解析各家响应、生成图片的工作由页面完成（shared/recipe.py 的 GEN 段），这里只存原始响应
 * 消息：{type:'run', id, reqs:[{url, headers, body | form}], timeout} / {type:'cancel', id}
 * 通知：BroadcastChannel('pl-gen') 发 {id, state}
 */
const DB = 'pl-gen', STORE = 'jobs', BC = new BroadcastChannel('pl-gen');
const live = new Map();   // id → AbortController

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));

function db() {
  return new Promise((ok, no) => {
    const r = indexedDB.open(DB, 1);
    r.onupgradeneeded = () => { if (!r.result.objectStoreNames.contains(STORE)) r.result.createObjectStore(STORE, {keyPath: 'id'}); };
    r.onsuccess = () => ok(r.result); r.onerror = () => no(r.error);
  });
}
async function patch(id, fields) {
  const d = await db();
  await new Promise((ok, no) => {
    const tx = d.transaction(STORE, 'readwrite'), st = tx.objectStore(STORE), g = st.get(id);
    g.onsuccess = () => { if (g.result) st.put(Object.assign(g.result, fields)); };
    tx.oncomplete = ok; tx.onerror = () => no(tx.error);
  });
  d.close();
}

function body(q) {
  if (!q.form) return q.body;
  const f = new FormData();
  for (const [k, v, name] of q.form) name ? f.append(k, v, name) : f.append(k, v);
  return f;
}

self.addEventListener('message', e => {
  const m = e.data || {};
  if (m.type === 'cancel') { const c = live.get(m.id); if (c) c.abort('cancel'); return; }
  if (m.type !== 'run' || typeof m.id !== 'string' || !Array.isArray(m.reqs) || !m.reqs.length) return;
  if (!m.reqs.every(q => typeof q.url === 'string' && /^https:\/\//i.test(q.url))) return;
  const ctl = new AbortController(), t0 = Date.now();
  const timer = setTimeout(() => ctl.abort('timeout'), Math.min(+m.timeout || 180000, 270000));
  live.set(m.id, ctl);
  e.waitUntil((async () => {
    await patch(m.id, {state: 'running', sw: true});
    BC.postMessage({id: m.id, state: 'running'});
    const res = await Promise.all(m.reqs.map(async q => {
      try {
        const r = await fetch(q.url, {method: 'POST', headers: q.headers || {}, body: body(q), signal: ctl.signal, credentials: 'omit'});
        return {status: r.status, text: await r.text()};
      } catch (err) {
        return {error: ctl.signal.aborted ? String(ctl.signal.reason || 'abort') : 'network', msg: String(err && err.message || err)};
      }
    }));
    clearTimeout(timer); live.delete(m.id);
    const reason = ctl.signal.aborted ? String(ctl.signal.reason || '') : '';
    await patch(m.id, {state: reason === 'cancel' ? 'canceled' : 'fetched', res, ms: Date.now() - t0});
    BC.postMessage({id: m.id, state: reason === 'cancel' ? 'canceled' : 'fetched'});
  })());
});
