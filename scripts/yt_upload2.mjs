// yt_upload2.mjs — attach a file to Studio's upload dialog and fill metadata.
// Attaches the file through the DOM node directly (input[name=Filedata]); the
// fileChooserOpened event is not reliable in current Studio builds.
import fs from 'node:fs';

const argv = process.argv.slice(2);
const arg = (k, d = null) => { const i = argv.indexOf(k); return i > -1 ? argv[i + 1] : d; };
const PORT = arg('--port', '9224');
const FILE = arg('--file');
const TITLE = arg('--title', '');
const DESC = arg('--desc-file') ? fs.readFileSync(arg('--desc-file'), 'utf8') : '';
const STAGE = arg('--stage', 'attach'); // attach | meta | publish
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
const target = list.filter(t => t.type === 'page' && t.url.includes('studio.youtube.com'))[0];
if (!target) { console.log(JSON.stringify({ ok: false, err: 'no studio tab' })); process.exit(1); }

const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((res, rej) => { ws.addEventListener('open', res, { once: true }); ws.addEventListener('error', rej, { once: true }); });
let id = 0; const pending = new Map();
ws.addEventListener('message', (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { const { res, rej } = pending.get(m.id); pending.delete(m.id); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); }
});
const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async (expr) => {
  const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) return 'ERR:' + (r.exceptionDetails.exception?.description || r.exceptionDetails.text || '').slice(0, 200);
  return r.result.value;
};
const log = (...a) => console.error(...a);
const out = { ok: false, stage: STAGE, steps: [] };
const step = (k, v) => { const s = k + ': ' + (typeof v === 'string' ? v : JSON.stringify(v)); out.steps.push(s); log('  ' + s.slice(0, 260)); };

await send('Page.enable'); await send('Runtime.enable'); await send('DOM.enable');
try { await send('Page.bringToFront'); } catch {}

const HELP = `window.__c={
 deep:(s)=>{let f=null;const w=(r)=>{if(f)return;const e=r.querySelector(s);if(e){f=e;return;}r.querySelectorAll('*').forEach(x=>{if(x.shadowRoot)w(x.shadowRoot)})};w(document);return f},
 click:(s)=>{const e=window.__c.deep(s);if(!e)return 'NOTFOUND';e.scrollIntoView({block:'center'});e.click();return 'CLICKED'},
 setText:(s,t)=>{const e=window.__c.deep(s);if(!e)return 'NOTFOUND';e.focus();
   const sel=window.getSelection();const r=document.createRange();r.selectNodeContents(e);sel.removeAllRanges();sel.addRange(r);
   document.execCommand('insertText',false,t);
   if(!(e.innerText||'').includes(t.slice(0,12))){e.textContent=t;e.dispatchEvent(new InputEvent('input',{bubbles:true,composed:true}))}
   return 'SET:'+(e.innerText||'').slice(0,50)},
 txt:()=>document.body.innerText.replace(/\\n+/g,' | ').slice(0,1400)
};'ok'`;
await ev(HELP);

if (STAGE === 'setfiles') {
  const doc = await send('DOM.getDocument', { depth: -1, pierce: true });
  const q = await send('DOM.querySelector', { nodeId: doc.root.nodeId, selector: 'ytcp-uploads-file-picker input[type=file]' });
  step('nodeId', q.nodeId);
  if (!q.nodeId) { console.log(JSON.stringify(out)); process.exit(7); }
  await send('DOM.setFileInputFiles', { files: [FILE], nodeId: q.nodeId });
  step('set', 'ok');
  for (let i = 0; i < 6; i++) {
    await sleep(4000);
    step('t' + (i * 4 + 4) + 's', await ev(`(document.body.innerText.match(/上传[^|]{0,40}|详情|进度|%/)||[''])[0] + ' || len=' + document.body.innerText.length`));
  }
  step('dialog', await ev(`window.__c.txt()`));
  out.ok = true;
  console.log(JSON.stringify(out));
  process.exit(0);
}

if (STAGE === 'attach3') {
  await ev(HELP);
  const rect = await ev(`(()=>{const b=document.querySelector('#select-files-button');if(!b)return null;const r=b.getBoundingClientRect();return {x:Math.round(r.left+r.width/2),y:Math.round(r.top+r.height/2),w:Math.round(r.width),h:Math.round(r.height)}})()`);
  step('rect', rect);
  if (!rect) { console.log(JSON.stringify(out)); process.exit(5); }
  const opened = [];
  ws.addEventListener('message', (e) => { const m = JSON.parse(e.data); if (m.method === 'Page.fileChooserOpened') opened.push(m.params); });
  await send('Page.setInterceptFileChooserDialog', { enabled: true });
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: rect.x, y: rect.y, button: 'none', clickCount: 0 });
  await sleep(200);
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: rect.x, y: rect.y, button: 'left', clickCount: 1 });
  await sleep(80);
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: rect.x, y: rect.y, button: 'left', clickCount: 1 });
  step('real click', 'dispatched');
  let ch = null;
  for (let i = 0; i < 40 && !ch; i++) { ch = opened[0]; if (!ch) await sleep(400); }
  step('chooser', ch ? 'backendNodeId=' + ch.backendNodeId : 'NOT OPENED');
  if (ch) {
    await send('DOM.setFileInputFiles', { files: [FILE], backendNodeId: ch.params ? ch.params.backendNodeId : ch.backendNodeId });
    step('setFile', 'ok');
    await sleep(12000);
    step('dialog', await ev(`window.__c.txt()`));
    out.ok = true;
  }
  console.log(JSON.stringify(out));
  process.exit(ch ? 0 : 6);
}

if (STAGE === 'attach2') {
  await ev(HELP);
  // list the buttons inside the upload dialog so the selector is not a guess
  step('buttons', await ev(`JSON.stringify([...document.querySelectorAll('ytcp-uploads-dialog ytcp-button, ytcp-uploads-dialog button, ytcp-uploads-file-picker ytcp-button')].map(b=>({id:b.id,cls:b.className&&b.className.toString().slice(0,40),txt:(b.innerText||'').slice(0,24)})))`));
  await send('Page.setInterceptFileChooserDialog', { enabled: true });
  const opened = [];
  ws.addEventListener('message', (e) => { const m = JSON.parse(e.data); if (m.method === 'Page.fileChooserOpened') opened.push(m.params); });
  step('click select', await ev(`(()=>{const b=document.querySelector('#select-files-button')||[...document.querySelectorAll('ytcp-button,button')].find(x=>(x.innerText||'').trim()==='选择文件'||(x.innerText||'').trim()==='Select files');if(!b)return 'NOTFOUND';b.click();return 'CLICKED'})()`));
  let ch = null;
  for (let i = 0; i < 30 && !ch; i++) { ch = opened[0]; if (!ch) await sleep(400); }
  step('chooser', ch ? 'backendNodeId=' + ch.backendNodeId : 'NOT OPENED');
  if (ch) {
    await send('DOM.setFileInputFiles', { files: [FILE], backendNodeId: ch.backendNodeId });
    step('setFile', 'ok');
    await sleep(10000);
    step('dialog', await ev(`window.__c.txt()`));
    out.ok = true;
  }
  console.log(JSON.stringify(out));
  process.exit(ch ? 0 : 4);
}

if (STAGE === 'attach') {
  step('nav', await ev(`(async()=>{ if(!location.href.includes('studio.youtube.com')){location.href='https://studio.youtube.com/'} return location.href })()`));
  await sleep(6000);
  await ev(HELP);
  step('click upload', await ev(`window.__c.click('#upload-button')`));
  // wait for the hidden file input to appear
  let found = false;
  for (let i = 0; i < 30 && !found; i++) {
    found = await ev(`!!document.querySelector('input[type=file][name=Filedata]')`);
    if (!found) await sleep(400);
  }
  step('file input present', String(found));
  if (!found) { console.log(JSON.stringify(out)); process.exit(2); }
  const doc = await send('DOM.getDocument', { depth: -1, pierce: true });
  let nodeId = null;
  try {
    const q = await send('DOM.querySelector', { nodeId: doc.root.nodeId, selector: 'input[type=file][name=Filedata]' });
    nodeId = q.nodeId;
  } catch (e) { step('querySelector', 'ERR ' + e.message.slice(0, 120)); }
  if (!nodeId) { step('nodeId', 'NOT FOUND'); console.log(JSON.stringify(out)); process.exit(3); }
  await send('DOM.setFileInputFiles', { files: [FILE], nodeId });
  step('setFileInputFiles', 'ok nodeId=' + nodeId);
  await sleep(8000);
  step('dialog', await ev(`window.__c.txt()`));
  out.ok = true;
  console.log(JSON.stringify(out));
  process.exit(0);
}

if (STAGE === 'meta') {
  await ev(HELP);
  step('title', await ev(`window.__c.setText('#title-textarea #textbox', ${JSON.stringify(TITLE)})`));
  await sleep(1200);
  step('desc', await ev(`window.__c.setText('#description-textarea #textbox', ${JSON.stringify(DESC)})`));
  await sleep(1200);
  step('kids', await ev(`window.__c.click('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]')`));
  await sleep(800);
  step('dialog', await ev(`window.__c.txt()`));
  out.ok = true;
  console.log(JSON.stringify(out));
  process.exit(0);
}

if (STAGE === 'publish') {
  await ev(HELP);
  for (let i = 0; i < 3; i++) {
    step('next' + i, await ev(`window.__c.click('#next-button')`));
    await sleep(2200);
  }
  step('public', await ev(`window.__c.click('tp-yt-paper-radio-button[name="PUBLIC"]')`));
  await sleep(1200);
  step('dialog', await ev(`window.__c.txt()`));
  step('save', await ev(`window.__c.click('#done-button')`));
  await sleep(6000);
  step('after', await ev(`window.__c.txt()`));
  out.ok = true;
  console.log(JSON.stringify(out));
  process.exit(0);
}
