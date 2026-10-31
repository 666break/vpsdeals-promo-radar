// ::ILANG [TYPE:component][COMPONENT:rakuten_watch][LANG:js]
// RESPONSIBILITY: 只做一件事 —— 存/读 Gmail 审批来信的比对基线（lastEmailInternalDate + lastEmailIds）。
//                 真正的 Gmail 读取由任务里的 Gmail 工具完成，脚本不碰网络、不碰浏览器。
// BOUNDARY: 不读写任何后台接口；不改 status/advertiser（历史基线原样保留）。

const fs = require("fs");
const path = require("path");

const DIR = "C:/Users/Administrator/vpsdeals-promo-radar";
const STATE = path.join(DIR, "_rakuten_watch_state.json");

const args = process.argv.slice(2);
const mode = args[0] || "--show";

function arg(name, def) {
  const i = args.indexOf("--" + name);
  return i >= 0 && args[i + 1] !== undefined ? args[i + 1] : def;
}

function readState() {
  try { return JSON.parse(fs.readFileSync(STATE, "utf8")); } catch (e) { return {}; }
}

if (mode === "--commit") {
  const st = readState();
  const iso = arg("email-iso", null);
  if (iso) st.lastEmailInternalDate = iso;
  const ids = arg("email-ids", null);
  if (ids) st.lastEmailIds = ids.split(",").map(s => s.trim()).filter(Boolean);
  st.lastCommitAt = new Date().toISOString();
  fs.writeFileSync(STATE, JSON.stringify(st, null, 2), "utf8");
  console.log(JSON.stringify({ committed: true, state: st }, null, 2));
} else {
  const st = readState();
  console.log(JSON.stringify({
    stateFile: STATE,
    baselineEmailInternalDate: st.lastEmailInternalDate || null,
    baselineEmailIds: st.lastEmailIds || [],
    preservedStatus: st.status === undefined ? null : st.status,
    preservedAdvertiser: st.advertiser === undefined ? null : st.advertiser,
    lastCommitAt: st.lastCommitAt || null
  }, null, 2));
}
