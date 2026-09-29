import http from 'node:http';
import https from 'node:https';
import fs from 'node:fs';

const WS = globalThis.WebSocket;

// ---- CDP helpers ----
function getJson(path) {
  return new Promise((res, rej) => {
    http.get({ host: '127.0.0.1', port: 9222, path }, (r) => {
      let d = ''; r.setEncoding('utf8'); r.on('data', (c) => (d += c));
      r.on('end', () => { try { res(JSON.parse(d)); } catch (e) { rej(e); } });
    }).on('error', rej);
  });
}

function cdpClient(wsUrl) {
  return new Promise((resolve, rej) => {
    const ws = new WS(wsUrl);
    let id = 0; const pending = new Map();
    const listeners = {};
    ws.addEventListener('open', () => resolve({
      send(method, params) {
        return new Promise((res, re) => {
          const mid = ++id;
          pending.set(mid, { res, re });
          ws.send(JSON.stringify({ id: mid, method, params: params || {} }));
        });
      },
      on(event, cb) {
        (listeners[event] = listeners[event] || []).push(cb);
      },
      close() { try { ws.close(); } catch {} }
    }));
    ws.addEventListener('message', (m) => {
      const d = JSON.parse(m.data);
      if (d.id && pending.has(d.id)) {
        const p = pending.get(d.id); pending.delete(d.id);
        if (d.error) p.re(new Error(d.error.message)); else p.res(d.result);
      }
      if (d.method && listeners[d.method]) listeners[d.method].forEach((cb) => cb(d.params));
    });
    ws.addEventListener('error', rej);
  });
}

function httpGetFollow(url, depth = 4) {
  return new Promise((res, rej) => {
    const doReq = (u, d) => {
      const lib = u.startsWith('https') ? https : http;
      const req = lib.get(u, { headers: { 'User-Agent': 'Mozilla/5.0' }, followRedirect: false }, (r) => {
        if ((r.statusCode === 301 || r.statusCode === 302) && r.headers.location && d > 0) {
          r.resume();
          return doReq(new URL(r.headers.location, u).toString(), d - 1);
        }
        let body = ''; r.setEncoding('utf8'); r.on('data', (c) => (body += c));
        r.on('end', () => res(body));
      });
      req.on('error', rej);
      req.setTimeout(8000, () => req.destroy(new Error('timeout')));
    };
    doReq(url, depth);
  });
}

function withTimeout(p, ms, tag) {
  return Promise.race([p, new Promise((res) => setTimeout(() => res(['__TIMEOUT__' + tag]), ms))]);
}

// ---- unwrap google result url ----
function unwrap(href) {
  try {
    const u = new URL(href);
    if (u.hostname.includes('google.com')) {
      if (u.pathname === '/url') {
        const q = u.searchParams.get('q');
        if (q) return q;
      }
      if (u.pathname === '/goto') {
        const url = u.searchParams.get('url');
        if (url) return null; // handled by caller via httpFollow
      }
    }
  } catch {}
  return href;
}

// ---- classification ----
const AGG = new Set([
  'reddit.com','wpbeginner.com','hostadvice.com','websiteplanet.com','cybernews.com',
  'simplycodes.com','host.promo','hostdean.com','techjury.net','wethrift.com','valuecom.com',
  'worthepenny.com','costgoat.com','facebook.com','instagram.com','youtube.com','twitter.com',
  'pinterest.com','linkedin.com','quora.com','medium.com','github.com','gist.github.com',
  'studentbeans.com','wp-tweaks.com','webhostingcat.com','wpism.com','hosting.com',
  'startupworld.com','codeuk.net','couponfollow.com','retailmenot.com','slickdeals.net',
  'dealcatcher.com','dontpayfull.com','groupon.com'
]);

function hostOf(u) { try { return new URL(u).hostname.replace(/^www\./, ''); } catch { return ''; } }

function classify(urls, domains) {
  let own = 0, agg = 0; const ranked = [];
  for (const raw of urls) {
    let href = raw;
    if (href && href.includes('/goto?url=')) {
      const gu = new URL(href); const t = gu.searchParams.get('url');
      href = t || raw;
    } else {
      href = unwrap(raw);
    }
    if (!href || !href.startsWith('http')) continue;
    const h = hostOf(href);
    if (!h) continue;
    if (AGG.has(h)) { agg++; continue; }
    if (domains.some((d) => h === d || h.endsWith('.' + d))) { own++; ranked.push(h); continue; }
    ranked.push(h);
  }
  return { own, agg, ranked };
}

// CDN / noise hosts to skip entirely
const SKIP = new Set(['google.com','google.co.uk','google.co.kr','gstatic.com','youtube.com','accounts.google.com','support.google.com','policies.google.com','www.google.com']);

// ---- SERP scrape via real Chrome ----
async function scrapeSerp(browserWs, kw) {
  const target = await browserWs.send('Target.createTarget', { url: 'about:blank' });
  const tid = target.targetId;
  await new Promise((r) => setTimeout(r, 500));
  const list = await getJson('/json/list');
  const entry = list.find((t) => t.id === tid);
  const tab = await cdpClient(entry.webSocketDebuggerUrl);
  await tab.send('Page.enable');
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  const navTo = async (url) => {
    await tab.send('Page.navigate', { url });
    // wait for load
    for (let i = 0; i < 12; i++) {
      await sleep(700);
      try {
        const st = await tab.send('Runtime.evaluate', { expression: 'document.readyState', returnByValue: true });
        if (st.result && st.result.value === 'complete') break;
      } catch {}
    }
  };

  const readHtml = () => tab.send('Runtime.evaluate', { expression: 'document.documentElement.outerHTML', returnByValue: true }).then((r) => r.result.value || '');
  const titleLinks = () => tab.send('Runtime.evaluate', {
    expression: `(function(){var out=[];document.querySelectorAll('a h3').forEach(function(h){var a=h.closest('a');if(a&&a.href)out.push(a.href);});return out;})()`,
    returnByValue: true
  }).then((r) => r.result.value || []);

  const searchUrl = 'https://www.google.com/search?q=' + encodeURIComponent(kw) + '&gl=us&hl=en&num=10';
  await navTo('https://www.google.com/ncr');
  await navTo(searchUrl);

  // consent handling
  let html = await readHtml();
  if (/before you continue|consent/i.test(html)) {
    await tab.send('Runtime.evaluate', { expression: `(()=>{var f=document.querySelector('form[action*="consent"]');if(f){f.submit();return true;}var b=[...document.querySelectorAll('button')].find(x=>/accept|agree|consent/i.test(x.textContent));if(b){b.click();return true;}return false;})()` });
    await sleep(1500);
    await navTo(searchUrl);
    html = await readHtml();
  }

  const links = await titleLinks();
  // also fallback: any h3 links
  if (!links.length) {
    html = await readHtml();
    const m = [...html.matchAll(/<a[^>]+href="([^"]+)"[^>]*>\s*<h3/gi)];
    // not reliable; rely on in-page
  }
  await browserWs.send('Target.closeTarget', { targetId: tid });

  // unwrap /goto?url= via http follow
  const finalUrls = [];
  for (const l of links.slice(0, 10)) {
    if (l && l.includes('/goto?url=')) {
      try { const body = await httpGetFollow(l); const mm = body.match(/https?:\/\/[^\s"'<>]+/); if (mm) finalUrls.push(mm[0]); }
      catch { finalUrls.push(l); }
    } else {
      const u = unwrap(l);
      if (u) finalUrls.push(u);
    }
  }
  return finalUrls.filter((u) => !SKIP.has(hostOf(u)));
}

const BRANDS = [
  ['contabo', ['contabo.com'], 'contabo coupon code'],
  ['wpengine', ['wpengine.com'], 'wp engine coupon code'],
  ['ionos', ['ionos.com', '1and1.com'], 'ionos coupon code'],
  ['linode', ['linode.com'], 'linode coupon code'],
  ['kamatera', ['kamatera.com'], 'kamatera coupon code'],
  ['hostarmada', ['hostarmada.com'], 'hostarmada coupon code'],
  ['nexcess', ['nexcess.net'], 'nexcess coupon code'],
  ['stablehost', ['stablehost.com'], 'stablehost coupon code'],
  ['mdhosting', ['mdhosting.com', 'mdwebhosting.com'], 'mdhosting coupon code'],
  ['hawkhost', ['hawkhost.com'], 'hawkhost coupon code']
];

async function main() {
  const ver = await getJson('/json/version');
  const browser = await cdpClient(ver.webSocketDebuggerUrl);
  const results = [];
  for (const [slug, domains, kw] of BRANDS) {
    const hosts = await withTimeout(scrapeSerp(browser, kw), 75000, kw);
    if (Array.isArray(hosts) && hosts[0] && hosts[0].startsWith('__TIMEOUT__')) {
      console.log(`=== ${slug} (${kw}) ===\nTIMEOUT\n`);
      results.push({ slug, kw, skip: 'TIMEOUT', top: [] });
      continue;
    }
    const { own, agg, ranked } = classify(hosts, domains);
    const skip = own >= 3;
    console.log(`  [diag ${kw}] top=${hosts.length} own=${own} agg=${agg} skip=${skip}`);
    console.log(`=== ${slug} (${kw}) ===`);
    console.log('top10:', ranked.slice(0, 10).join(', '));
    console.log(`own=${own} agg=${agg} => ${skip ? 'SKIP' : 'PASS'}`);
    results.push({ slug, kw, skip, own, agg, top: ranked.slice(0, 10) });
  }
  const passed = results.filter((r) => !r.skip);
  const skipped = results.filter((r) => r.skip);
  console.log('\nPASSED:', passed.map((r) => r.slug).join(', ') || '(none)');
  console.log('SKIPPED:', skipped.map((r) => r.slug + (r.skip === 'TIMEOUT' ? '(timeout)' : '(own>=3)')).join(', ') || '(none)');
  fs.writeFileSync('_serp_gate4.json', JSON.stringify(results, null, 2));
  console.log('WROTE _serp_gate4.json');
}

main().catch((e) => { console.error('FATAL', e); process.exit(1); });
