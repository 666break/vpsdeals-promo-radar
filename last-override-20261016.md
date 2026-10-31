# last_override — 清单（@PAGE1 漏网倍数 + @PAGE2 披露句）

执行日：2026-10-16（本机 GMT+8）
范围：`live-site/cheap-vps-hosting.html`（1 处）、`live-site/cheap-vps-for-beginners.html`（1 处）
判据：正文与列表里都不出现自己算出来的倍数，只出现读到的数并列；声称核过的说法不能跟"未核到"那一格打架。

---

## 一、四列清单（页 URL / 改前 / 改后 / 站外返回码）

| 页 URL | 改前写的什么 | 改后写的什么 | 外面核到的返回码 |
|---|---|---|---|
| /cheap-vps-hosting（ScalaHosting 的 Cons 列表） | `<li>5-7x more expensive than unmanaged equivalents</li>` | `<li>Higher monthly price than unmanaged plans</li>` | **200** / 0 跳转 |
| /cheap-vps-for-beginners（disclosure 段） | `The prices cited above are verified against official provider pages on our <a href="cheap-vps-hosting.html">cheap VPS pricing page</a> (last verified Sep 2026).` | `The prices cited above are verified against official provider pages on our <a href="cheap-vps-hosting.html">cheap VPS pricing page</a> (last verified Sep 2026), except where noted.` | **200** / 0 跳转 |

- 第一处：倍数与数字全去，**没有加任何数**，没换成别的比例；同段正文 `The unmanaged renewal price for the same configuration is $24.95/month, so the managed premium is about $5/month over the unmanaged rate. That is a narrower gap than most people assume.` 与新句不打架（两边都只说"更高"，正文另说清只高约 $5）。
- 第二处：只加限定 `, except where noted.`，其余一字未动。

### 那句披露句长在哪里（改前先查，结论：只长在这一页自己的源文件里）

| 位置 | 是否部署源 | 处理 |
|---|---|---|
| `live-site/cheap-vps-for-beginners.html:388` | **是**（部署源） | **已改** |
| `site/cheap-vps-for-beginners.html:388` | 否（`build.py` 的构建产物，`.gitignore` 第 1 行忽略） | 未动 |
| `live-site.pre-dailyshift-20261013.bak/`、`live-site.pre-polish.bak/` | 否（本地快照） | 未动 |
| 共用模板 / 构建脚本 | —— | **查无此句** |

依据：`build.py` 第 538–562 行是 **单向** `live-site/ → site/`（注释原文 `live-site/ is the deploy source, so it must carry GA4 BEFORE the copy.`），`deploy_serverbudget.py` 第 19 行 `SITE_DIR = .../live-site`。所以 `site/` 不是源、不会被反向覆盖，**只改一页不留岔口**。全仓库搜 `cited above are verified` 也只命中这一页源文件（另两处是构建产物与快照）。

---

## 二、commit 与部署 id

- commit：**`d38fec8`** — `fix(claims): drop last computed multiplier (ScalaHosting cons) and qualify the verification claim`，已推送（`c6b7102..d38fec8` → main）
- 部署 id：**`https://b6f19a97.serverbudget-site.pages.dev`**（project `serverbudget-site`）

（本轮未重读任何官方页，无新的官方原文；Hetzner 沿用当日 05:2x 读数，Contabo 今天整域 403 未读。）

---

## 三、没改的有哪些、为什么

1. **RackNerd 段 `double the rate on renewal`**（@PAGE1 第 347 行）：按 DONT 一 保留 —— 没有数，说的是行业做法。
2. **@PAGE2 第 388 行那句里的 `deploy times`**：按 DONT 二 不动 —— 是"次数"，假阳性。
3. `16 TB` 三处、`CX23 not available`、Contabo 的价、其余 plan、结论句、署名 / byline、页面级日期、sitemap、结构化数据：一律未动。
4. `site/` 构建产物与两个 `.bak` 快照里的旧字符串：未动（非部署源；下次 `build.py` 会按 `live-site/ → site/` 刷新）。

---

## 四、自检的结果（原样贴）

**两页返回码 / 标题 / 逐字节**

```
cheap-vps-hosting => HTTP:200 REDIR:0 SIZE:38478
  live title : <title>Cheap VPS Hosting in 2026: What Pricing Pages Won't Tell You | ServerBudget</title>
  local title: <title>Cheap VPS Hosting in 2026: What Pricing Pages Won't Tell You | ServerBudget</title>
  线上 vs 本地: IDENTICAL
cheap-vps-for-beginners => HTTP:200 REDIR:0 SIZE:29128
  live title : <title>Cheap VPS Hosting for Beginners: Deploy Your First Server in Under an Hour | ServerBudget</title>
  local title: <title>Cheap VPS Hosting for Beginners: Deploy Your First Server in Under an Hour | ServerBudget</title>
  线上 vs 本地: IDENTICAL
```

**点名处线上 0 处**

```
PAGE1: 5-7x=0  5-7=0  Nx=0  higher_monthly=1  four_times=0  per_dollar=0  same_money=0  times_the_price=0  CX22=0  3.79=0
PAGE2: except_where_noted=1  5-7=0  Nx=0  CX22=0  3.79=0
```

**线上改后原文（原样）**

```
① <li>Higher monthly price than unmanaged plans</li>
② The prices cited above are verified against official provider pages on our <a href="cheap-vps-hosting.html">cheap VPS pricing page</a> (last verified Sep 2026), except where noted.
```

**两页剩余倍数词（原样，只报不改）**

```
C:/tmp/F_cheap-vps-hosting.html:347:rs often lure customers with a low first year and double the rate on renewal.</p>
C:/tmp/F_cheap-vps-for-beginners.html:388:rom typical signup, provisioning, SSH, and deploy times &mdash; your experience will vary with provider s
```

即：@PAGE1 只剩第 347 行 `double the rate on renewal`（无数字，按 DONT 一 保留）；@PAGE2 只剩 `deploy times`（假阳性）。两页 `twice` / `per dollar` / `Nx` / `5-7` 均为 0。

**周边页站外核验（全 200 / 0 跳转）**

```
/                          HTTP:200 REDIR:0
/best-vps                  HTTP:200 REDIR:0
/contabo-review            HTTP:200 REDIR:0
/virtual-private-server    HTTP:200 REDIR:0
/free-vps                  HTTP:200 REDIR:0
/forex-vps                 HTTP:200 REDIR:0
/about                     HTTP:200 REDIR:0
```
