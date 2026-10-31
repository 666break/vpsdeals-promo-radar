# kill_price_derived_claims — 清单（两页）

执行日：2026-10-16（本机 GMT+8）
范围：`live-site/cheap-vps-hosting.html`（@PAGE1）、`live-site/cheap-vps-for-beginners.html`（@PAGE2）
判据：凡是靠价格比出来的、或自己算出来的说法，一律不留；不补任何自己算的新比例。
读不到的事实：Hetzner 官方 CX 定价页今天**整页不渲染任何档的价格**，所以该档的价今天读不到；Contabo 整域 403，本轮未使用任何 Contabo 数字。

---

## 一、四列清单（页 URL / 改前 / 改后 / 站外返回码）

| 页 URL | 改前写的什么 | 改后写的什么 | 外面核到的返回码 |
|---|---|---|---|
| /cheap-vps-hosting（DigitalOcean 段·价格倍数句） | `The weakness is price: Hetzner offers four times the RAM for the same money.` | `The weakness is specs: Hetzner's CX23 includes 4 GB of RAM, where DigitalOcean's entry plan gives 512 MiB.` | **200** / 0 跳转 |
| /cheap-vps-hosting（Hetzner Pros） | `Best RAM-per-dollar in this list` | `2 vCPU and 4 GB RAM at the entry tier` | **200** / 0 跳转 |
| /cheap-vps-hosting（Hetzner 小节·带宽句） | `…the 500 GB that DigitalOcean and Vultr include at similar price points.` | `…the 500 GB that DigitalOcean and Vultr include on their entry plans.` | **200** / 0 跳转 |
| /cheap-vps-hosting（Contabo Pros） | `Highest RAM and vCPU count per dollar` | `4 vCPU and 8 GB RAM` | **200** / 0 跳转 |
| /cheap-vps-hosting（DigitalOcean Cons） | `Lower specs per dollar than Hetzner` | `Less RAM than Hetzner's entry plan` | **200** / 0 跳转 |
| /cheap-vps-hosting（ScalaHosting 段） | `For roughly 5-7 times the price of an unmanaged Hetzner plan with the same specs, you get …` | `At $29.95/month for 2 vCPU and 4 GB RAM, you get …`（只留 ScalaHosting 自己页面上读到的数） | **200** / 0 跳转 |
| /cheap-vps-hosting（Key Takeaways 第 3 条）※**超出你点名的范围** | `Most resources per dollar: Contabo's Cloud VPS 4 at $5.28/month …` | `Most resources in this comparison: Contabo's Cloud VPS 4 at $5.28/month …`（Contabo 价一字未动） | **200** / 0 跳转 |
| /cheap-vps-hosting（购买指南 7·Storage VPS）※**超出你点名的范围** | `…a Storage VPS line with far more storage per dollar than its compute-focused Cloud VPS.` | `…a Storage VPS line with far more storage than its compute-focused Cloud VPS.` | **200** / 0 跳转 |
| /cheap-vps-hosting（表格脚注） | `Prices verified as of September 2026 from official provider pricing pages. Hetzner price in EUR converted at approximately 1:1.07. Always verify current pricing on the provider's website before purchasing.` | `Prices verified as of September 2026 from official provider pricing pages. Always verify current pricing on the provider's website before purchasing.`（前后两句照旧） | **200** / 0 跳转 |
| /cheap-vps-hosting（表格 Storage 格 + 小节 spec-line） | 表格 `<td>40 GB</td>`；spec-line `…4 GB RAM · 40 GB SSD · 20 TB bandwidth` | 表格 `<td>40 GB NVMe</td>`；spec-line `…4 GB RAM · 40 GB NVMe · 20 TB bandwidth` | **200** / 0 跳转 |
| /cheap-vps-for-beginners（Key Takeaways 第 1 条） | `Hetzner CX22 at $3.79/month` | `Hetzner CX23 (price not displayed on Hetzner official page as of 2026-10-16)` | **200** / 0 跳转 |

两页标题均未变；线上文件与本地源文件**逐字节 IDENTICAL**。
周边页站外核验全部 **200 / 0 跳转**：`/`、`/best-vps`、`/contabo-review`、`/virtual-private-server`、`/free-vps`、`/forex-vps`、`/about`。

---

## 二、官方页原文与读取日期

**Hetzner —— 读到了（2026-10-16，当日第二次读，两次结果一致）**
`https://www.hetzner.com/cloud/cost-optimized/`，标题 `Cheap cloud-hosting – low vps prices for developers`

- 档位名原样：`CX23 / CAX11 / CX33 / CAX21 / CX43 / CAX31 / CX53 / CAX41`；**`CX22` 出现 0 次**
- CX23 那一行逐字：`CX23` · `not available` · `2` · `Intel®/AMD` · `4 GB` · **`40 GB` · `NVMe`** · `from  /month` · ` /hour` · `Create` ＋ `This product is currently unavailable. Please check back later.` ＋ `Traffic inclusive 20 TB /month`
- 价格：**整页 `€` 数字 0 处** ⇒ 该档的价今天读不到，页面上的价一律不冒充已核

**Contabo —— 本轮没读**（2026-10-16 全天整域 HTTP 403），所以本轮没有使用任何 Contabo 数字，`16 TB` 三处一字未动、未写复核日。

---

## 三、commit 与部署 id

- commit：**`121db94`** — `fix(claims): remove all price-derived claims on cheap-vps-hosting and cheap-vps-for-beginners`，已推送（`fa3aaa4..121db94` → main）
- 部署 id：**`https://6f4af243.serverbudget-site.pages.dev`**（project `serverbudget-site`）

---

## 四、没改的有哪些、为什么

1. **`16 TB` 三处**（表格 cell、Contabo spec-line、pros）：一字未动、未加标注、未写复核日（Contabo 读不到）。
2. **Contabo 的价 `$5.28 / $6.60`**：一字未动。
3. 其余 plan、结论句、署名 / byline、页面级 `September 2026`、sitemap、结构化数据：未动。
4. **`CX23 not available` 没写进正文**（那是官方页当下的临时状态）。
5. 上一轮留下的 Contabo 段 `<p class="note">Hetzner comparison re-checked…</p>`：保留未动。
6. @PAGE2 除那一句外**一字未动**，包括同句里的 `(last verified Sep 2026)`（见六·3）。
7. **本页还有 2 处倍数，但不是价格派生，按 NON_GOALS 未动**（原文见六·1）。
8. 第 398 行末句 `Hetzner is the better value.` 保留未动（不在你点名的短语里，但它是软性价格判断，见六·4）。

---

## 五、自检四项（线上实测）

| 检查项 | @PAGE1 线上 | @PAGE2 线上 |
|---|---|---|
| `CX22` 出现次数 | **0** | **0** |
| 我写进正文的自己算的倍数 | **0**（新句里无 `twice / double / 2x / 倍数`） | **0** |
| `per dollar` / `per-dollar` 处数 | **0** | **0** |
| `for the same money` 处数 | **0** | **0** |
| `times the price` 处数 | **0** | **0** |
| `3.79` 出现次数 | **0** | **0** |
| 未核到标注处数 | 2 | 1 |

（补充：`similar price` 也已清 0；本页 `NVMe` = 2 处。）

---

## 六、要你知道的三件事

1. **`per dollar` 实际有 5 处，你点名了 3 处**，我按同一判据把另外 2 处也清了（Key Takeaways 的 `Most resources per dollar`、购买指南的 `far more storage per dollar`），否则自检第 3 项过不去。两处改法都只去掉"per dollar"，数字与结论一字未动，可回退。
2. **本页仍有 2 处倍数，我判断不是价格派生，未动**：
   - 第 347 行（RackNerd 段）：`providers often lure customers with a low first year and double the rate on renewal.`（行业惯例陈述，无数字）
   - 第 554 行（购买指南·CPU 代次）：`The newer chip has four times the core count, double the memory bandwidth, and a newer I/O bus.`（CPU 规格比，8 核→32 核就在同段明写；但 `double the memory bandwidth` 与 Intel 公开规格对不上，属另一类问题）
   你若要把这两处也清，说一声即可。
3. **@PAGE2 那句里的 `(last verified Sep 2026)` 我按"别的一字不动"保留了**，但现在同句里已经有一项写着"未核到"，两者并读会显得别扭。
4. 第 398 行末句 `Hetzner is the better value.`：仍是软性价格判断（"更划算"要靠价支撑，而价今天读不到），未改，待你拍板。
