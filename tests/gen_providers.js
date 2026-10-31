// 生图核心单测：各家请求格式与响应解析（不发真实请求）
// 用法: node tests/gen_providers.js <从 shared/gen.py 提取的 JS>
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
const mk = st => ({getItem: k => (k in st ? st[k] : null), setItem: (k, v) => { st[k] = String(v); }, removeItem: k => { delete st[k]; }});
const store = {}, sstore = {};
global.window = global; global.localStorage = mk(store); global.sessionStorage = mk(sstore);
global.location = {protocol: 'https:'}; global.isSecureContext = true;
global.indexedDB = {open: () => { const r = {}; setTimeout(() => r.onerror && r.onerror(new Error('no idb'))); return r; }};
global.navigator = {}; global.PL = {};
global.dispatchEvent = () => {}; global.Event = class { constructor(n) { this.type = n; } };
global.atob = s => Buffer.from(s, 'base64').toString('binary');
global.Blob = class { constructor(p, o) { this.parts = p; this.type = o && o.type; } };
process.on('unhandledRejection', () => {});
eval(src);
const G = PL.gen;
let fail = 0;
const ok = (c, m) => { if (!c) { fail++; console.log('FAIL', m); } else console.log('ok  ', m); };
const img = [{mime: 'image/jpeg', url: 'data:image/jpeg;base64,AAAA', b64: 'AAAA', blob: {fake: 1}}, {mime: 'image/jpeg', url: 'data:image/jpeg;base64,BBBB', b64: 'BBBB', blob: {fake: 2}}];
const c = (p, extra) => Object.assign({p, model: {}, base: {}, ratio: '3:4', n: 2}, extra || {});

// OpenAI：multipart，image[] 重复，Bearer
let q = G.build('openai', c('openai'), 'sk-x', 'hello', img);
ok(q.length === 1 && q[0].url === 'https://api.openai.com/v1/images/edits', 'openai url');
ok(q[0].headers.authorization === 'Bearer sk-x' && !q[0].headers['content-type'], 'openai auth, multipart (no content-type)');
const f = Object.fromEntries(q[0].form.filter(x => x[0] !== 'image[]'));
ok(f.model === 'gpt-image-2.5-flare' && f.n === '2' && f.size === '1152x1536', 'openai model/n/size(gpt-2 custom 3:4)');
ok(q[0].form.filter(x => x[0] === 'image[]').length === 2, 'openai two image[] parts');
q = G.build('openai', c('openai', {model: {openai: 'gpt-image-1.5'}, ratio: '16:9'}), 'k', 'p', img);
ok(Object.fromEntries(q[0].form.filter(x => x[0] !== 'image[]')).size === '1536x1024', 'openai gpt-image-1.5 uses std size');
// 中转：自定义 Base URL
q = G.build('relay', c('relay', {base: {relay: 'https://relay.example.com/v1/'}}), 'k', 'p', img);
ok(q[0].url === 'https://relay.example.com/v1/images/edits', 'relay base url trimmed');

// 自定义中转：空白、末尾斜杠、版本路径、两种接口与图片字段。
ok(G.cfg().p === 'relay', 'new user starts with configurable relay');
ok(G.baseOf({base:{relay:'  https://relay.example.com/  '}}, 'relay') === 'https://relay.example.com/v1', 'relay origin adds v1');
ok(G.baseOf({base:{relay:'https://relay.example.com/api/v1/'}}, 'relay') === 'https://relay.example.com/api/v1', 'relay preserves version path');
ok(!G.baseOf(c('relay'), 'relay'), 'missing relay address stays empty');
q = G.build('relay', c('relay', {base:{relay:'https://relay.example.com'}, field:'image'}), 'k', 'p', img);
ok(q[0].form.filter(x => x[0] === 'image').length === 2 && !q[0].form.some(x => x[0] === 'image[]'), 'relay repeated image field');
q = G.build('relay', c('relay', {base:{relay:'https://relay.example.com'}, proto:'json', n:3, model:{relay:'custom-model'}}), 'k', 'p', img);
let rb = JSON.parse(q[0].body);
ok(q.length === 1 && q[0].url === 'https://relay.example.com/v1/images/generations' && !q[0].form, 'relay JSON route');
ok(rb.model === 'custom-model' && rb.n === 3 && rb.prompt === 'p' && rb.image.length === 2 && rb.image[1] === img[1].url, 'relay JSON includes every reference and options');
ok(q[0].headers.authorization === 'Bearer k' && q[0].headers['content-type'] === 'application/json', 'relay JSON auth');
ok(G.baseOf({base:{gemini:'https://gemini.example.com/v1beta/'}}, 'gemini') === 'https://gemini.example.com/v1beta', 'custom native-provider base');

// Gemini：Interactions API，每张一个请求
q = G.build('gemini', c('gemini'), 'AIza', 'hello', img);
ok(q.length === 2 && q[0].url === 'https://generativelanguage.googleapis.com/v1beta/interactions', 'gemini n requests + url');
let b = JSON.parse(q[0].body);
ok(q[0].headers['x-goog-api-key'] === 'AIza' && !q[0].headers.authorization, 'gemini api key header');
ok(b.model === 'gemini-nano-banana-2.1' && b.input[0].type === 'text' && b.input[1].type === 'image' && b.input[1].mime_type === 'image/jpeg' && b.input[1].data === 'AAAA', 'gemini input blocks');
ok(b.response_format.type === 'image' && b.response_format.aspect_ratio === '3:4' && b.response_format.image_size === '2K', 'gemini response_format');
b = JSON.parse(G.build('gemini', c('gemini', {model: {gemini: 'gemini-3.1-flash-lite-image'}}), 'k', 'p', img)[0].body);
ok(b.response_format.image_size === '1K', 'gemini lite only 1K');

// Seedream：data URI 数组，b64_json，关水印
q = G.build('seedream', c('seedream'), 'ark', 'hello', img);
b = JSON.parse(q[0].body);
ok(q.length === 2 && q[0].url === 'https://ark.cn-beijing.volces.com/api/v3/images/generations', 'seedream url + n requests');
ok(Array.isArray(b.image) && b.image[0].startsWith('data:image/jpeg;base64,') && b.response_format === 'b64_json' && b.watermark === false && b.size === '1728x2304', 'seedream body');
const [w, h] = b.size.split('x').map(Number); ok(w * h >= 921600 && w * h <= 4624220 && Math.abs(w / h - 0.75) < 0.01, 'seedream size in 5.0 pro range, 3:4');

// Qwen：messages content，图片在前文字在后，W*H
q = G.build('qwen', c('qwen'), 'sk', 'hello', img);
b = JSON.parse(q[0].body);
ok(q[0].url === 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation', 'qwen url');
const ct = b.input.messages[0].content;
ok(ct.length === 3 && ct[0].image && ct[2].text === 'hello' && b.parameters.n === 2 && b.parameters.size === '1536*2048', 'qwen body');
const [qw, qh] = b.parameters.size.split('*').map(Number); ok(qw * qh <= 2048 * 2048 && qw % 16 === 0 && qh % 16 === 0, 'qwen size limits');
ok(G.build('qwen', c('qwen', {n: 9}), 'k', 'p', img).length === 1 && JSON.parse(G.build('qwen', c('qwen', {n: 9}), 'k', 'p', img)[0].body).parameters.n === 4, 'n clamped to 4');

// 解析：各家成功响应
const P = (status, o) => ({status, text: typeof o === 'string' ? o : JSON.stringify(o)});
let r = G.parse([P(200, {data: [{b64_json: 'IMG1'}, {b64_json: 'IMG2'}]})]);
ok(r.out.length === 2 && r.out[0].b64 === 'IMG1' && !r.err, 'parse openai b64_json');
r = G.parse([P(200, {id: 'x', steps: [{type: 'thought', summary: [{type: 'image', data: 'THINK'}]}, {type: 'model_output', content: [{type: 'text', text: 'hi'}, {type: 'image', mime_type: 'image/png', data: 'GEM'}]}], output_image: {data: 'GEM', mime_type: 'image/png'}})]);
ok(r.out.length === 1 && r.out[0].b64 === 'GEM', 'parse gemini interactions, skip thought, dedupe output_image');
r = G.parse([P(200, {candidates: [{content: {parts: [{text: 'a'}, {inlineData: {mimeType: 'image/png', data: 'GC'}}]}}]})]);
ok(r.out.length === 1 && r.out[0].b64 === 'GC', 'parse gemini generateContent inlineData');
r = G.parse([P(200, {data: [{b64_json: 'SD', size: '2048x2048'}], usage: {}})]);
ok(r.out[0].b64 === 'SD', 'parse seedream');
r = G.parse([P(200, {output: {choices: [{message: {content: [{image: 'https://dashscope-result.oss.aliyuncs.com/a.png?Expires=1'}]}}]}})]);
ok(r.out.length === 1 && r.out[0].url.startsWith('https://'), 'parse qwen url');

// 解析：错误分类
const E = (st, o) => G.parse([P(st, o)]).err.k;
ok(E(401, {error: {message: 'Incorrect API key provided'}}) === 'auth', 'err 401 auth');
ok(E(429, {error: {message: 'Rate limit reached'}}) === 'rate', 'err 429 rate');
ok(E(400, {error: {code: 'moderation_blocked', message: 'Your request was rejected by the safety system'}}) === 'safety', 'err openai safety');
ok(E(400, {code: 'DataInspectionFailed', message: 'Input data may contain inappropriate content.'}) === 'safety', 'err qwen inspection');
ok(E(400, {error: {code: 'InputImageSensitiveContentDetected', message: 'sensitive'}}) === 'safety', 'err seedream sensitive');
ok(E(404, {error: {message: 'model not found'}}) === 'model', 'err 404 model');
ok(E(503, 'Service Unavailable') === 'server', 'err 5xx');
ok(E(200, {data: []}) === 'empty', 'err empty result');
ok(G.parse([{error: 'timeout', msg: 'aborted'}]).err.k === 'timeout', 'err timeout');
ok(G.parse([{error: 'network', msg: 'Failed to fetch'}]).err.k === 'network', 'err network (CORS / region)');
// 部分成功：两张请求一张失败，仍算成功
r = G.parse([P(200, {data: [{b64_json: 'A'}]}), P(500, 'x')]);
ok(r.out.length === 1 && !r.err, 'partial success keeps images');

// 设置与 Key：默认只进 sessionStorage
G.setKey('openai', 'sk-temp', false);
ok(G.key('openai') === 'sk-temp' && !(store['pl.genkey'] || '').includes('sk-temp') && (sstore['pl.genkey'] || '').includes('sk-temp'), 'key only in sessionStorage by default');
G.setKey('openai', 'sk-keep', true);
ok((store['pl.genkey'] || '').includes('sk-keep'), 'key remembered when asked');
G.setKey('openai', '', false);
ok(!G.key('openai') && !(store['pl.genkey'] || '').includes('sk-') && !(sstore['pl.genkey'] || '').includes('sk-'), 'forget clears both');
ok(G.httpsOk('https://a.b/v1') && !G.httpsOk('http://a.b') && !G.httpsOk('javascript:alert(1)'), 'httpsOk');

console.log(fail ? `\n${fail} FAILED` : '\nALL OK');
process.exit(fail ? 1 : 0);
