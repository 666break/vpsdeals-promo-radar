// cdp.mjs — minimal Chrome DevTools Protocol driver (no deps; Node 22 global WebSocket).
// Usage:
//   node scripts/cdp.mjs --url "https://..." --wait 6000 --expr "document.title" [--shot out.png]
// Requires a Chrome already listening on --remote-debugging-port=9222.
import fs from 'node:fs';

const argv = process.argv.slice(2);
const arg = (k, d = null) => { const i = argv.indexOf(k); return i > -1 ? argv[i + 1] : d; };

const port = arg('--port', '9222');
const url = arg('--url', null);
const wait = parseInt(arg('--wait', '5000'), 10);
const expr = arg('--expr', 'document.title');
const shot = arg('--shot', null);

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function targets() {
  for (let i = 0; i < 40; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${port}/json/list`);
      const j = await r.json();
      const pages = j.filter(t => t.type === 'page' && t.webSocketDebuggerUrl);
      if (pages.length) return pages;
    } catch { /* not up yet */ }
    await sleep(500);
  }
  throw new Error('no CDP page target on port ' + port);
}

class Conn {
  constructor(ws) { this.ws = ws; this.id = 0; this.pending = new Map(); this.events = [];
    ws.addEventListener('message', (ev) => {
      const m = JSON.parse(ev.data);
      if (m.id && this.pending.has(m.id)) { const { res, rej } = this.pending.get(m.id); this.pending.delete(m.id); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); }
      else if (m.method) this.events.push(m);
    });
  }
  send(method, params = {}) {
    const id = ++this.id;
    return new Promise((res, rej) => { this.pending.set(id, { res, rej }); this.ws.send(JSON.stringify({ id, method, params })); });
  }
  close() { try { this.ws.close(); } catch {} }
}

const pages = await targets();
const target = pages.find(p => !p.url.startsWith('devtools://')) || pages[0];
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((res, rej) => { ws.addEventListener('open', res, { once: true }); ws.addEventListener('error', rej, { once: true }); });
const c = new Conn(ws);

await c.send('Page.enable');
await c.send('Runtime.enable');
try { await c.send('Page.bringToFront'); } catch { /* non-fatal */ }
if (url) {
  await c.send('Page.navigate', { url });
  await sleep(wait);
} else {
  await sleep(300);
}

let value;
try {
  const r = await c.send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
  value = r.result && 'value' in r.result ? r.result.value : r.result;
} catch (e) { value = 'EVAL_ERROR: ' + e.message; }
console.log(typeof value === 'string' ? value : JSON.stringify(value, null, 2));

if (shot) {
  const r = await c.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
  fs.writeFileSync(shot, Buffer.from(r.data, 'base64'));
  console.error('shot saved: ' + shot);
}
c.close();
process.exit(0);
