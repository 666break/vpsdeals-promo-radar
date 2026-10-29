// yt_upload.mjs — drive YouTube Studio's upload dialog over CDP.
// Usage: node scripts/yt_upload.mjs --port 9224 --file "C:\path\video.mp4" --title "..." --desc-file "desc.txt" [--dry]
// Prints a JSON result on the last line.
import fs from 'node:fs';

const argv = process.argv.slice(2);
const arg = (k, d = null) => { const i = argv.indexOf(k); return i > -1 ? argv[i + 1] : d; };
const flag = (k) => argv.includes(k);

const PORT = arg('--port', '9224');
const FILE = arg('--file');
const TITLE = arg('--title');
const DESC_FILE = arg('--desc-file');
const DRY = flag('--dry');
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const pages = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
const target = pages.filter(t => t.type === 'page' && t.url.includes('studio.youtube.com'))[0]
  || pages.filter(t => t.type === 'page')[0];
if (!target) { console.log(JSON.stringify({ ok: false, err: 'no studio tab' })); process.exit(1); }

const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((res, rej) => { ws.addEventListener('open', res, { once: true }); ws.addEventListener('error', rej, { once: true }); });

let id = 0; const pending = new Map(); const events = [];
ws.addEventListener('message', (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { const { res, rej } = pending.get(m.id); pending.delete(m.id); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); }
  else if (m.method) events.push(m);
});
const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); });

const ev = async (expression) => {
  const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error('eval: ' + (r.exceptionDetails.text || '') + ' ' + JSON.stringify(r.exceptionDetails.exception?.description || '').slice(0, 300));
  return r.result.value;
};

const log = (...a) => console.error(...a);

await send('Page.enable');
await send('Runtime.enable');
await send('DOM.enable');
try { await send('Page.bringToFront'); } catch {}

// helper injected once
const HELPERS = `
window.__c = {
  q: (s) => document.querySelector(s),
  deep: (s) => { let f = null; const walk = (r) => { if (f) return; const e = r.querySelector(s); if (e) { f = e; return; } r.querySelectorAll('*').forEach(x => { if (x.shadowRoot) walk(x.shadowRoot); }); }; walk(document); return f; },
  click: (s) => { const e = window.__c.deep(s); if (!e) return 'NOTFOUND'; e.scrollIntoView({block:'center'}); e.click(); return 'CLICKED'; },
  txt: () => document.body.innerText.slice(0, 1200),
  inputs: () => [...document.querySelectorAll('input, textarea, [contenteditable="true"]')].map(e => ({
    tag: e.tagName, id: e.id, type: e.type, name: e.name,
    ce: e.getAttribute && e.getAttribute('contenteditable'),
    val: (e.value !== undefined ? e.value : e.innerText || '').slice(0, 60)
  }))
};
'ok'`;
await ev(HELPERS);

const result = { ok: false, steps: [] };
const step = (name, v) => { result.steps.push(name + ': ' + (typeof v === 'string' ? v : JSON.stringify(v))); log('  ' + name + ' -> ' + (typeof v === 'string' ? v : JSON.stringify(v)).slice(0, 200)); };

// 1. make sure we are on studio home
await send('Page.navigate', { url: 'https://studio.youtube.com/' });
await sleep(9000);
await ev(HELPERS);
step('nav', await ev(`location.href`));

// 2. open the create menu (id has changed across Studio versions)
const opened = await ev(`window.__c.click('#create-icon')`);
step('create-btn', opened);
await sleep(1800);
await ev(HELPERS);

// 3. intercept the file chooser before clicking upload
await send('Page.setInterceptFileChooserDialog', { enabled: true });
events.length = 0;
let clicked = 'NOTFOUND';
for (const sel of ['#upload-button', '#menu-paper-icon-item-0', 'ytcp-uploads-file-picker input[type=file]']) {
  clicked = await ev(`window.__c.click(${JSON.stringify(sel)})`);
  step('click ' + sel, clicked);
  if (clicked === 'CLICKED') break;
}

// 4. wait for fileChooserOpened
let chooser = null;
for (let i = 0; i < 40 && !chooser; i++) {
  chooser = events.find(e => e.method === 'Page.fileChooserOpened');
  if (!chooser) await sleep(500);
}
if (!chooser) {
  step('chooser', 'NOT OPENED');
  step('dom', await ev(`JSON.stringify(window.__c.inputs())`));
  console.log(JSON.stringify(result));
  process.exit(2);
}
step('chooser', 'backendNodeId=' + chooser.params.backendNodeId);

if (DRY) { console.log(JSON.stringify(result)); process.exit(0); }

// 5. attach the file
await send('DOM.setFileInputFiles', { files: [FILE], backendNodeId: chooser.params.backendNodeId });
step('setFile', 'done');
await sleep(12000);

// 6. inspect the dialog
step('dialogTxt', await ev(`document.body.innerText.replace(/\\n+/g,' | ').slice(0,900)`));
step('fields', await ev(`JSON.stringify(window.__c.inputs())`));

console.log(JSON.stringify(result));
process.exit(0);
