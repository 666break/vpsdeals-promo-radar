# fix_two_claims — 清单（serverbudget.com/cheap-vps-hosting）

执行日：2026-10-16（本机 GMT+8）
范围：`live-site/cheap-vps-hosting.html` 两处（倍数句 / 型号与价）
纪律：只动这两处；`16 TB` 那处一字未动；读不到的价不冒充已核；页面内不放中文。

---

## 一、四列清单（页 URL / 改前 / 改后 / 站外返回码）

| 页 URL | 改前写的什么 | 改后写的什么 | 外面核到的返回码 |
|---|---|---|---|
| serverbudget.com/cheap-vps-hosting（Contabo 段·倍数句） | `Contabo looks like the best deal on paper: four times the vCPU and double the RAM of Hetzner's CX22. But those 4 vCPUs are shared…` | `Contabo looks like the best deal on paper: 4 vCPU and 8 GB RAM against Hetzner's CX23 at 2 vCPU and 4 GB RAM. But those 4 vCPUs are shared…` | **200** / 0 跳转 |
| serverbudget.com/cheap-vps-hosting（对比表那一行） | `<td>Hetzner CX22</td>` + `<td class="price">$3.79/mo</td>` | `<td>Hetzner CX23</td>` + `<td class="price">price not displayed on Hetzner official page as of 2026-10-16</td>` | **200** / 0 跳转 |
| serverbudget.com/cheap-vps-hosting（小节标题 + spec-line） | `<h3>Hetzner CX22</h3>` + `$3.79/month (approx. $4) · 2 vCPU · 4 GB RAM · 40 GB SSD · 20 TB bandwidth` | `<h3>Hetzner CX23</h3>` + `price not displayed on Hetzner official page as of 2026-10-16 · 2 vCPU · 4 GB RAM · 40 GB SSD · 20 TB bandwidth` | **200** / 0 跳转 |
| serverbudget.com/cheap-vps-hosting（小节正文） | `Hetzner's CX22 offers the best price-to-specification ratio in this comparison. For the same $4 that DigitalOcean charges for 512 MiB of RAM, Hetzner gives you 4 GB and a second vCPU.` | `Hetzner's CX23 pairs 4 GB of RAM with a second vCPU, where DigitalOcean's entry plan gives 512 MiB and one vCPU.` | **200** / 0 跳转 |
| serverbudget.com/cheap-vps-hosting（Key Takeaways 第一条） | `Hetzner's CX22 gives 2 vCPU and 4 GB RAM for about the same price.` | `Hetzner's CX23 gives 2 vCPU and 4 GB RAM.` | **200** / 0 跳转 |
| serverbudget.com/cheap-vps-hosting（FAQ 正文） | `Hetzner's CX22 provides 2 vCPU and 4 GB RAM for about the same price.` | `Hetzner's CX23 provides 2 vCPU and 4 GB RAM.` | **200** / 0 跳转 |
| serverbudget.com/cheap-vps-hosting（FAQPage 结构化数据·同一句） | 同上（JSON-LD 内） | 同上（JSON-LD 内） | **200** / 0 跳转 |

周边页站外核验（全部 200 / 0 跳转）：`/`、`/cheap-vps-for-beginners`、`/best-vps`、`/contabo-review`、`/virtual-private-server`、`/free-vps`、`/forex-vps`、`/about`。
本页标题未变：`Cheap VPS Hosting in 2026: What Pricing Pages Won't Tell You | ServerBudget`；线上文件与本地源文件 **逐字节 IDENTICAL**。

---

## 二、官方页原文与读取日期

### Hetzner —— 读到了（2026-10-16，本机时间 05:2x，当日第二次读，两次结果一致）
页：`https://www.hetzner.com/cloud/cost-optimized/`，标题 `Cheap cloud-hosting – low vps prices for developers`

- 该页档位名（原样）：`CX23 / CAX11 / CX33 / CAX21 / CX43 / CAX31 / CX53 / CAX41`
- **`CX22` 在该页出现 0 次**
- CX23 那一行逐字：`CX23` · `not available` · `2` · `Intel®/AMD` · `4 GB` · `40 GB` · `NVMe` · `from  /month` · ` /hour` · `Create` ＋ `This product is currently unavailable. Please check back later.` ＋ `eu-central NBG1 HEL1` ＋ `Traffic inclusive 20 TB /month`
- 价格：**整页 `€` 数字 0 处**（价格字段渲染为空——`from /month` 后面没有数字），所以 `$3.79` 今天无法从官方页复核。

### Contabo —— 本轮没读（本轮未使用任何 Contabo 数字）
2026-10-16 全天 `contabo.com` 整域 **HTTP 403**（Contabo 自家反爬等待页）。按你的规矩：读不到的页不写复核日、不搬站内别处口径。

---

## 三、commit 与部署 id

- commit：**`fa3aaa4`** — `fix(claims): drop unsupported Hetzner ratio, re-point CX22 refs to CX23 (cheap-vps-hosting)`，已推送（`6f3e47c..fa3aaa4` → main）
- 部署 id：**`https://200adcba.serverbudget-site.pages.dev`**（project `serverbudget-site`，站目录 `live-site/`）

---

## 四、没改的有哪些、为什么

1. **`16 TB` 那处**（对比表 `16 TB`、Contabo spec-line `16 TB bandwidth`、pros `Generous 16 TB bandwidth`）：按你规矩**一字未动**，未加标注、未写复核日 —— Contabo 官方页读不到。
2. Contabo 的价 `$5.28 / $6.60`：未动。
3. 其余 6 家 plan、结论句（Bottom Line）、署名 / byline、页面级 `September 2026`、表格其它格、sitemap：未动。
4. 结构化数据：**只**改了 FAQPage 里那一句（因为它同样点名 CX22 且用那个价），BreadcrumbList 等其余 JSON-LD 未动。
5. 上一轮留下的 Contabo 段内 `<p class="note">Hetzner comparison re-checked against Hetzner's official cloud pricing page on 2026-10-16.</p>`：保留未动。
6. 站上**另一页** `cheap-vps-for-beginners.html` 第 227 行也点名同一档同一价：`Hetzner CX22 at $3.79/month`（同句还写 `last verified Sep 2026`）—— 不在本轮 @PAGE 范围内，未动。

---

## 五、自检两项

1. **线上 `CX22` 出现 0 次** —— 本页实测 0 次（`CX23` 7 次）✓
   （注：站上 `cheap-vps-for-beginners` 线上仍有 `CX22` 1 次 / `3.79` 1 次，属另一页，见四·6）
2. **自己算的倍数 0 个** —— 我写进正文的新句里没有任何 `twice / double / 2x / four times` 或比例数字 ✓
   线上实测：`four times the vCPU` = 0、`double the RAM` = 0、`for about the same price` = 0、`3.79` = 0、未核到标注 = 2 处。

---

## 六、顺带标记（超出边界，**未改**，请你拍板）

1. **本页仍有 2 处别的、依赖同一个读不到的价的比例句**（不在你点名的两处内，按 NON_GOALS 未动）：
   - 第 398 行（DigitalOcean 段）：`The weakness is price: Hetzner offers four times the RAM for the same money.`（且 4 GB vs 512 MiB 实为 8×，"four times" 本身也对不上）
   - 第 474 行（ScalaHosting 段）：`For roughly 5-7 times the price of an unmanaged Hetzner plan with the same specs…`
2. **表格脚注第 339 行**：`Prices verified as of September 2026 from official provider pricing pages. Hetzner price in EUR converted at approximately 1:1.07.` —— 现在与"未核到"那一格并存，且 EUR 折算那句已无对象。
3. **存储口径**：本站写 `40 GB SSD`，官方页今天写 `40 GB NVMe`（本轮按范围未动）。
4. **官方页上 CX23 那一行标 `not available`**（`This product is currently unavailable. Please check back later.`）：我按你指令把型号改成 CX23，但"该档当前官方不可购"这条事实必须让你知道。
5. **软性价格说法仍在**：表格脚注、第 373 行 `at similar price points`、pros 里 `Best RAM-per-dollar in this list`、`Highest RAM and vCPU count per dollar`。
6. **站上另一页** `cheap-vps-for-beginners.html`（第 227 行）同上第一条所述。

---

## 七、没做到的 / 说不清的

- `$3.79` 这个价：**今天读不到**，官方页整页不渲染价格。我没有用任何第三方数据站、也没有推算，只是把它标成未核到并把依赖它的说法改成不依赖数字的说法。
- Contabo 的 `16 TB`：**今天读不到**（403），所以那一处保持原样，也没有写复核日。
