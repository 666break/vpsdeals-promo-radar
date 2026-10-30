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

## 2026-10-30（第四班，发 `vps-price-extra-ipv4`）

> 本班不跑 SERP。下面每一条都写清在哪个页面的哪个位置看到的，抓取日期 2026-10-30，全部 HTTP 200。

### 今天这篇用掉的料（来自 2026-10-29 清单的三条）

| 用料 | 出处 | 怎么用的 |
|---|---|---|
| Hetzner「Primary IP 与服务器分开计费、未绑定也照收、IPv6 免费」 | 2026-10-29 清单第 1 行，本次回原页核实 | 原文核实无误，另抓到单价页 `docs.hetzner.com/cloud/servers/primary-ips/overview/`：€0.50 / $0.60 每月（不含税）、€0.0008 / $0.0010 每小时，每台服务器上限 1 个 IPv4 + 1 个 IPv6 |
| DO 的 IPv4 计费按套餐类型分裂（Bundled 含、v5 另收） | 2026-10-29 清单第 2 行，本次抓到完整句 | 完整句在 `digitalocean.com/pricing/droplets` 的 FAQ「Do Droplets come with a dedicated IP address?」：Bundled 含、v5 单独列项、入门价 $0.00/hour，另有 Private Droplet 无公网 IP 故无该行 |
| DO 的 networking / additional-IP 价目 | 2026-10-29 清单第 2 行要求的动作 | 关键页不是 networking 价目（`digitalocean.com/pricing/networking` 已 404），而是 `docs.digitalocean.com/products/networking/reserved-ips/details/pricing/`：已绑定 $0、未绑定 $5.00/月（$0.01/小时）、未满 $1 不计费 |

### 今天新抓到的、可复用的料

| 线索 | 在哪看到的 | 能怎么用 |
|---|---|---|
| OVH VPS 的 Additional IP 单价 $2.40/IP/月，上限 16 个 | `us.ovhcloud.com/vps/options/`（价目块）与 `us.ovhcloud.com/network/additional-ip/`（「Additional IPv4 address & blocks $2.40 /IP/month」） | 已用。16 × $2.40 = $38.40，是 VPS-1（$4.54）的 8.46 倍 —— 以后写「多站点/多租户成本」可复用 |
| OVH 明确写：VPS 不支持 IP 段（只能 /32），IPv6 /56 免费但只能走 vRack、不能用于 VPS | `us.ovhcloud.com/network/additional-ip/` 的 FAQ 与限额段 | 已用。「免费的东西用不上」是最硬的一类独家料，可复用到 IPv6-only 那条缺口 |
| OVH 对未绑定 Additional IP 的回收条款：连续 30 天未绑定可回收 | `us.ovhcloud.com/network/additional-ip/` FAQ「What is the maximum period of non-assignation of my Additional IP?」 | 已用。三家唯一一条「不用就收回」的明文 |
| OVH Public Cloud 的 Public IP IPv4 (/32)：$0.00319/小时、约 $2.3287/月（不含税），且「including when it is not attached to an instance」 | `us.ovhcloud.com/public-cloud/prices/` | 已用（并明确标注是 Public Cloud 不是 VPS）。以后写「IP 是不是资产」可当反例：OVH 自己两个产品线对同一件事的定价差 3% |
| Hetzner 服务器计费原文：「until you delete them, independent of their state… we allocate full resources to servers, regardless of their power state」 | `docs.hetzner.com/cloud/billing/faq/` | 已用。这句是「关机不省钱」的通用引证，任何涉及停机的缺口都能引 |

### 明天（`vps-price-snapshot-billing`）的料，今晚就位

| 线索 | 在哪看到的（2026-10-30 实抓，逐字） | 明天怎么用 |
|---|---|---|
| Hetzner 快照按 GB·月计费，且只算压缩后实际占用 | `docs.hetzner.com/cloud/billing/faq/`「How do you bill for Snapshots and Backups?」：「We will bill you for Snapshots per gigabyte per month. If a Snapshot only exists for a fraction of a month, then we will only bill for this fraction. We will only bill you for the space the compressed Snapshot uses in our storage system. So if you create a Snapshot of a disk of 40GB, we will bill you for 40GB or less — depending on how the data on your disk compresses.」 | 明天的主对照之一：同一块盘，快照账单取决于压缩率，不取决于盘大小 |
| Hetzner 备份是「服务器价格的 20%」固定月费，含 7 个槽位 | 同上页：「we will bill you for Backups with a monthly flat price, which is 20% of the price of the server… For this price, you will get a total of 7 Backup slots.」并给了 €3.29 → €0.658/月 的算例 | 备份 vs 快照两条计价逻辑（百分比 vs 每 GB）正好做一张对照表 |
| Hetzner 建议「长期关机不如拍快照再删机」 | 同上页 server 计费段 | 与今天的关机计费串起来：快照是官方推荐的停机替代品，那它的单价就直接决定「停机省钱」成不成立 |

### 还没拿到、需要下次补的

- DO 的快照单价（`docs.digitalocean.com` 的 snapshots 定价页本次未抓），明天第一件事。
- OVH VPS 的 snapshot 选项价只在 `/vps/` 上看到「Starting at $0.40/month」，是否按容量分档未确认，明天回原页看选项表。

## 2026-10-31 追加（明天 = 缺口 #6 `vps-price-bandwidth-overage`：超流量那一个月账单上发生什么）

| 线索 | 在哪看到的（2026-10-31 实抓，逐字） | 明天怎么用 |
|---|---|---|
| Hetzner 超额按 100MB 块计、不足一块向上取整 | `docs.hetzner.com/cloud/billing/faq/`「How do you bill for traffic?」：「If you exceed the traffic included in your package, we will bill you for the over-usage in blocks of 100MB. If you only consume a fraction of 100MB, we will round up to the next full 100MB.」并给算例：含 20TB，用了 20.00008TB，计 0.0001TB（=100MB）超额 | 主对照：计费颗粒度（100MB 向上取整）本身就是独家料，TOP3 无一页写颗粒度 |
| Hetzner 超额告警只是通知、不停机 | 同上页：「We will notify you, the project owner, if the traffic usage exceeds 75% of the included free traffic, and again if you reach 100%… they do not cap or stop it… Any traffic used beyond the included amount is billed as usual, even if a notification reaches you late or does not arrive at all.」 | 「75% / 100% 两次告警但都不封顶」是可引用的原文 |
| Hetzner EU 机型含 20TB，超额单价写在机型卡下方 | `hetzner.com/cloud/cost-optimized/` CX23 段：「Traffic inclusive 20 TB」「For each additional TB at EU-Central locations we charge € 1.00 per hour, excl. VAT.」 | **这句措辞要先复核**：写的是 per TB **per hour**，与「per month」不符，可能是页面文案错误；明天回原页确认后再决定能不能用，不许照抄当结论 |
| DO 每档 Basic 的 included transfer 是 500GiB–6,000GiB 递增 | `digitalocean.com/pricing/droplets` Basic 表 Transfer 列（2026-10-31 抓）：512MiB=500GiB、1GiB=1,000GiB、2GiB=2,000GiB、2GiB/2vCPU=3,000GiB、4GiB=4,000GiB、8GiB=5,000GiB、16GiB=6,000GiB | 已核实的一半；**超额单价本次没抓到**，明天去 `docs.digitalocean.com` 的 bandwidth/transfer 定价页补 |
| OVH VPS 页的流量口径本次未取 | 今天只读了 `/vps/options/`，没读 `/vps/` 的流量段 | 明天第一件事：`us.ovhcloud.com/vps/` 抓 unmetered / fair-use 的原文，抓不到就在正文写明「该页当天未取到」 |
