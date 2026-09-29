const fs = require('fs');
const LOG = 'C:/wb_real_launch.log';
const OUT = 'C:/wb_host_out.json';

const URLS = [
  'https://www.hostinger.com/coupons',
  'https://www.hostinger.com/promos',
  'https://www.hostinger.com/pricing',
  'https://www.hostinger.com/wordpress-hosting',
  'https://www.hostinger.com/terms-of-service',
  'https://www.hostinger.com/'
];

function getWs() {
  for (let i = 0; i < 40; i++) {
    try {
      const log = fs.readFileSync(LOG, 'utf8');
      const m = log.match(/ws:\/\/127\.0\.0\.1:9222\/devtools\/browser\/[0-9a-f-]+/);
      if (m) return m[0];
    } catch (e) {}
    const t = Date.now(); while (Date.now() - t < 1000) {}
  }
  return null;
}
function connect(url) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(url); ws.binaryType = 'nodebuffer';
    const pending = {}; let id = 0;
    const api = {
      send(m, p = {}, s = null) {
        return new Promise((res, rej) => {
          const mid = ++id; pending[mid] = { res, rej };
          const msg = { id: mid, method: m, params: p }; if (s) msg.sessionId = s;
          try { ws.send(JSON.stringify(msg)); } catch (e) { delete pending[mid]; return rej(e); }
          setTimeout(() => { if (pending[mid]) { delete pending[mid]; rej(new Error('cmd timeout ' + m)); } }, 30000);
        });
      },
      close() { try { ws.close(); } catch (e) {} }
    };
    ws.onopen = () => resolve(api);
    ws.onmessage = (ev) => { let msg; try { msg = JSON.parse(ev.data.toString()); } catch (e) { return; }
      if (msg.id && pending[msg.id]) { const { res, rej } = pending[msg.id]; delete pending[msg.id]; if (msg.error) rej(new Error(JSON.stringify(msg.error))); else res(msg.result); } };
    ws.onerror = (e) => reject(new Error('wserr ' + (e.message || '')));
    setTimeout(() => reject(new Error('connect timeout')), 12000);
  });
}
(async () => {
  const wsUrl = getWs();
  if (!wsUrl) { console.log('NO_WS'); process.exit(1); }
  const api = await connect(wsUrl);
  const ct = await api.send('Target.createTarget', { url: 'about:blank' });
  const targetId = ct.targetId;
  const at = await api.send('Target.attachToTarget', { targetId, flatten: true });
  const sid = at.sessionId;
  await api.send('Page.enable', {}, sid);
  await api.send('Runtime.enable', {}, sid);
  const PAGEINFO = `(function(){var d=document;var h1=(d.querySelector('h1')||{}).innerText||'';var mt=(d.querySelector('meta[name=description]')||{}).content||'';var body=d.body?d.body.innerText.replace(/\\s+/g,' ').trim():'';return {loc:location.href,title:d.title||'',h1:h1.slice(0,200),meta:mt.slice(0,300),body:body.slice(0,4000),bodyLen:body.length};})()`;
  function evalJs(expr){return api.send('Runtime.evaluate',{expression:expr,returnByValue:true,awaitPromise:true},sid).then(r=>(r&&r.result?r.result.value:null)).catch(()=>null);}
  async function waitLoad(ms){const t=Date.now();while(Date.now()-t<ms){const s=await evalJs('document.readyState');if(s==='complete')return true;await new Promise(r=>setTimeout(r,400));}return false;}
  async function navigate(url){try{await api.send('Page.navigate',{url},sid);}catch(e){return false;}return true;}
  const out=[];
  for(const u of URLS){
    await navigate(u);
    const ok=await waitLoad(12000);
    let info=null; if(ok) info=await evalJs(PAGEINFO);
    const finalLoc=info?info.loc:null;
    const offHost = finalLoc ? (()=>{try{return new URL(finalLoc).hostname.toLowerCase();}catch(e){return '';}})() : '';
    const isOfficial = offHost.endsWith('hostinger.com');
    const isErr = finalLoc && finalLoc.indexOf('chrome-error')===0;
    out.push({url:u, ok:!!ok&&!isErr, finalUrl:finalLoc, isOfficial, page:info});
    await new Promise(r=>setTimeout(r,2000));
  }
  try{await api.send('Target.closeTarget',{targetId});}catch(e){}
  fs.writeFileSync(OUT, JSON.stringify(out,null,2));
  console.log('DONE '+out.length+' pages -> '+OUT);
})().catch(e=>{console.error('FATAL',e&&e.message);process.exit(1);});
