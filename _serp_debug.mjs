import http from 'node:http';
const WS = globalThis.WebSocket;

function getJson(path){return new Promise((res,rej)=>{http.get({host:'127.0.0.1',port:9222,path},r=>{let d='';r.setEncoding('utf8');r.on('data',c=>d+=c);r.on('end',()=>{try{res(JSON.parse(d));}catch(e){rej(e);}});}).on('error',rej);});}
function cdpClient(wsUrl){return new Promise((resolve,rej)=>{const ws=new WS(wsUrl);let id=0;const pending=new Map();const L={};ws.addEventListener('open',()=>resolve({send(m,p){return new Promise((res,re)=>{const mid=++id;pending.set(mid,{res,re});ws.send(JSON.stringify({id:mid,method:m,params:p||{}}));});},on(ev,cb){(L[ev]=L[ev]||[]).push(cb);},close(){try{ws.close();}catch{}}}));ws.addEventListener('message',m=>{const d=JSON.parse(m.data);if(d.id&&pending.has(d.id)){const p=pending.get(d.id);pending.delete(d.id);if(d.error)p.re(new Error(d.error.message));else p.res(d.result);}if(d.method&&L[d.method])L[d.method].forEach(cb=>cb(d.params));});ws.addEventListener('error',rej);});}

async function main(){
  const ver=await getJson('/json/version');
  const browser=await cdpClient(ver.webSocketDebuggerUrl);
  const t=await browser.send('Target.createTarget',{url:'about:blank'});
  const tid=t.targetId;
  await new Promise(r=>setTimeout(r,500));
  const list=await getJson('/json/list');
  const entry=list.find(x=>x.id===tid);
  const tab=await cdpClient(entry.webSocketDebuggerUrl);
  await tab.send('Page.enable');
  const sleep=ms=>new Promise(r=>setTimeout(r,ms));
  const nav=async u=>{await tab.send('Page.navigate',{url:u});for(let i=0;i<15;i++){await sleep(700);try{const s=await tab.send('Runtime.evaluate',{expression:'document.readyState',returnByValue:true});if(s.result&&s.result.value==='complete')break;}catch{}}};
  const ev=expr=>tab.send('Runtime.evaluate',{expression:expr,returnByValue:true}).then(r=>r.result&&r.result.value);
  const kw='contabo coupon code';
  await nav('https://www.google.com/search?q='+encodeURIComponent(kw)+'&gl=us&hl=en&num=10');
  const info=await ev(`(function(){
    var body=document.body?document.body.innerText:'';
    var title=document.title;
    var h3as=[...document.querySelectorAll('a h3')].map(a=>a.href);
    var ext=[...document.querySelectorAll('a')].map(a=>a.href).filter(h=>h && !/google\\.com|gstatic|cloudflare|ogp\\.me|googleapis|youtube/.test(h)).slice(0,15);
    return JSON.stringify({
      title:title,
      bodyLen:body.length,
      hasConsent:/before you continue|consent\\.google|unusual traffic|verify you are human/i.test(title+' '+body),
      consentForm: !!document.querySelector('form[action*="consent"]'),
      h3aCount:h3as.length,
      h3aSample:h3as.slice(0,8),
      extSample:ext
    });
  })()`);
  console.log(info);
  await browser.send('Target.closeTarget',{targetId:tid});
}
main().catch(e=>{console.error('FATAL',e);process.exit(1);});
