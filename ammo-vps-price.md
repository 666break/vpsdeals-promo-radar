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

## 2026-10-28（第二班，发完 `vps-price-stopped-instance` 后补）

> 这一班没跑 Google 实搜，所以不写"SERP 看到了什么"。下面每条都注明是在哪个官方页面上实际看到的。

### 明天（`vps-price-sales-tax`）可直接用的官方线索

| 线索 | 在哪看到的（2026-10-28 实抓） | 能怎么用 |
|---|---|---|
| DigitalOcean 文档站 Billing 栏目下有一篇独立的 **Taxes by Country** 页 | `docs.digitalocean.com/products/billing/` 左侧目录（正文没进，只看到标题） | 明天第一件事就是抓这篇，逐国列税率；这是"税"这个缺口的正门 |
| DO 的 Late Payments 页写明：每月 1 号出账时 "applying signup credit and **taxes when applicable**" | `docs.digitalocean.com/products/billing/late-payments/` | 证明税是出账时加、不是标价里含的；一句话坐实"标价不含税" |
| Hetzner 的 Cloud billing FAQ 里有一节 **Can I change the currency in the invoice?**，并写明项目按"owner 配置的币种"计费 | `docs.hetzner.com/cloud/billing/faq/` | 这篇写税，但币种这条留给 `vps-price-currency-and-fx`，明天顺手记下原文 |
| OVHcloud 的 commitment 指南：commitment "billed **annually and up front only**"，提前取消要"pay the remainder" | `docs.ovhcloud.com/.../manage-commitments.md` | 留给 `vps-price-annual-prepay` 与 `vps-price-downgrade-credit`，是"预付=现金流出前置"的硬证据 |

### 长尾问句（自拟，未经 SERP 验证，明天用前先实搜确认）

- "is digitalocean price including tax" / "ovhcloud vps price vat included"
- "hetzner cloud price excl vat us customer"
- 说明：这三条是我按缺口写的问法，**没有**跑 SERP，不许当成"有人这么搜"的依据。

### 结构线索

- OVHcloud `/vps/` 页上有一句给老客户的话："To purchase the same configuration you have today, you may need to choose a different model. There is a new VPS-1 entry-level model, and the configurations for the other models have shifted." —— 这是官方自己承认产品线改版会让老配置对不上新 SKU，写 `vps-price-renewal-vs-first-term` 时的好料，先记着。
- DO 的 v5 与 bundled 两套计费规则写在同一个文档页里、相邻两节，但**月上限只有 bundled 有**。这种"同页两套规则"的结构可以直接复用到"税"那篇（标价页 vs 出账页两套口径）。

## 2026-10-29（第三班，发 `vps-price-currency-and-fx`）

> 本班不跑 SERP。下面每一条都写清在哪个页面的哪个位置看到的，抓取日期 2026-10-29，全部 HTTP 200。

### 今天这篇用掉的料（来自 2026-10-28 清单的那一条）

| 用料 | 出处 | 怎么用的 |
|---|---|---|
| 「Hetzner 的 Cloud billing FAQ 里有一节 Can I change the currency in the invoice?，并写明项目按 owner 配置的币种计费」 | 2026-10-28 清单「明天（`vps-price-sales-tax`）可直接用的官方线索」第 3 行，本次回原页核实 | 核实后原文是 "It is not possible to change the currency after an account has been created."，比 10-28 记的更强：不是"按 owner 配置"，而是**建号后不可改**。已写进正文并逐字引用 |

### 今天新抓到的、可复用的料

| 线索 | 在哪看到的 | 能怎么用 |
|---|---|---|
| OVHcloud 同一台 VPS-1（2 vCore / 4 GB / 40 GB NVMe）在四个区域商店的价：US $4.54、UK £3.31 ex./£3.97 incl.、DE 4,53 € inkl. MwSt.、FR 3,81 € HT/4,57 € TTC | us.ovhcloud.com/vps/、ovhcloud.com/en-gb/vps/、ovhcloud.com/de/vps/、ovhcloud.com/fr/vps/ 四页同日抓 | 已用于今天这篇。这组四商店对照可以反复用作"同规格跨店比价"的基准 |
| 美国站可见文本里 tax / VAT / excl / incl **各 0 次**，但 `tax-excluded-price` 这个 class 出现 6 次 | us.ovhcloud.com/vps/ 去标签后正则计数 | 「美国站唯一的税披露是一个 CSS 类名」—— 这是结构级证据，比文字引用更硬 |
| ECB 每日参考汇率文件 `ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml`（免费、无 key、XML，日期在 `<Cube time=...>`） | 本次实抓，2026-10-29 抓到的是 2026-10-28 那期 | 以后任何"跨币种比价"都该用这个做分母，可溯源到官方，不用商业汇率站 |
| DigitalOcean 税页 FAQ：「USD is the only currency we accept for payments, so all invoices are in USD.」 | docs.digitalocean.com/platform/billing/taxes/ | 已用。注意这句在**税**页而不是计费页，别人不容易找到 |
| Hetzner 跨币种搬服务器会触发重新定价：「the server will be switched to the current pricing scheme upon completion of the transfer」 | docs.hetzner.com/cloud/billing/faq/ | 已用。这条对"老价格客户别乱搬项目"是硬提醒 |
| Visa 汇率计算器页 HTTP 520、Mastercard 换汇页 HTTP 403，两者当天都抓不到 | 本次实抓 | 按纪律整段排除。以后要写"卡组织怎么定汇率"必须先解决抓取，不能凭常识补 |

### 明天（`vps-price-extra-ipv4`）的料，今晚就位

| 线索 | 在哪看到的（2026-10-29 实抓，逐字） | 明天怎么用 |
|---|---|---|
| Hetzner 把 IP 和服务器分开计费，且**未绑定的 IP 也照收** | docs.hetzner.com/cloud/billing/faq/：「We bill Primary IPs (IPv4, IPv6) and cloud servers separately, and we list both resources separately in invoices. We will bill you for all Primary IPs that have finished the creation process, including Primary IPs that are not assigned to any cloud server. If you want to stop paying for a Primary IP, you need to delete it.」另：「Primary IPv6s are free and are not listed in the invoice in general.」 | 明天这篇的核心对照之一：IPv6 免费、IPv4 按个收、没绑也收 |
| DigitalOcean 的 IPv4 计费按套餐类型分裂：Bundled 含、v5 另收 | digitalocean.com/pricing/droplets 的 FAQ「Do Droplets come with a dedicated IP address?」：「For Bundled Plans, a public IPv4 is included at no extra cost. Public IPv4 addresses for Droplets with v5 configurations are billed separately from the v5 configur…」（句子被页面截断，明天要抓完整句和单价） | 明天第一件事：抓 DO 的 networking / additional-IP 价目页拿单价，再抓 OVH 的额外 IP 价 |
| OVHcloud 的 VPS 页提到数据中以外的机房「cannot be modified or upgraded after delivery」 | us.ovhcloud.com/vps/ 底部注 | 与 IP 关系不大，先存着，留给"机房选择影响后续变更"的缺口 |
