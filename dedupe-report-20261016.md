# serverbudget.com — 同主题页去重报告（新页 cloud-vps-server + 8 个同主题页）

执行时间：2026-10-16 02:05–02:15（本机时间）｜执行者：本机 AI（完全访问）｜仓库：`C:\Users\Administrator\vpsdeals-promo-radar`
比对范围（9 页）：`cloud-vps-server`（新页）、`cheap-vps-hosting`、`virtual-private-server`、`best-vps`、`free-vps`、`free-trial-vps`、`cheap-vps-for-beginners`、`windows-vps`、`cheap-windows-vps-hosting`

## 怎么比的（可复现）

用 Python 标准库 `HTMLParser` 把每页正文抽成块（`p` / `li` / `h2`–`h5` / `td` / `th`，跳过 `header`/`footer`/`nav`/`script`/`style`），归一化后按「词集 Jaccard」+「4-gram shingle Jaccard」跨页两两比对，取 ≥0.55 的段落对再聚成簇。9 页共抽出 1,254 个块。所有结论都可用本地文件 + 线上 curl 复核。

## 一、重复段 / 之前出现在哪几页 / 现在只留在哪一页

| # | 段落（首句识别） | 之前出现在哪几页 | 现在只留在哪一页 |
|---|---|---|---|
| 1 | 「We deliberately exclude vendor-owned promotional pages … benchmark-three list is pending owner input …」（第三方基准方法说明） | best-vps、windows-vps、cheap-windows-vps-hosting、free-vps、free-trial-vps、virtual-private-server（6 页） | **best-vps**（其余 5 页各换成一句指向 best-vps 的内链） |
| 2 | 「OVHcloud's VPS-1 is the lowest verified entry point that still supports Windows … this is the budget door.」 | windows-vps、cheap-windows-vps-hosting | **cheap-windows-vps-hosting**（windows-vps 换成内链） |
| 3 | 「The disadvantage is that the headline price lies by omission …」（Vultr 真实成本） | windows-vps、cheap-windows-vps-hosting | **cheap-windows-vps-hosting**（windows-vps 换成内链） |
| 4 | 「Pick Vultr. Scale CPU, RAM, and bandwidth independently, pay hourly …」（混合 Linux+Windows 该选谁） | windows-vps、cheap-windows-vps-hosting | **windows-vps**（cheap-windows-vps-hosting 换成内链） |
| 5 | 「Vultr's model is maximum flexibility: you pick any instance …」（Vultr 授权模式怎么运作） | windows-vps、cheap-windows-vps-hosting | **windows-vps**（cheap-windows-vps-hosting 换成内链）〔本次〕 |
| 6 | 「Pick OVHcloud VPS-1 at $4.54/month … the lowest verified entry into a Windows vps server.」 | windows-vps、cheap-windows-vps-hosting | **cheap-windows-vps-hosting**（windows-vps 换成内链）〔本次〕 |

判断依据（你给的唯一判据「来这个问题的人最该在哪一页看到它」）：问「Vultr / Contabo 的 Windows 授权到底怎么算、混合 Linux 与 Windows 该怎么选」的，是通用 Windows VPS 意图 → 留 `windows-vps`；问「最便宜的 Windows 门在哪、真实总成本是多少」的，是最便宜意图 → 留 `cheap-windows-vps-hosting`。

## 二、现在还有没有同主题的页在互相抢

有。`windows-vps` ↔ `cheap-windows-vps-hosting` 仍是同主题并行页：两页同时出现的近逐字重复段共 9 组，本次与上一班次合计削掉 5 组、另加 1 段 OVHcloud 叙述段（第 1–6 项），但**还剩 5 组**——两页的「入门计划表 spec 行」（OVHcloud / Contabo / Vultr）、「BYOL 问答」、「You run a mix of Linux and Windows」小标题，加上两页各自的 pros/cons 清单与 Bottom Line 仍高度重叠；另外 `best-vps` / `virtual-private-server` / `cheap-vps-hosting` / `cloud-vps-server` 四页的「入门价比较表」也互相重叠（同一批 provider、同一批数字）。这两处都需要你定「谁当主、谁当长尾」，不是删段能解决的。

## 三、改了哪个源文件 / 下次重建会不会还在

改了仓库 `live-site/` 下 6 个文件：`cheap-windows-vps-hosting.html`、`windows-vps.html`、`free-vps.html`、`free-trial-vps.html`、`virtual-private-server.html`、`index.html`（最后一个是 meta description 去掉过时的 "Linode"）。**会还在**——这 9 页的生成源就是仓库里的 `live-site/*.html`：`.github/workflows/update.yml` 每 6 小时 `actions/checkout@v4` 取仓库内容后直接 `wrangler pages deploy live-site/`，不重新生成文章页。本次已 commit `945ce84` 并 push 到 `origin/main`（已用 `git show origin/main:live-site/…` 逐页确认 5 页都带上了改动）。

> 关键修复：这些去重改动（含上一班次做的）此前**只落在本地磁盘和线上，没进仓库**。按上述流水线，下一次 CI 会把线上内容换回仓库里的旧版 —— 也就是把去重回退掉。本次一并入库，这个回退风险已解除。

## 四、判不了的段（列出来问你）

| # | 段落 | 出现在哪几页 | 我判不了的原因 |
|---|---|---|---|
| 1 | OVHcloud VPS-1 入门价行（$4.54/mo，2 vCores / 4 GB / 40 GB NVMe） | best-vps、virtual-private-server、windows-vps、cheap-windows-vps-hosting（4 页） | 9 页里没有 provider 页；问「OVHcloud 入门价」的人没有唯一该落的那一页。四页各有各的正当理由 |
| 2 | Contabo Cloud VPS 4 入门价行（Linux 版 $5.28/mo promo） | best-vps、virtual-private-server（2 页） | 同上；且 `cheap-vps-hosting` 同一 plan 写 $8.80/mo、Windows 两页写 €12.40 与 $14.88 —— 数字本身不一致，见第五节 |
| 3 | Vultr Cloud Compute from $5.00/mo 行 | windows-vps、cheap-windows-vps-hosting（2 页） | 两页都是 Windows 主题，判据分不开 |
| 4 | DigitalOcean Basic $4.00/mo 行 | best-vps、virtual-private-server（2 页） | 同上 |
| 5 | RackNerd KVM from $2.24/mo 行 | virtual-private-server、cheap-windows-vps-hosting（2 页） | 同上 |
| 6 | Hostinger KVM 1 $6.49/mo 行 | best-vps、**cloud-vps-server**（2 页） | 同上；这是新页与同主题页之间**唯一**的重复段 |
| 7 | 署名简介段「Marcus has been working with virtualized server infrastructure since 2015 …」 | best-vps、cheap-vps-hosting、cheap-windows-vps-hosting、free-vps、free-trial-vps、virtual-private-server、windows-vps（7 页） | 它是署名/E-E-A-T 元素，不是「验价数字 / 问答 / 结论」，也不回答任何访客问题——判据套不上。删掉 6 页只留 1 页会伤 E-E-A-T |
| 8 | 「Future guides will cover … RackNerd deals, and Black Friday VPS promotions.」 | best-vps、cheap-windows-vps-hosting、free-vps、virtual-private-server、windows-vps（5 页） | 同上，是页尾导览句，不是内容段 |
| 9 | BYOL 问答「Can I use my own Windows license on a VPS?」 | windows-vps、cheap-windows-vps-hosting（2 页） | 两页的 `FAQPage` JSON-LD 里**都**含这条问答。删可见答案而不动结构化数据会造成「标记与正文不符」，动 JSON-LD 就等于改数据 —— 两条都踩你的红线，需要你定 |
| 10 | 「You run a mix of Linux and Windows and want precise control」小标题 | windows-vps、cheap-windows-vps-hosting（2 页） | 它现在是内链的锚点小标题，删了那句内链就悬空；且它是标题不是段 |

**要你给的只有一件事**：上面 1–6 这六组「入门价数字行」和 9 这组问答，是 (a) 留在原地不动、(b) 统一并到某一页（例如 `virtual-private-server` 的 "Verified VPS Entry Prices" 或 `cheap-vps-hosting`）、还是 (c) 逐条指定保留页？你说一条我就能改生成源、重建、部署、再从外面核一遍。

## 五、附带发现（不在本次范围，我没动，供你决定）

1. `cheap-vps-hosting` 的 Contabo Cloud VPS 4 写 **$8.80/mo**，`best-vps` / `virtual-private-server` 同一个 plan 写 **$5.28/mo promo（$6.60 常规）**；RackNerd 也是 `cheap-vps-hosting` 写 $0.92/mo（1 GB/20 GB/2 TB）、别页写 $2.24/mo（512 MB/30 GB）。同一 plan 两个价，我只核不改 —— 数字要你确认哪个对。
2. 全部 9 页的 `<title>` 长度 79–90 字符、`<meta description>` 217–224 字符，都超过 SERP 常规上限（60 / 160）。既有状态，本次未动。
3. 站内链接仍写成 `.html`（访问时 308 跳到无后缀地址）。全站既有写法，本次新增的内链也沿用同一写法。
4. **本机现在同时有一个 Codex 会话在同一个仓库作业**（进程 `codex.exe` / `codex-windows-sandbox-ser`，它提交了 `bff5f82` 清理 `_verify_forex-vps.html`）。两个 AI 同时改同一仓库有冲突风险，建议同一时间只留一个。
5. 本机 `date -u` 比真实 UTC 慢 8 小时（本地 TZ 配成 +08:00、系统时钟按真实 UTC 走）。判断线上时间戳别用 `date -u`，以 HTTP `Date` 头为准。

## 六、线上复核（本次亲手从外面拉回来的）

- 9 页 `curl -sL` 全部 **200**（`https://serverbudget.com/<page>`）。
- 该留的在：`best-vps` 仍有方法说明；`cheap-windows-vps-hosting` 仍保留 OVHcloud 段与 headline-price 段；`windows-vps` 仍保留 "Pick Vultr"。
- 该删的没了：`cheap-windows-vps-hosting` 无 "Vultr's model is maximum flexibility"；`windows-vps` 无 "Pick OVHcloud VPS-1 at $4.54/month"。
- 新增内链 3 个目标全部 200：`/windows-vps`、`/cheap-windows-vps-hosting`、`/best-vps`。
- 6 个被改页的 `JSON-LD`（Article / BreadcrumbList / FAQPage）逐块 `json.loads` 全部通过；标签配平；中文字符 0。
- 部署：`python deploy_serverbudget.py` → 上传 3 个文件，deployment `2872fbc7.serverbudget-site.pages.dev`；线上 `index.html` 时间戳已刷新为本次部署时刻。
- 新页 `cloud-vps-server`、`cheap-vps-hosting`、`cheap-vps-for-beginners` 本次**未改动**（与上一版逐字节一致）。

## 边界遵守

未删任何一页；未新建页面；未改任何结论 / 公式 / 数据；未把重复段改写成空话（删掉的段都换成一句指向保留页的内链）；表里所有线上状态都是本次亲手 `curl` 拉回来核过的。
