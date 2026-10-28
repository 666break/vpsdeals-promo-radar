# 对标表 — keyword `vps price`（28 天锁定，2026-10-28 建立）

> 本文件是本轮唯一对标依据。@KEYWORD 与 @TOP3 28 天内不换。
> 所有"讲了什么/没讲什么"均来自 2026-10-28 当天实抓的 30 个页面正文（HTML 转纯文本后逐词检索），不是印象。

## 一、锁定项（LOCK）

| 项 | 值 | 取法 |
|---|---|---|
| @KEYWORD | `vps price` | 第 7 步定词，只此一个 |
| SERP 采样 | Google 美国 / `gl=us&hl=en&pws=0` / 2026-10-28 | 真实 Chrome（用户登录态）CDP 实抓 |
| TOP1 | `digitalocean.com` — "VPS Hosting Plans - Starting at $4/mo" | 自然结果第 1 位 |
| TOP2 | `us.ovhcloud.com` — "VPS - Your virtual private server in the cloud" | 自然结果第 2 位 |
| TOP3 | `vpspricetracker.com` — "VPS Price Tracker: Rank and Compare VPS Hardware..." | 自然结果第 3 位 |

同屏第 4 位是 Reddit 讨论帖（r/selfhosted，"Cheapest quality VPS?"），第 5 位起才是 namecheap / getdeploying / contabo / ionos / hostkey。
**这三家是本轮对手，理由只是它们现在排在这三个位置，不是因为它们"应该"排在这。**

## 二、每站前十篇：它们讲了什么

### digitalocean.com（10 页）

| 页面 | 主题 | 它讲了什么 | 它没有的 |
|---|---|---|---|
| /solutions/vps-hosting | VPS 卖点页 | 四档 Droplet（Basic / General Purpose / CPU-Optimized / Dedicated），$4/mo 起 | 月上限怎么算、按秒计费规则、税、退款 |
| /pricing | 全产品价目总表 | Compute/Storage/Networking 全系价格，提到预付（prepay） | 一台 VPS 的真实到手成本、税、汇率 |
| /products/droplets | Droplet 产品页 | 按秒计费、60 秒最低、Bundled 套餐有月上限 | 关机后是否仍计费、额外 IPv4 价格、快照单独计价 |
| /pricing/droplets | Droplet 价目表 | 每档 RAM/vCPU/SSD/流量，含 672 小时栏位 | 跨区价差、税、结算币种 |
| /pricing/calculator | 计算器 | 交互式估算（正文仅 407 词，靠 JS 渲染） | 任何可引用的静态数字 |
| /solutions/cheap-web-hosting | 便宜建站 | $4 起、共享与独享的差别 | VPS 与共享主机的成本边界 |
| /solutions/virtual-machines | VM 通用页 | 规格怎么挑 | 价格怎么推 |
| /products/cloudways | 托管 VPS | 托管平台的溢价在哪 | 自管 vs 托管差价量化 |
| /solutions/cpanel-hosting | cPanel 主机 | cPanel 捆绑方案 | cPanel 授权费单列多少 |
| /resources/articles/digitalocean-vs-linode | 对比文（3,516 词） | 规格与价格逐项对比、FAQ | 真实账单口径（税、汇率、超额） |

### us.ovhcloud.com（10 页）

| 页面 | 主题 | 它讲了什么 | 它没有的 |
|---|---|---|---|
| /vps/ | VPS 主卖点页（4,336 词） | VPS 2027 系列，VPS-1 标 $4.54/mo，含什么 | 月上限、小时计费、税 |
| /vps/cheap-vps/ | 低价 VPS | VPS-1 规格、egress 提及 | 价格推导；**且该页夹着整段法语正文（"Une gamme de VPS performants à petit prix"）** |
| /vps/os/vps-linux/ | Linux VPS | 发行版选择、可扩展性 | 任何价格 |
| /vps/os/vps-windows/ | Windows VPS | 许可已含在价里 | Windows 许可占多少、与 Linux 同规格差多少 |
| /vps/os/vps-ubuntu/ | Ubuntu VPS | 场景与卖点 | 任何价格 |
| /vps/vps-cloud/ | Cloud VPS | 弹性与网络 | 与经典 VPS 的价差 |
| /resources/blog/cloud-infrastructure-pricing-in-2026/ | 2026 云定价趋势（2,777 词） | 涨价驱动因素（硬件、能耗、AI 需求） | 具体到 VPS 的账单结构 |
| /bare-metal/prices/ | 裸金属全价目（39,368 词） | 全系裸金属价、setup fee、renewal | VPS 口径（这是独立服务器页） |
| /vps/vps-amd/ | AMD VPS | AMD vs Intel 的卖点 | 同规格的价差数字 |
| /resources/blog/vps-2020/ | 2020 年老文 | 历史产品线 | 现价 |

### vpspricetracker.com（10 页）

| 页面 | 主题 | 它讲了什么 | 它没有的 |
|---|---|---|---|
| / | 目录 + 比较器首页（1,576 词） | 按 RAM / 核心数筛"最便宜" | 计费口径、税、超额 |
| /provider/SolidVPS | 单商统计 | 该公司最便宜 VPS、最大存储、最大带宽、最大 RAM | 账单细节 |
| /provider/VPS_Panda | 单商统计 | 同上 | 同上 |
| /provider/SolidVPS/server | 单商服务器统计 | 同上 + 独服 | 同上 |
| /blog/35/Cheap_storage_VPS_server_list | 便宜大存储 VPS 清单（486 词） | 列表 | 正文几乎只有表 |
| /blog/24/Cheapest_VPS_with_4GB_RAM | 4GB 最便宜（521 词） | 列表 | 正文几乎只有表 |
| /blog/28/The_Ultimate_VPS_Directory... | 目录说明（539 词） | 工具怎么用 | 任何价格分析 |
| /blog/25/Cheap_Windows_VPS_List_for_RDP | Windows/RDP 清单（829 词） | 分评估版/授权版/Windows 11 | 许可成本怎么进价 |
| /blog/38/Market_Analysis_of_VPS_Hosting_Prices | 市场分析（738 词） | 按 RAM 档位列最便宜 | 分析极浅，标题大于内容 |
| /blog/all-articles | 文章索引 | 索引 | — |

**观察（推断）**：TOP3 里两家的价格页是"卖自己"，第三家是"列别人"，没有一家在解释"这个价格是怎么算出来的"。这是本轮唯一可持续的切入口。

## 三、30 页正文议题覆盖统计（实测，2026-10-28）

对 30 个页面 HTML 去标签后的纯文本做正则检索，`n/30` = 命中页数。

| 议题 | 命中 | 命中页 |
|---|---|---|
| `672`（月上限小时数） | **2/30** | DO /products/droplets、DO /pricing/droplets |
| `hourly`（小时计费） | **4/30** | DO 4 页（droplets、pricing/droplets、cloudways、vs-linode）；OVH 0、vpspricetracker 0 |
| `monthly cap` | 2/30 | DO 同两页 |
| `egress` | 5/30 | DO /pricing、DO vs-linode、OVH cheap-vps、OVH vps-windows、OVH 定价趋势文 |
| `overage` | 3/30 | DO /pricing、DO cpanel、DO vs-linode |
| `bandwidth overage` | **0/30** | — |
| `per GB` | **0/30** | — |
| `per vCPU` | 2/30 | DO 两页 |
| `per core` | 1/30 | — |
| `VAT` | **0/30** | — |
| `sales tax` | **0/30** | — |
| `EUR` / `USD`（币种代码） | **0/30** | — |
| `exchange rate`（汇率） | **0/30** | — |
| `renewal` | **1/30** | OVH /bare-metal/prices（不是 VPS 页） |
| `setup fee` | **1/30** | OVH /bare-metal/prices（不是 VPS 页） |
| `refund` | 2/30 | — |
| `downgrade` | 1/30 | — |
| `prorat*`（按比例） | **0/30** | — |
| `stopped`（关机） | **0/30** | — |
| `powered off` | **0/30** | — |
| `money-back` | **0/30** | — |
| `coupon` | **0/30** | — |
| `promo` | 3/30 | DO droplets、DO pricing/droplets、OVH bare-metal |
| `IPv4` | 14/30 | 但 vpspricetracker 的 10 次全是"是否支持 IPv4"的标记，不是价格 |
| `snapshot` | 11/30 | 全部是"有快照功能"，没有一处写快照怎么计费 |
| `annual` | 10/30 | — |
| `hidden` | 2/30 | DO vs-linode、OVH vps-cloud |

**结论（实测支撑，不是判断）**：TOP3 的 30 个页面里，**税、汇率、每 GB/每 vCPU 单价、按比例退款、关机计费、退款期、优惠码** 这 7 类议题命中率是 0。这就是缺口所在。

## 四、缺口 → 明天写哪篇

缺口队列在 `gaps-vps-price.json`，32 条，按"缺口大的先写"排。
每天从队列取第一条 `done:false`，写一篇，写完标 `done:true` 并记 `published` 日期。
**同一条缺口只写一篇，写过的 slug 永不复用。**

## 五、取料纪律

- 只从官方价格页 / 官方文档 / 官方 FAQ 取数，抓到哪个记哪个，抓不到就写"该页当天无法抓取"，**不填**。
- 每篇至少 30% 的内容必须是这三家没有的东西，来源写清是哪个官方页、哪天抓的。
- 这三家的句子一句都不许搬。学结构、学角度，不学措辞。
