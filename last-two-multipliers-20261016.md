# last_two_multipliers — 清单（@PAGE：serverbudget.com/cheap-vps-hosting）

执行日：2026-10-16（本机 GMT+8）
范围：`live-site/cheap-vps-hosting.html` 两处（CPU 段两个倍数、DO 段价格结论）
判据：正文里不出现自己算出来的倍数，只出现读到的数并列；没有能读到的价就不下价格结论。

---

## 一、四列清单（页 URL / 改前 / 改后 / 站外返回码）

| 页 URL | 改前写的什么 | 改后写的什么 | 外面核到的返回码 |
|---|---|---|---|
| /cheap-vps-hosting（购买指南 1·CPU 代次段） | `The newer chip has four times the core count, double the memory bandwidth, and a newer I/O bus.` | `The newer chip has 32 physical cores against the older chip's 8, and a newer I/O bus.` | **200** / 0 跳转 |
| /cheap-vps-hosting（DigitalOcean 段·末句） | `…where DigitalOcean's entry plan gives 512 MiB. If you do not need DigitalOcean's specific features, Hetzner is the better value.` | `…where DigitalOcean's entry plan gives 512 MiB.`（整句删除） | **200** / 0 跳转 |

- 两个倍数一起去掉了：`four times the core count`、`double the memory bandwidth`。只把同段里**已经印着的两个核数**并排（`32 physical cores against the older chip's 8`），另加 `a newer I/O bus`。
- `double the memory bandwidth` 没有 Intel 出处，**直接删掉，没有换成别的比例**。
- 价格结论半句**整句删除**，没有换成 `the best deal` / `cheapest` 这类同样要靠价支撑的词。
- 改后线上原文：`The newer chip has 32 physical cores against the older chip's 8, and a newer I/O bus. None of this appears on a pricing page that simply says "2 vCPU."`
- 本页标题未变，线上文件与本地源文件**逐字节 IDENTICAL**。
- 另一页 @PAGE2（/cheap-vps-for-beginners）本轮未改一字，仍 200 / 0 跳转、标题未变、与本地逐字节 IDENTICAL。
- 周边页站外核验全部 **200 / 0 跳转**：`/`、`/best-vps`、`/contabo-review`、`/virtual-private-server`、`/free-vps`、`/forex-vps`、`/about`。

---

## 二、commit 与部署 id

- commit：**`c6b7102`** — `fix(claims): remove last two computed multipliers and one price conclusion (cheap-vps-hosting)`，已推送（`121db94..c6b7102` → main）
- 部署 id：**`https://acd3618b.serverbudget-site.pages.dev`**（project `serverbudget-site`）

（本轮没有重读任何官方页，所以没有新的官方原文与读取日期可报；Hetzner CX 页今天的读数沿用当日 05:2x 那次：档位 `CX23 / CAX11 / CX33 / CAX21 / CX43 / CAX31 / CX53 / CAX41`，`CX22` 0 次，CX23 行 `not available`·`2`·`4 GB`·`40 GB NVMe`·`Traffic inclusive 20 TB /month`，整页 `€` 价 0 处。Contabo 今天整域 403，未读。）

---

## 三、没改的有哪些、为什么

1. **RackNerd 段 `double the rate on renewal`**（第 347 行）：按 DONT 一 保留 —— 它没有数，说的是行业做法，不在判据里。
2. **@PAGE2 的 `last verified Sep 2026`**（第 227 行、第 388 行共 2 处）：按 DONT 二 保留 —— 那个日期管的是同一串里另外两家的价。
3. `16 TB` 三处、`CX23 not available`、Contabo 的价 `$5.28/$6.60`、其余 plan、结论句、署名 / byline、页面级日期、sitemap、结构化数据：一律未动。
4. **第 488 行 `5-7x more expensive than unmanaged equivalents`（ScalaHosting 的 Cons 里）**：见四·2 —— 按"只报不改"未动，但它是同一判据下的漏网。

---

## 四、自检两项的结果

### 1. 点名那几处线上已清 0 处 ✓

| 检查串 | @PAGE1 线上 | @PAGE2 线上 |
|---|---|---|
| `four times` | 0 | 0 |
| `double the memory bandwidth`（含 `double the`） | 0（`double the` = 1，见下 2·①） | 0 |
| `is the better value` | 0 | 0 |
| `times the price` | 0 | 0 |
| `for the same money` | 0 | 0 |
| `per dollar` / `per-dollar` | 0 | 0 |
| `similar price` | 0 | 0 |
| `CX22` | 0 | 0 |
| `3.79` | 0 | 0 |

### 2. 两页里剩下的所有倍数词（`times` / `double` / `twice` / `per dollar`，另查 `triple` `quadruple` `half` `Nx`）—— 逐个列出，**只报不改**

| # | 位置 | 原文 | 判定 |
|---|---|---|---|
| ① | @PAGE1 第 347 行（RackNerd 段） | `…providers often lure customers with a low first year and **double the rate on renewal**.` | 无数字，行业做法陈述 → 按你的 DONT 一 **保留**（本轮未动） |
| ② | @PAGE1 第 488 行（ScalaHosting 的 Cons） | `<li>**5-7x** more expensive than unmanaged equivalents</li>` | **有数字、价格派生**（基数含读不到的 Hetzner 价）→ 按你"只报不改"**未动**，等你一句话即可按同一判据处理 |
| ③ | @PAGE2 第 388 行（disclosure） | `…built from typical signup, provisioning, SSH, and deploy **times** —…` | **假阳性**：`times` 是"次数"，不是倍数 |
| — | 两页其余 | `twice` = 0、`triple` = 0、`quadruple` = 0、`half` = 0、`per dollar` = 0、`for the same money` = 0、`times the price` = 0、`four times` = 0、`Nx` 仅第 488 行那 1 处 | — |

---

## 五、顺带标记（未改，待你拍板）

1. 上表 ② 的 `5-7x more expensive than unmanaged equivalents`：它与上一轮我从 ScalaHosting 段正文删掉的 `For roughly 5-7 times the price of an unmanaged Hetzner plan with the same specs` 是同一件事的两处写法，正文删了、Cons 里这条还在。
2. @PAGE2 第 388 行 disclosure 写 `The prices cited above are verified against official provider pages`，而同一页"上面引的价"里已经有一项写着 `price not displayed on Hetzner official page as of 2026-10-16`，两者并读会显得别扭（按 DONT 二 未动）。
