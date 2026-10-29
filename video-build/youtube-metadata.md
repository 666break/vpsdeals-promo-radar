# YouTube upload metadata

Every number spoken in these videos is taken from the matching article page, and
every article number traces to a provider page or the ECB rate file captured on
2026-10-29. Nothing here is estimated, and no view or subscriber figure is
claimed anywhere.

Narration is synthetic text-to-speech (Microsoft neural voice, `en-US-AndrewNeural`).
No human is impersonated and no stock footage is used: every frame is a still
rendered from the article's own tables.

---

## Video 1 — vps-price-sales-tax.mp4 (59 s)

**Title**
`VPS Price Sales Tax: What the Advertised Price Actually Costs After Tax`

**Description**
```
The advertised VPS price is pre-tax at all three providers we checked. This
video shows what gets added between the pricing page and the invoice, using the
figures published on 2026-10-29.

DigitalOcean publishes state and city sales tax rates from 1% (Connecticut) to
11.5% (Puerto Rico), set by the account address. A $24.00 4 GB / 2 vCPU Droplet
becomes $25.50 in Texas, $25.56 in Washington state and $26.76 in Puerto Rico.

OVHcloud's US storefront prints no tax text at all; the only disclosure is an
HTML element classed "tax-excluded-price". Hetzner prints "excl. VAT" next to
every price but does not print the rate on the page.

Against OVHcloud's $4.54, the pre-tax gap is 5.3x. After DigitalOcean's state
tax alone it becomes 5.90x.

Full breakdown, sources and formulas:
https://serverbudget.com/vps-price-sales-tax

Sources: docs.digitalocean.com/platform/billing/taxes/ and /taxes/usa/;
us.ovhcloud.com/vps/ (HTML source); hetzner.com/cloud/cost-optimized/;
digitalocean.com/pricing/droplets. All fetched 2026-10-29.

Narration is synthetic text-to-speech. No stock footage; frames are rendered
from the article's own tables.
```

---

## Video 2 — vps-price-currency-and-fx.mp4 (~55 s)

**Title**
`VPS Price Currency: The Same Plan in Four Storefronts`

**Description**
```
OVHcloud sells one VPS-1 configuration (2 vCPU, 4 GB RAM, 40 GB NVMe) on four
country storefronts, in four currencies, at four prices. This video converts all
four to euros at the European Central Bank reference rate for 2026-10-28
(1.1133 USD per euro, 0.83785 GBP per euro) and shows the gap.

US $4.54. UK £3.31 excluding VAT. Germany €4.53 including VAT. France €3.81
before tax.

Before tax, converted: €3.81 (France), €3.95 (UK), €4.08 (US) — a 7.0% spread on
identical hardware. Including the VAT each store prints: €4.53 (Germany), €4.57
(France), €4.74 (UK) — a 4.6% spread.

Two of the three providers give you no choice about the currency: DigitalOcean
bills in USD only and states it cannot provide an invoice in another currency;
Hetzner fixes the account currency at signup and will not change it afterwards.

Full table, rates and every division:
https://serverbudget.com/vps-price-currency-and-fx

Sources: us.ovhcloud.com/vps/, ovhcloud.com/en-gb/vps/, ovhcloud.com/de/vps/,
ovhcloud.com/fr/vps/; docs.digitalocean.com/platform/billing/taxes/;
docs.hetzner.com/cloud/billing/faq/; ecb.europa.eu euro foreign exchange
reference rates. All fetched 2026-10-29.

Narration is synthetic text-to-speech. No stock footage; frames are rendered
from the article's own tables.
```

---

## Channel

- Name: `ServerBudget`
- Handle preference order: `@serverbudget`, `@serverbudgetvps`, `@serverbudget_hq`
- Description:
```
VPS pricing, read off the provider's own pages. One billing question at a time:
what the advertised price includes, what gets added at checkout, and where the
same plan costs more than it should. Every figure is dated and sourced.
https://serverbudget.com
```
- Links: https://serverbudget.com
- No claims about audience size, no growth promises.
