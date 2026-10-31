# 倍数句 + 流量口径 修正报告（2026-10-16）

- 仓库：`C:\Users\Administrator\vpsdeals-promo-radar`　站点：serverbudget.com
- commit：**`6f3e47c`**（已 push 到 `origin/main`，`29c3af3..6f3e47c`）
- 部署：`python deploy_serverbudget.py` → project `serverbudget-site`
  → 部署 id `https://05a66b19.serverbudget-site.pages.dev`
- 开工前 LOCK：无 `.git/index.lock`，无第二个会话在动本仓库

---

## 一、两家官方页读到的原文 + 读的日期

### 1) Hetzner 官方云定价页 —— 读到了（2026-10-16 03:25 本机时间 / UTC 2026-10-15T19:25Z）

- 读的页：`https://www.hetzner.com/cloud/cost-optimized/`（CX 线定价页）
  与 `https://www.hetzner.com/cloud/`（总览）
- 读法：真实 Chrome（真实 User Data）+ CDP，取渲染后 DOM
- 页面标题：`Cheap cloud-hosting – low vps prices for developers`

**该页当前列出的档位（原样）**：

> CX23 / CAX11 / CX33 / CAX21 / CX43 / CAX31 / CX53 / CAX41

**每档的规格与价格区原文（以 CX23 为例，逐字）**：

> `CX23` `not available` `2` `Intel®/AMD` `4 GB` `40 GB` `NVMe` `from  /month` ` /hour` `Create`
> `This product is currently unavailable. Please check back later.`
> `eu-central  NBG1  HEL1` `Traffic inclusive` `20 TB` ` /month`

**关键事实：整页 `CX22` 出现 0 次**（对 `document.documentElement.outerHTML` 正则计数 = 0）。
CX22 已被 **CX23** 取代。另外该页所有档位都显示 `from  /month`（价格不渲染）+ “currently unavailable”。

旁证（官方价格 API，非第三方）：

- `https://website-price-api.hetzner.com/api/v1/views/cloud_matrix`（updatedAt `2026-10-08T11:12:21+02:00`）
  只有 3 条「起价」条目，最便宜的云主机起价 **€5.99 / $7.09 每月**，无 CX22 条目。
- `https://website-price-api.hetzner.com/api/v1/products/CLOUD_132+CLOUD_21`
  → `monthly EUR 5.99 / USD 7.09`（Cost-Optimized 线起价）

**⇒ 结论：Hetzner 官方定价页上读不到 CX22 这一档的价（这一档已不在官方页）。**

### 2) Contabo 官方 VPS 定价页 —— **没读到（整域被挡）**

- 目标页：`https://contabo.com/en/vps/`
- 实测结果：**HTTP 403**，返回 Contabo 自家反爬等待页（不是 Cloudflare 通用页）：
  - `<title>Contabo.com</title>`、`<meta http-equiv="refresh" content="360">`、约 20,940 字节
- 覆盖面：**整域**（`/en/`、`/en/vps/`、`/de/vps/`、`/en/cloud-vps/`、`/en/vps-hosting/` 全部 403）
- 两条出口都试过：直连 403、走本机代理 `127.0.0.1:51474` 403
- 真实 Chrome（真实 User Data）+ CDP：连等 **7 分 16 秒**、期间 8 次重载，标题始终是「请稍候…」，未放行
- **⇒ 读不到官方原话，因此没动带宽口径，也没拿任何别处的口径顶。**

---

## 二、清单（四列）

| 页 URL | 改前写的什么 | 改后写的什么 | 外面核到的返回码 |
|---|---|---|---|
| https://serverbudget.com/cheap-vps-hosting （Detailed Breakdown · Contabo Cloud VPS 4 条目，第 447 行） | `Contabo looks like the best deal on paper: four times the vCPU and double the RAM of Hetzner's CX22 for roughly double the price. But those 4 vCPUs are shared, and shared vCPUs can be oversold.` | `Contabo looks like the best deal on paper: four times the vCPU and double the RAM of Hetzner's CX22. But those 4 vCPUs are shared, and shared vCPUs can be oversold.`<br>（并新增一行复核日：`<p class="note">Hetzner comparison re-checked against Hetzner's official cloud pricing page on 2026-10-16.</p>`） | **200**，0 次跳转，标题与本地逐字节相同 |
| https://serverbudget.com/cheap-vps-hosting （同一档的流量口径，共 3 处：Price Comparison 表 Bandwidth 列第 322 行 `16 TB`／spec-line 第 446 行 `16 TB bandwidth`／pros 第 455 行 `Generous 16 TB bandwidth`） | `16 TB` / `16 TB bandwidth` / `Generous 16 TB bandwidth` | **未改（原样）** —— 读不到 Contabo 官方页，不许拿别处的口径顶 | **200**，0 次跳转 |

**未动的部分（边界内，逐条确认过）**：这一档的价（$5.28/$6.60）、其余 6 家 plan 的价格与结论句、
署名与 byline（`Last updated Sep 21, 2026`）、页面级 `Prices verified as of September 2026`、
结构化数据（JSON-LD）、sitemap 条数、404 与其它页 —— 一个字没碰。

---

## 三、commit 号

- **`6f3e47c`** — `fix(claim): remove unverifiable Hetzner price multiplier on cheap-vps-hosting`
- 上一笔（本次的前置，未回退）：`29c3af3` — 把这一档价从 `$8.80` 对齐到官方 `$5.28/$6.60`

---

## 四、读不到的那一处 —— 明写读不到，我删了什么

### A. Hetzner CX22 那一档的价：**读不到**（官方页已无 CX22，只有 CX23，且全档价格不渲染）

- 按判据执行：**把那半句价格对比整个删掉，只留内存那一半**。
- 我删掉的是这 6 个词：**`for roughly double the price`**
- **一个自己算的数都没出现**：没有写 1.3×、1.4×、1.7× 之类任何倍数，也没有把 `$3.79` 或 `€3.79` 留在这一句里。

### B. Contabo 这一档的流量口径：**读不到**（contabo.com 整域 403）

- 我**没有删任何东西**，也**没有把站内别处那句 `unlimited traffic` 搬过来**（那正是被禁止的「拿别处的口径顶」）。
- 该处保持原样 `16 TB bandwidth`，本次**未加复核日** —— 没读过的页上写复核日就是假话。

---

## 五、按边界「未动」但建议 owner 拍板的两处（都在 cheap-vps-hosting.html 同一段）

1. **`four times the vCPU` 本身是旧错**：Contabo Cloud VPS 4 = 4 vCPU，Hetzner CX22 = 2 vCPU ⇒ 实际是 **2×**，不是 4×。
   超出本次「只动这两处」的边界，**未改**，仅标记。
2. **`Hetzner's CX22` 这个型号已不在 Hetzner 官方定价页上**（现在是 CX23）。
   本次只按判据删了价格半句，没改型号名，**未改**，仅标记。

---

## 六、站外核验明细（都是从外面重新拉的，没有拿「部署成功」当核过）

| 页 | 站外返回码 | 跳转次数 | 标题与本地比对 |
|---|---|---|---|
| https://serverbudget.com/cheap-vps-hosting | 200 | 0 | SAME |
| https://serverbudget.com/ | 200 | 0 | SAME |
| https://serverbudget.com/best-vps | 200 | 0 | SAME |
| https://serverbudget.com/contabo-review | 200 | 0 | SAME |
| https://serverbudget.com/virtual-private-server | 200 | 0 | SAME |
| https://serverbudget.com/free-vps | 200 | 0 | SAME |
| https://serverbudget.com/forex-vps | 200 | 0 | SAME |

另：线上 `cheap-vps-hosting` 的 HTML 与本地文件 `live-site/cheap-vps-hosting.html` **逐字节 diff = IDENTICAL**；
旧句 `for roughly double the price` 在线上出现 **0 次**。

---

## 七、复核日

- 本次读官方页日期：**2026-10-16**（Hetzner 读到了；Contabo 被 403 挡住，没读到）
- 已写在改动处：`<p class="note">… re-checked against Hetzner's official cloud pricing page on 2026-10-16.</p>`
- 页面级 `September 2026` 与页面 byline **未动**。
- `live-site/index.html` 的页脚构建时间戳由部署脚本自动刷成 `2026-10-15T19:44:08Z`（构建时间，非复核日，未提交）。
