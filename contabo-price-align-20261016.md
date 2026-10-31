# Contabo Cloud VPS 4 价格对齐报告

- 日期：2026-10-16（本机时间）
- commit：`29c3af3`（已 push 到 origin/main，`5a558c0..29c3af3`）
- 部署：`wrangler pages deploy live-site/` → project `serverbudget-site`，部署 id `https://83538710.serverbudget-site.pages.dev`
- 改动范围：仅 `live-site/cheap-vps-hosting.html` 的 3 处价格行 + `live-site/index.html` 的 `Last updated:` 构建时间戳（部署脚本自动）

---

## 一、官方页读到的原文（唯一来源：Contabo 官方定价页）

- URL：`https://contabo.com/en/vps/`
- 读取时间：**2026-10-16 02:56**（本机时间；UTC 2026-10-15T18:56Z）
- 读取方式：真实 Chrome（真实 User Data）+ CDP，页面 `lang="en"`，货币选择器为 `$`（USD）
- 页面标题：`The Best Value Cloud VPS On Earth`

Cloud VPS 4 卡片 **DOM 原文**：

```html
<div class="previous-price-row" aria-active="false"><span class="previous-price">$6.60</span></div>
<div class="price-wrapper default">
  <div class="currency-col currency-before"><span class="currency-symbol">$</span></div>
  <div class="pre-decimal-col">5</div>
  <div class="decimal-col">
    <span class="decimal">28</span>
    <span class="monthly"><span class="currency-symbol curency-after">$</span> / month</span>
  </div>
</div>
<div class="net-price-wrapper" aria-active="true"><span class="net-price">$5.28</span> Including VAT / Excluding VAT</div>
<div class="price-legal-text">for the first 24 months</div>
```

页面页脚法定说明原文：

> The price displayed is the effective monthly rate for a 24-month subscription including applicable taxes.

> Minimum initial contract length: 1 month | Minimum following contract length: Equal to the initial contract length | Minimum cancellation notice: None (pre-paid) or 4 weeks (post-paid).

**⇒ 官方给的正是 promo 与 standard 两个数：**

| | 数值 | 期限 |
|---|---|---|
| promo（前 24 个月） | **$5.28 / month** | 前 24 个月 |
| standard（标准价，页面以划线价显示） | **$6.60 / month** | 24 个月期满后 |
| 换价点 | — | 第 24 个月结束时 |

旁证（同一页其它档位，promo 一律 = 划线标准价的 **80%**）：6.00/7.50、11.20/14.00、20.00/25.00、29.60/37.00、39.20/49.20 —— Cloud VPS 4 的 5.28/6.60 同样正好 = 80%。

**官方页全文出现 `8.80` 的次数：0。**

---

## 二、清单（四列）

### A. 已改动（全部在 `cheap-vps-hosting.html`，该页本档价共 3 处，全部是 $8.80）

| 页面 URL | 改前 | 改后 | 站外返回码 |
|---|---|---|---|
| https://serverbudget.com/cheap-vps-hosting （Key Takeaways 第 1 条） | `Contabo's Cloud VPS 4 at $8.80/month` | `Contabo's Cloud VPS 4 at $5.28/month for the first 24 months ($6.60/month regular)` | **200**（0 次跳转） |
| https://serverbudget.com/cheap-vps-hosting （Price Comparison 表 · Monthly Price 列） | `<td class="price">$8.80/mo</td>` | `<td class="price">$5.28/month for the first 24 months ($6.60/month regular)</td>` | **200**（0 次跳转） |
| https://serverbudget.com/cheap-vps-hosting （Detailed Breakdown · Contabo 条目 spec-line） | `$8.80/month · 4 vCPU · 8 GB RAM · 100 GB SSD · 16 TB bandwidth` | `$5.28/month for the first 24 months ($6.60/month regular) · 4 vCPU · 8 GB RAM · 100 GB SSD · 16 TB bandwidth` | **200**（0 次跳转） |

三处用了**同一个写法**：`$5.28/month for the first 24 months ($6.60/month regular)`（该写法与站内最常用的一致）。

### B. 未改动（数值本来就 = 官方，复核后确认无需动）

| 页面 URL | 改前 | 改后 | 站外返回码 |
|---|---|---|---|
| https://serverbudget.com/best-vps | `$5.28/mo promo / $6.60 std`（表）；`$5.28/month … standard is $6.60`（正文） | 同左（未改） | 200（0 次跳转） |
| https://serverbudget.com/virtual-private-server | `$5.28/mo (first 24 mo) … $6.60/mo regular` | 同左（未改） | 200（0 次跳转） |
| https://serverbudget.com/contabo-review | `$5.28 / mo` + `$6.60 / mo`（表）；正文多处 | 同左（未改） | 200（0 次跳转） |
| https://serverbudget.com/contabo-coupon-code | `$5.28/month for the first 24 months (regular $6.60/month)` | 同左（未改） | 200（0 次跳转） |
| https://serverbudget.com/vps-black-friday | `$5.28/mo` | 同左（未改） | 200（0 次跳转） |
| https://serverbudget.com/racknerd-vps | `$5.28/mo` | 同左（未改） | 200（0 次跳转） |
| https://serverbudget.com/free-trial-vps | `$5.28/mo` | 同左（未改） | 200（0 次跳转） |
| https://serverbudget.com/forex-vps | `$5.28/mo` | 同左（未改） | 200（0 次跳转） |
| https://serverbudget.com/hostinger-review | `$5.28/mo`（内链文字） | 同左（未改） | 200（0 次跳转） |
| https://serverbudget.com/a2-hosting-review | `$5.28/mo`（内链文字） | 同左（未改） | 200（0 次跳转） |

**说明**：任务点名的是三处（cheap-vps-hosting、best-vps、virtual-private-server）。实测 best-vps 与 virtual-private-server 早已等于官方值（$5.28/$6.60），所以本次实际落笔的只有 cheap-vps-hosting 的 3 处 $8.80。

### C. 站外核验（14 页，全部 `200 | 0 次跳转`，标题与本地逐字节相同）

a2-hosting-review, best-vps, cheap-vps-hosting, cheap-windows-vm, cheap-windows-vps-hosting, contabo-coupon-code, contabo-review, forex-vps, free-trial-vps, hostinger-review, racknerd-vps, virtual-private-server, vps-black-friday, windows-vps —— 全部 `200`，`num_redirects=0`，`<title>` 与本地文件 `SAME`。

---

## 三、部署后全站再搜「这一档价的第二个写法」

- `live-site/` 全站：`8.80` 出现 **0 次**（已清干净）。
- Cloud VPS 4（Linux 云主机）这一档，全站现在只有一种价：**$5.28 / $6.60**，与官方一致。
- 仍然存在**带「Cloud VPS 4」字样的另一种价**，但那是**另一个 SKU**（含 Windows 授权的 Windows 线），本次**未动**：

| 页面 | 现值 | 站外返回码 |
|---|---|---|
| https://serverbudget.com/cheap-windows-vps-hosting | `Windows Server VPS (Cloud VPS 4)`：`$14.88/mo`（前 24 个月）/ `$16.20/mo regular` | 200（0 次跳转） |
| https://serverbudget.com/cheap-windows-vm | `~$14.88/mo intro` / `$16.20 regular` | 200（0 次跳转） |
| https://serverbudget.com/windows-vps | `Windows Server VPS (CLOUD VPS 4)`：`€12.40/mo excl. VAT`（前 24 个月）/ `€15.50 incl. VAT` / `€16.88 standard` | 200（0 次跳转） |

⇒ 这三处要不要一起按 Contabo 的 **Windows VPS 页**核，属另一档的活，**需 owner 决定**（我这次只读了 `/en/vps/`，没读 Windows 页，所以不给结论、不给数字）。

- `templates/`、`build.py`、脚本、json 里都没有这一档价；`site/`（.gitignore 的构建产物）里还留着旧 `8.80`，但 `site/` 不参与部署，可忽略。

---

## 四、按边界「未动」但需 owner 拍板的两处（都在 cheap-vps-hosting.html 同一段）

1. **第 447 行原句**：`Contabo looks like the best deal on paper: four times the vCPU and double the RAM of Hetzner's CX22 for roughly double the price.`
   这句是围绕旧价 **$8.80**（≈ Hetzner CX22 的 ~$4 的两倍）写的。价格改成 $5.28 后，`roughly double the price` 不再成立（约 1.3×）。
   按边界「不许改动这一档价以外的任何数字或句子」，**我没有动它**，只做标记。
2. **带宽写法**：同页本档写 `16 TB bandwidth`，站内其它页写 `unlimited traffic`。不是价格，**未动**。

---

## 五、复核日期

- **本次读官方页日期：2026-10-16**
- **建议复核日期：2026-11-16**（该 promo 是 24 个月期内的自动折扣，官方标价随时可变）
- 站内**页面级**日期（`cheap-vps-hosting` 表下 `Prices verified as of September 2026`、byline `Last updated Sep 21, 2026`）**不是本档复核日**，未动；`index.html` 的 `vdate` 仍为 `2026-10-14`，也未动（部署脚本已不再自动刷它）。
