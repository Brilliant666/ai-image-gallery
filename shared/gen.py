# -*- coding: utf-8 -*-
"""生图核心：服务商请求格式、参考图准备、任务记录（IndexedDB）、响应解析

页面里的配方栏（shared/recipe.py）调用 PL.gen：
  PL.gen.PROV / RATIOS              服务商与比例
  PL.gen.cfg() / setCfg(o)          服务商、模型、比例、张数（localStorage pl.gen）
  PL.gen.key(p) / setKey(p, k, remember)   API Key：默认只存在本标签页（sessionStorage），勾选「记住」才进 localStorage
  PL.gen.run({items, prompt, up})   发起一次生成，返回任务 id
  PL.gen.cancel(id) / jobs() / del(id) / clear()
  addEventListener('pl:gen', …)     任务状态变化（本页或其他标签页）
请求优先交给根目录的 /gen-sw.js（Service Worker）发出：切换图库时请求不中断。
不支持 Service Worker 时在页面里直接发，切换页面会中断（界面会提示）。
Key 只放在请求头里直接发给服务商，不写进任务记录，也不经过本站服务器。
"""

JS = r"""<script>
(function(){
const PROV = {
  openai:  {name:'OpenAI GPT Image', base:'https://api.openai.com/v1', models:['gpt-image-2.5-flare','gpt-image-2.5-sunburst','gpt-image-2','gpt-image-1.5'], get:'https://platform.openai.com/api-keys'},
  gemini:  {name:'Google Gemini · Nano Banana', base:'https://generativelanguage.googleapis.com/v1beta', models:['gemini-nano-banana-2.1','gemini-3-pro-image','gemini-3.1-flash-image','gemini-3.1-flash-lite-image'], get:'https://aistudio.google.com/apikey'},
  seedream:{name:'豆包 Seedream · 火山方舟', base:'https://ark.cn-beijing.volces.com/api/v3', models:['doubao-seedream-5-0-pro-260628','doubao-seedream-4-5-251128','doubao-seedream-4-0-250828'], get:'https://console.volcengine.com/ark'},
  qwen:    {name:'通义 Qwen-Image · 阿里云百炼', base:'https://dashscope.aliyuncs.com/api/v1', models:['qwen-image-2.0-pro','qwen-image-2.0'], get:'https://bailian.console.aliyun.com/'},
  relay:   {name:'自定义中转', base:'', models:['gpt-image-2','gpt-image-2.5-sunburst','gpt-image-2.5-flare','gpt-image-1','gemini-2.5-flash-image','flux-kontext-pro','qwen-image-edit','doubao-seedream-4-0-250828'], get:''},
};
const RATIOS = ['3:4','2:3','1:1','4:3','9:16','16:9'];
const SIZE = {
  std:  {'3:4':'1024x1536','2:3':'1024x1536','9:16':'1024x1536','1:1':'1024x1024','4:3':'1536x1024','16:9':'1536x1024'},
  gpt2: {'3:4':'1152x1536','2:3':'1024x1536','9:16':'1152x2048','1:1':'1024x1024','4:3':'1536x1152','16:9':'2048x1152'},
  ark:  {'3:4':'1728x2304','2:3':'1664x2496','9:16':'1440x2560','1:1':'2048x2048','4:3':'2304x1728','16:9':'2560x1440'},
  qwen: {'3:4':'1536*2048','2:3':'1344*2016','9:16':'1152*2048','1:1':'1664*1664','4:3':'2048*1536','16:9':'2048*1152'},
};
const TIMEOUT = 180000, KEEP = 30, DBN = 'pl-gen', ST = 'jobs';
const L = localStorage, S = sessionStorage;
const jget = (s, k, d) => { try{ const v = JSON.parse(s.getItem(k) || 'null'); return v && typeof v === 'object' ? v : d; }catch(_){ return d; } };
const jset = (s, k, v) => { try{ s.setItem(k, JSON.stringify(v)); }catch(_){} };

/* ── 设置与 Key ── */
const cfg = () => Object.assign({p:'relay', model:{}, base:{}, proto:'edits', field:'image[]', ratio:'3:4', n:1, remember:false}, jget(L, 'pl.gen', {}));
const setCfg = o => { jset(L, 'pl.gen', Object.assign(cfg(), o)); fire(); };
const modelOf = (c, p) => (c.model && c.model[p]) || PROV[p].models[0] || '';
const baseOf = (c, p) => {
  let b = ((c.base && c.base[p]) || PROV[p].base).trim().replace(/\/+$/, '');
  if (!b) return b;
  if (p === 'openai' || p === 'relay') return /\/v\d+(?:beta|alpha)?$/.test(b) ? b : b + '/v1';
  return b;
};
const key = p => (jget(S, 'pl.genkey', {})[p] || jget(L, 'pl.genkey', {})[p] || '');
function setKey(p, k, remember){
  const s = jget(S, 'pl.genkey', {}), l = jget(L, 'pl.genkey', {});
  if (k){ s[p] = k; if (remember) l[p] = k; else delete l[p]; } else { delete s[p]; delete l[p]; }
  jset(S, 'pl.genkey', s); jset(L, 'pl.genkey', l); fire();
}
const httpsOk = u => /^https:\/\/[^\s/?#]+(\/[^\s]*)?$/i.test(u);

/* ── 任务记录（与 gen-sw.js 共用一个 IndexedDB） ── */
function db(){ return new Promise((ok, no) => { const r = indexedDB.open(DBN, 1);
  r.onupgradeneeded = () => { if (!r.result.objectStoreNames.contains(ST)) r.result.createObjectStore(ST, {keyPath:'id'}); };
  r.onsuccess = () => ok(r.result); r.onerror = () => no(r.error); }); }
async function tx(mode, fn){ const d = await db(); try{ return await new Promise((ok, no) => {
  const t = d.transaction(ST, mode), st = t.objectStore(ST), r = fn(st); let v;
  if (r) r.onsuccess = () => { v = r.result; }; t.oncomplete = () => ok(v); t.onerror = () => no(t.error); }); } finally { d.close(); } }
const put = j => tx('readwrite', st => st.put(j));
const get = id => tx('readonly', st => st.get(id));
const all = () => tx('readonly', st => st.getAll()).then(a => (a || []).sort((x, y) => y.at - x.at));
const del = id => tx('readwrite', st => st.delete(id)).then(fire);
const clear = () => tx('readwrite', st => st.clear()).then(fire);
const bc = 'BroadcastChannel' in window ? new BroadcastChannel('pl-gen') : null;
function fire(){ dispatchEvent(new Event('pl:gen')); }

/* ── 参考图：同源中图 → 长边 1024 的 JPEG ── */
const loadImg = src => new Promise((ok, no) => { const im = new Image(); im.onload = () => ok(im); im.onerror = () => no(new Error('img')); im.src = src; });
async function refImg(src){
  const im = await loadImg(src), s = Math.min(1, 1024 / Math.max(im.naturalWidth, im.naturalHeight));
  const c = document.createElement('canvas'); c.width = Math.round(im.naturalWidth * s); c.height = Math.round(im.naturalHeight * s);
  const g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height); g.drawImage(im, 0, 0, c.width, c.height);
  const url = c.toDataURL('image/jpeg', 0.92), b64 = url.slice(url.indexOf(',') + 1);
  const bin = atob(b64), u8 = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
  return {mime:'image/jpeg', url, b64, blob: new Blob([u8], {type:'image/jpeg'})};
}

/* ── 各家请求格式 ── */
function build(p, c, k, prompt, imgs){
  const m = modelOf(c, p), base = baseOf(c, p), n = Math.max(1, Math.min(4, +c.n || 1)), r = RATIOS.includes(c.ratio) ? c.ratio : '3:4';
  const json = (url, headers, body) => ({url, headers: Object.assign({'content-type':'application/json'}, headers), body: JSON.stringify(body)});
  const rep = f => Array.from({length:n}, f);
  if (p === 'openai' || p === 'relay'){
    const size = (/^gpt-image-2/.test(m) ? SIZE.gpt2 : SIZE.std)[r];
    if (p === 'relay' && c.proto === 'json') return [json(base + '/images/generations', {authorization:'Bearer ' + k},
      {model:m, prompt, n, size, image:imgs.map(x => x.url)})];
    const field = p === 'relay' && c.field === 'image' ? 'image' : 'image[]';
    return [{url: base + '/images/edits', headers:{authorization:'Bearer ' + k},
      form: [['model', m], ['prompt', prompt], ['n', String(n)], ['size', size], ...imgs.map((x, i) => [field, x.blob, 'ref' + (i + 1) + '.jpg'])]}];
  }
  if (p === 'gemini') return rep(() => json(base + '/interactions', {'x-goog-api-key': k}, {model: m,
    input: [{type:'text', text: prompt}, ...imgs.map(x => ({type:'image', mime_type: x.mime, data: x.b64}))],
    response_format: {type:'image', aspect_ratio: r, image_size: /lite/.test(m) ? '1K' : '2K'}}));
  if (p === 'seedream') return rep(() => json(base + '/images/generations', {authorization:'Bearer ' + k},
    {model: m, prompt, image: imgs.map(x => x.url), size: SIZE.ark[r], response_format:'b64_json', watermark:false}));
  if (p === 'qwen') return [json(base + '/services/aigc/multimodal-generation/generation', {authorization:'Bearer ' + k},
    {model: m, input:{messages:[{role:'user', content:[...imgs.map(x => ({image: x.url})), {text: prompt}]}]},
     parameters:{n, size: SIZE.qwen[r], watermark:false, prompt_extend:true}})];
  throw new Error('provider');
}

/* ── 响应解析：在 JSON 里找图片（b64_json / image+data / inlineData / 图片 URL），跳过思考过程 ── */
function images(o, out){
  if (!o || typeof o !== 'object') return out;
  if (Array.isArray(o)){ o.forEach(x => images(x, out)); return out; }
  if (o.type === 'thought') return out;
  const inl = o.inlineData || o.inline_data;
  if (typeof o.b64_json === 'string') out.push({b64: o.b64_json, mime: 'image/' + (o.output_format || 'png')});
  else if (o.type === 'image' && typeof o.data === 'string') out.push({b64: o.data, mime: o.mime_type || o.mimeType || 'image/png'});
  else if (inl && typeof inl.data === 'string') out.push({b64: inl.data, mime: inl.mimeType || inl.mime_type || 'image/png'});
  else if (typeof o.image === 'string' && /^https:\/\//.test(o.image)) out.push({url: o.image});
  else if (typeof o.url === 'string' && /^https:\/\//.test(o.url) && !o.error) out.push({url: o.url});
  else Object.keys(o).forEach(k => images(o[k], out));
  return out;
}
const msgOf = j => j && (j.error && (j.error.message || j.error.code) || j.message || j.code || j.msg) || '';
function kind(status, msg, ex){
  const m = String(msg).toLowerCase();
  if (ex === 'timeout') return 'timeout';
  if (ex === 'cancel') return 'cancel';
  if (ex) return 'network';
  if (/safety|moderation|content[_ ]policy|sensitive|inspection|inappropriate|prohibited|blocked|违规|敏感|审核/.test(m)) return 'safety';
  if (status === 401 || status === 403) return 'auth';
  if (status === 429 || /quota|balance|insufficient|余额|额度/.test(m)) return 'rate';
  if (status === 404) return 'model';
  if (status >= 500) return 'server';
  return 'bad';
}
function parse(res){
  const out = [], seen = new Set(); let err = null;
  for (const r of res || []){
    if (r.error){ err = err || {k: kind(0, r.msg, r.error), msg: r.msg || ''}; continue; }
    let j = null; try{ j = JSON.parse(r.text); }catch(_){}
    if (r.status >= 400 || !j){ err = err || {k: kind(r.status, msgOf(j) || r.text, null), msg: String(msgOf(j) || r.text || '').slice(0, 300), status: r.status}; continue; }
    const got = images(j, []);
    for (const g of got){ const sig = g.url || g.b64; if (!seen.has(sig)){ seen.add(sig); out.push(g); } }   // Gemini 的 output_image 与最后一步重复，按完整内容去重
    if (!got.length) err = err || {k:'empty', msg: String(msgOf(j) || JSON.stringify(j)).slice(0, 300)};
  }
  return {out, err: out.length ? null : (err || {k:'empty', msg:''})};
}
const b64blob = (b64, mime) => { const bin = atob(b64), u8 = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i); return new Blob([u8], {type: mime}); };

/* ── 收尾：把原始响应变成图片（任何一页都可以做，重复做结果相同） ── */
async function finish(id){
  const j = await get(id); if (!j || j.state !== 'fetched') return;
  const {out, err} = parse(j.res);
  j.out = out.map(g => g.url ? {url: g.url} : {blob: b64blob(g.b64, g.mime), mime: g.mime});
  j.state = out.length ? 'done' : 'error'; j.err = err; delete j.res;
  await put(j); if (bc) bc.postMessage({id, state: j.state}); fire(); trim();
}
async function trim(){ const a = await all(); for (const j of a.slice(KEEP)) await tx('readwrite', st => st.delete(j.id)); }
async function sweep(){
  for (const j of await all()){
    if (j.state === 'fetched') await finish(j.id);
    else if ((j.state === 'running' || j.state === 'queued') && Date.now() - j.at > TIMEOUT + 90000){
      j.state = 'error'; j.err = {k:'timeout', msg:''}; await put(j); fire();
    }
  }
}
if (bc) bc.onmessage = e => { const m = e.data || {}; if (m.state === 'fetched') finish(m.id); else fire(); };

/* ── Service Worker（根目录 /gen-sw.js，只转发生图请求，不缓存任何东西） ── */
let swReg = null;
const swOk = 'serviceWorker' in navigator && location.protocol !== 'file:' && window.isSecureContext;
function sw(up){
  if (!swOk) return Promise.resolve(null);
  if (!swReg) swReg = navigator.serviceWorker.register(up + 'gen-sw.js', {scope: up}).then(() => navigator.serviceWorker.ready).catch(() => null);
  return swReg;
}

async function run({items, prompt, up}){
  if (location.protocol === 'file:') throw {k:'offline'};
  const c = cfg(), p = PROV[c.p] ? c.p : 'openai', k = key(p);
  if (!k) throw {k:'nokey'};
  if (!httpsOk(baseOf(c, p))) throw {k:'base'};
  const imgs = await Promise.all(items.map(x => refImg(up + (x.send || x.im || x.th))));
  const reqs = build(p, c, k, prompt, imgs);
  const id = 'g' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  await put({id, at: Date.now(), p, model: modelOf(c, p), ratio: c.ratio, n: +c.n || 1, prompt, refs: items.map(x => x.th), state:'queued'});
  fire();
  const reg = await sw(up);
  if (reg && reg.active){ reg.active.postMessage({type:'run', id, reqs, timeout: TIMEOUT}); return id; }
  // 没有 Service Worker：在页面里直接发（切换页面会中断）
  const j = await get(id); j.state = 'running'; j.inPage = true; await put(j); fire();
  const ctl = new AbortController(); inPage.set(id, ctl);
  const timer = setTimeout(() => ctl.abort('timeout'), TIMEOUT);
  const res = await Promise.all(reqs.map(async q => {
    let body = q.body; if (q.form){ body = new FormData(); q.form.forEach(([a, b, n]) => n ? body.append(a, b, n) : body.append(a, b)); }
    try{ const r = await fetch(q.url, {method:'POST', headers: q.headers, body, signal: ctl.signal, credentials:'omit'}); return {status: r.status, text: await r.text()}; }
    catch(e){ return {error: ctl.signal.aborted ? String(ctl.signal.reason) : 'network', msg: String(e && e.message || e)}; }
  }));
  clearTimeout(timer); inPage.delete(id);
  const j2 = await get(id); if (!j2) return id;
  j2.state = ctl.signal.reason === 'cancel' ? 'canceled' : 'fetched'; j2.res = res; await put(j2); await finish(id); fire();
  return id;
}
const inPage = new Map();
async function cancel(id){
  if (inPage.has(id)) return inPage.get(id).abort('cancel');
  const reg = swReg && await swReg; if (reg && reg.active) reg.active.postMessage({type:'cancel', id});
}

PL.gen = {PROV, RATIOS, cfg, setCfg, modelOf, baseOf, key, setKey, run, cancel, jobs: all, del, clear, sw, swOk, parse, build, httpsOk};
sweep();
})();
</script>"""
