# 弹药清单 — `vps price`（T3 每天往里填）

> 规则：只记"确实看到了"的东西，写清在哪看到的。想不出来就写"空"，不编。
> 明天写哪篇从这份清单 + `gaps-vps-price.json` 里拿，不当天早上临时想。

## 2026-10-28

### 长尾问句（来自 Google 实搜，`gl=us&hl=en&pws=0`，2026-10-28）

| 问句 | 实搜看到的自然结果 | 可用的点 |
|---|---|---|
| does a stopped vps still cost money | r/hetzner "Pricing for stopped vps"（10+ 评论）、help.skysilk.com "Am I charged even if my VPS is powered off?"、serverpoint.com "VPS billing explained"、readyserver.sg "Why Powering Off Your VPS Doesn't Stop Billing"、learn.microsoft.com "Stopped VM charged me or not?"、repost.aws "Will costs continue when I shutdown my VPS?" | 这题有真实讨论、且 TOP3 的 30 页里 `stopped` / `powered off` 命中 0 —— 对应缺口 `vps-price-stopped-instance`。注意：站外已有小厂写过，我们要赢只能靠"逐家官方条款对照表"，不能靠泛泛而谈 |
| vps price per month vs hourly | layeronecloud.com "Hourly vs Monthly VPS Billing Explained"、colossuscloud.com "VPS Billing (Hourly with Monthly Cap)"、serverpoint.com "VPS billing explained"、instantnode.eu "Hourly VPS Billing Explained" | 小时 vs 月付这题在中小主机商里是常见内容，但 TOP3 里只有 DigitalOcean 讲（4/30 页）。对应缺口 `vps-price-minimum-billing-unit` 与 `vps-price-annual-prepay` |

### 结构线索（来自本轮对标表 `bench-vps-price.md`）

- OVHcloud 的 `/vps/cheap-vps/` 页面里夹着整段法语正文（"Une gamme de VPS performants à petit prix" / "Pourquoi choisir un hébergement VPS low cost ?"）。这是他们本地化没清干净的痕迹 —— 我们不做多语言，不做这条，只记下来当"对手不是无懈可击"的观察。
- vpspricetracker.com 的 10 篇博客正文普遍只有 480–830 词，且 H2 就是文章标题本身，等于没有小标题结构。标题大于内容。
- DigitalOcean 的 `/pricing/calculator` 正文只有 407 词，全靠 JS 渲染 —— 这类页面对"想复制一段数字"的读者没有用。

### 还没拿到、需要下次补的

- 三家 VPS 的实际结账页加价项（税、开通费）—— 需要登录态走到结账页才能看到，暂未取。
- 关机计费的逐家官方条款原文 —— 下次写 `vps-price-stopped-instance` 时逐家抓官方 billing FAQ。
