# 日更台账 — `vps price` 周期（第 1 轮，2026-10-28 起，28 天）

> 一行一天，**只追加不覆盖**。日期 | slug | 标题 | 线上地址 | 用了哪条缺口 | 图做了什么 | 明天写哪条

| 日期 | slug | 标题 | 线上地址 | 缺口 | 图 | 明天写哪条 |
|---|---|---|---|---|---|---|
| 2026-10-28 | vps-price | VPS Price Explained: Hourly Rates, Monthly Caps and the Cost per GB | https://serverbudget.com/vps-price | 开局页（672 小时月上限 / 每 GiB 与每 vCPU 阶梯 / 5.3 倍同规格价差） | 本轮补：4GB-2vCPU 三价对比柱状图（内联 SVG，2026-10-28 官方价） | vps-price-stopped-instance |
| 2026-10-28 | vps-price-stopped-instance | Does a Stopped VPS Still Cost Money? Billing by State | https://serverbudget.com/vps-price-stopped-instance | 缺口 #1 `vps-price-stopped-instance`（关机 / 暂停 / 销毁三态的计费差） | 累计计费小时阶梯图（168h 用 / 672h 上限两条线，内联 SVG，DO 官方 672 小时规则） | vps-price-sales-tax |

## 说明

- 2026-10-28 这篇是在本班次开始前由上一个会话发布并已进 sitemap 的（commit 431409f）。本班次没有重写，只做了两件事：① 补上内联 SVG 图（原页 0 张图）；② 建立本轮对标表与缺口队列。
- 因此本周期第 1 天的"发一篇"由该页承接；日更自动任务从 2026-10-29 07:30 起每天发新页。
- 缺口队列见 `gaps-vps-price.json`（32 条），对标表见 `bench-vps-price.md`。
- 2026-10-28 19:20 追加：日更自动任务实际在当晚 19:00 就跑了第一班，发了 `vps-price-stopped-instance`（缺口 #1，已标 done）。所以 2026-10-29 那班从队列第 2 条 `vps-price-sales-tax` 起写。
- 2026-10-28 19:50 追加：`/vps-price` 与 `/vps-price-stopped-instance` 的 672 小时口径对齐。官方原文（digitalocean.com/pricing/droplets 的 FAQ，2026-10-28 19:38 抓）：「Bundled Plans have a monthly cap, so you'll never pay more than the flat monthly price for that plan. v5 Droplets are billed on actual hours used each month and are not capped at 672 hours.」→ 672 只管 Bundled Plan（Basic / CPU-Optimized / Memory-Optimized 属这一类），v5 没有这个上限。两页各补限定，数字一个没删。
- 2026-10-28 20:55 追加（第二轮核对，官方页重抓于 20:37-20:39）：三处官方原文坐实口径 —— ①docs 定价页「Bundled-plan CPU Droplets are billed per second with a minimum charge of 60 seconds or $0.01, whichever is higher. Usage is capped at 672 hours (28 days) per month.」②同页「Unlike bundled plans, v5 Droplets do not have a monthly usage cap.」③choosing-a-plan 页「There are five bundled Droplet plans: one shared CPU plan and four dedicated CPU plans.」→ 672 是**五类 bundled plan** 的月上限（Basic + 四类专用 CPU），不是全 Droplet 规则；v5 按实际小时计费、无上限。两页各改一句：`/vps-price` 的 H2 加限定并把「672 只适用于 Bundled-plan CPU Droplets」写进正文；`/vps-price-stopped-instance` 在 v5 那段补「五类 bundled plan」的出处，并把 Basic / CPU-Optimized / Memory-Optimized 明确成「例子」而非全集。数字一个没删。
- 2026-10-28 21:55 追加（断点续做：百分比逐行重算 + 四处改动）：按 `digitalocean.com/pricing/droplets`（2026-10-28 21:2x 抓，HTTP 200）**渲染表格里同时给出 $/hr 与 $/mo 的 21 行**逐行算 —— `小时数 = 月价 ÷ 时价` 落在 **671.89–672.27**；`时价 × 730 ÷ 月价 − 1` 落在 **+8.59% ～ +8.65%**。原页 `7.9–8.6%` 的下限对不上任何一行（该句已由 964bb9f 换成 8.59–8.65%）。本轮补剩下三处残留 + 一处口径：① Key Takeaways `roughly 8%` → `roughly 8.6%`；② FAQ 正文 `about 8 percent` → `about 8.6 percent`；③ 同句的 FAQPage JSON-LD 同步（保持结构化数据与可见正文一致）；④ `/vps-price-stopped-instance` v5 那格 `None published` → `No cap — billed on actual hours`，依据 `docs.digitalocean.com/products/droplets/details/pricing/`「Unlike bundled plans, v5 Droplets do not have a monthly usage cap.」。提交 `635350b`（rebase 后哈希，原 `ba33331`），run `40700646354` 绿；两页 200、`cf-cache-status: DYNAMIC`、无 `x-robots-tag`；sitemap 线上 75 条，两页都在。数字一个没删。
