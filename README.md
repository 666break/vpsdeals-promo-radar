# vpsdeals-promo-radar

Automated VPS hosting deal tracker. Scrapes real pricing from provider websites every 6 hours, builds a static site, and deploys to Cloudflare Pages — all free, all automated, no server.

**Live site:** `https://vpsdeals-promo-radar.pages.dev`

## What It Does

1. **Scrapes** VPS provider pricing pages (DigitalOcean, Hetzner, Contabo, Vultr, Hostinger, ScalaHosting)
2. **Extracts** real plan names, prices, and currencies — never fabricates
3. **Builds** static HTML pages with JSON-LD structured data for SEO
4. **Deploys** to Cloudflare Pages automatically via GitHub Actions
5. **Updates** every 6 hours — fresh deals, automatically

## Brand Positioning

**vpsdeals** — a no-nonsense VPS price comparison and deal tracking site. Real prices, real data, updated automatically. The value is in timeliness: whoever posts new pricing first wins.

## Tech Stack

- **Python 3.12** + requests + beautifulsoup4
- **GitHub Actions** (cron every 6 hours, unlimited on public repos)
- **Cloudflare Pages** (free static hosting)
- **Zero server, zero API keys, zero runtime cost**

## Quick Start

```bash
# Install dependencies
pip install requests beautifulsoup4

# Scrape provider pricing
python scraper.py

# Build static site
python build.py

# Site is generated in site/
```

## Repository Structure

```
├── .ilang/site.ilang        ← Site rules (SINGLE SOURCE OF TRUTH)
├── scraper.py               ← Reads site.ilang, scrapes providers, writes offers.json
├── build.py                 ← Reads site.ilang + offers.json, renders site/
├── templates/               ← HTML templates (index, provider, deal, compare)
├── data/offers.json          ← Scraped data (overwritten each run)
├── site/                     ← Generated static site
├── .github/workflows/update.yml  ← Cron: scrape → build → commit → push
├── AGENTS.md                 ← Instructions for AI agents taking over
└── README.md                 ← This file
```

## How to Add a Provider

Edit `.ilang/site.ilang`, add one line under `::MODULE{PROVIDERS}`:

```
  ProviderName | https://provider-website.com | https://provider-website.com/pricing |
```

Re-run `python scraper.py && python build.py`. The site now includes the new provider. That's it — no code changes needed.

## How to Add an Affiliate Link

Edit `.ilang/site.ilang`, add the affiliate URL in the 4th column:

```
  DigitalOcean | https://www.digitalocean.com | https://www.digitalocean.com/pricing | https://m.do.co/c/your-affiliate-code
```

Re-run. All deal pages now use the affiliate link instead of the bare URL.

## Monetization

- **Affiliate:** Providers with affiliate programs (CJ, ShareASale, Impact) — add links in site.ilang
- **Exit:** Package the site + domain + traffic history + revenue and sell it

Only legitimate affiliate networks per their public terms. Never brand-bid, cookie-inject, or self-promote.

## Why Register a Domain?

The `pages.dev` subdomain belongs to Cloudflare, not you. The SEO weight accumulates to Cloudflare's domain. Register your own domain ASAP and update `domain:` in `.ilang/site.ilang`. A domain registered today is one year older next year — start now.

## Site Rules

This site's configuration is defined using the **I-Lang protocol**. The rules are in `.ilang/site.ilang`, which is read by both `scraper.py` and `build.py` at runtime — it is not decorative. The protocol is explained at [ilang.ai](https://ilang.ai).

## License

MIT — do whatever you want with this.
