const fs = require('fs');
const LOG = 'C:/wb_host_launch.log';
const m = (() => { try { return fs.readFileSync(LOG, 'utf8').match(/ws:\/\/127\.0\.0\.1:9222\/devtools\/browser\/[0-9a-f-]+/); } catch (e) { return null; } })();
if (!m) { console.log('NO_WS (nothing to close)'); process.exit(0); }
const ws = new WebSocket(m[0]);
ws.binaryType = 'nodebuffer';
const to = setTimeout(() => { console.log('TIMEOUT'); try { ws.close(); } catch (e) {} process.exit(0); }, 8000);
ws.onopen = () => {
  try { ws.send(JSON.stringify({ id: 1, method: 'Browser.close', params: {} })); } catch (e) {}
  setTimeout(() => { clearTimeout(to); try { ws.close(); } catch (e) {} console.log('CLOSED temp-profile Chrome on 9222'); process.exit(0); }, 1500);
};
ws.onerror = () => { console.log('WS_ERR (already gone)'); process.exit(0); };
