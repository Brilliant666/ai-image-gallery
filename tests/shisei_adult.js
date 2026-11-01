// Execute the generated Shisei gallery script with a small DOM fixture; no image/network access.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(process.argv[2], 'utf8');
const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).find(s => s.includes('const DB = '));
assert(script);
assert(!/unblur|data-blur|blurTap|ADULT_MODE === 'blur'/.test(script));

function boot(hash = '') {
  const elements = new Map(), events = new Map();
  function element(key) {
    if (elements.has(key)) return elements.get(key);
    const classes = new Set();
    const e = {
      innerHTML: '', textContent: '', value: '', hidden: false, dataset: {}, options: Array.from({length: 4}, () => ({})),
      children: [{}, {}], listeners: {}, style: {setProperty() {}},
      classList: {add: c => classes.add(c), remove: c => classes.delete(c), contains: c => classes.has(c),
        toggle(c, on) { on = on ?? !classes.has(c); on ? classes.add(c) : classes.delete(c); return on; }},
      addEventListener(k, f) { this.listeners[k] = f; }, setAttribute(k, v) { this[k] = v; },
      getAttribute(k) { return this[k]; }, removeAttribute(k) { delete this[k]; }, querySelectorAll() { return []; },
    };
    elements.set(key, e); return e;
  }
  const PL = {adult: false, lang: 'zh', top: () => element('#modal'),
    openDialog(e) { e.classList.add('open'); },
    closeDialog(e) { e.classList.remove('open'); e.listeners['pl:close']?.(); },
  };
  const context = vm.createContext({PL, URLSearchParams, location: {hash}, navigator: {},
    document: {querySelector: element, getElementById: id => id ? element('#' + id) : null, addEventListener() {}},
    addEventListener(k, f) { events.set(k, f); }, window: {},
    Image: function() {}, setTimeout: () => 1, clearTimeout() {},
  });
  // Expose only state/actions needed for assertions, inside the actual script closure.
  vm.runInContext(script.replace(/\}\)\(\);\s*$/, 'globalThis.probe = {DB, S, visible, draw, drawCats, openM, getView: () => VIEW};})();'), context);
  return {...context.probe, PL, element, adult(on) { PL.adult = on; events.get('pl:adult')(); }};
}

const g = boot();
const expectedAdult = p => ['全身・セクシー', 'ふたり'].includes(p.s) || p.x;
assert.equal(g.visible().length, 96);
assert.equal(g.getView().length, 96);
assert(g.visible().every(p => !expectedAdult(p)));
assert.match(g.element('#count').innerHTML, /96/);
assert.match(g.element('#count').innerHTML, /395/);
assert(!/全身・セクシー|ふたり/.test(g.element('#tabs').innerHTML));
assert(!/data-x="1"/.test(g.element('#grid').innerHTML));
g.S.view = 'card'; g.draw();
assert.equal(g.getView().length, 395);
assert.match(g.element('#count').innerHTML, /395/);
g.adult(true);
assert.equal(g.visible().length, 280);
assert.equal(g.getView().length, 1133);
assert.match(g.element('#tabs').innerHTML, /全身・セクシー/);
assert.match(g.element('#tabs').innerHTML, /ふたり/);
g.adult(false);
assert.equal(g.getView().length, 395);

// An entirely hidden series or category hash must remain selected with zero results.
for (const hash of ['#series=全身・セクシー', '#series=ふたり', '#series=上半身&cat=セクシー系']) {
  const h = boot(hash), selected = [h.S.series, h.S.cat];
  assert.equal(h.getView().length, 0, hash);
  assert.match(h.element('#grid').innerHTML, /data-adult-go/, hash);
  assert.match(h.element('#count').innerHTML, /0/, hash);
  h.adult(true);
  assert.deepEqual([h.S.series, h.S.cat], selected);
  assert(h.getView().length > 0, hash);
  assert(h.getView().every(o => o.p.s === selected[0] && (!selected[1] || o.p.c === selected[1])));
  h.adult(false);
  assert.deepEqual([h.S.series, h.S.cat], selected);
  assert.equal(h.getView().length, 0);
}

// Suggestive in an otherwise public series cannot be found by search while 18+ is off.
const other = g.DB.poses.find(p => p.x && p.s === '全身・標準');
g.S.q = other.p.toLowerCase(); g.S.view = 'pose'; g.draw();
assert.equal(g.getView().length, 0);
assert.match(g.element('#grid').innerHTML, /data-adult-go/);
g.adult(true);
assert.equal(g.getView().length, 1);
g.openM(0, g.getView()[0].d);
assert(g.element('#modal').classList.contains('open'));
assert(g.element('#mimg').src);
g.adult(false);
assert(!g.element('#modal').classList.contains('open'));
for (const id of ['mimg', 'mimgLo', 'cmpA', 'cmpB']) assert.equal(g.element('#' + id).src, undefined);
assert.equal(g.element('#mfull').href, undefined);
assert.equal(g.element('#mdl').href, undefined);
assert.equal(g.element('#mang').innerHTML, '');

// A populated VIEW after filtering must not keep an old adult modal alive by reused index.
g.S.q = ''; g.adult(true);
const adultIndex = g.getView().findIndex(o => o.p.x);
g.openM(adultIndex, g.getView()[adultIndex].d);
g.adult(false);
assert(g.getView()[adultIndex]);
assert(!g.element('#modal').classList.contains('open'));
console.log('Shisei filters/count/hash/modal regressions passed');
