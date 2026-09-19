::ILANG [TYPE:agent-guide][PROJECT:coupon-niche-autojourney][LANG:en]

# AGENTS.md — For any AI taking over this repo

## What This Project Is

A zero-server, zero-cost, self-updating VPS hosting coupon/deal vertical site. Deployed on Cloudflare Pages. Scrapes provider pricing pages every 6 hours via GitHub Actions, builds static HTML, and auto-commits updates.

The site is live at `https://vpsdeals-promo-radar.pages.dev` (or a custom domain once registered).

## Single Source of Truth

**`.ilang/site.ilang`** is the ONLY config file that matters. It defines:
- Brand name, niche, domain
- Which providers to scrape (add/remove a line here and the site changes)
- Which fields to extract from each offer
- Rules (no fabrication of prices, no expired offers left as valid)
- Permanent boundary (never fabricate offers, prices, or commissions)

`scraper.py` and `build.py` MUST read this file. They do not have a second hardcoded provider list. If you change a provider in `site.ilang` and re-run, the site must change — otherwise the I-Lang is decorative and must be fixed.

## What You Can Do

- Add or remove providers in `.ilang/site.ilang` (one line per provider)
- Update templates in `templates/` (HTML with `{{PLACEHOLDER}}` variables)
- Fix bugs in `scraper.py` or `build.py`
- Add affiliate links in `site.ilang` (4th column, pipe-separated)
- Register a custom domain and update `domain:` in `site.ilang`

## What You Must NOT Do

::BOUNDARY{never:编优惠 编价格 编佣金|scope:permanent}
- Never fabricate offers, prices, or commissions
- Never add prices that weren't scraped from a real page
- Never leave expired offers pretending to be valid
- Never buy followers, inflate traffic, or post fake deals
- Never brand-bid, cookie-inject, or do anything that circumvents platform rules

## Tech Stack

- Python 3.12 (requests + beautifulsoup4 for scraping)
- GitHub Actions (cron every 6 hours)
- Cloudflare Pages (static hosting, free tier)
- No server, no API keys, no inference at runtime
- I-Lang protocol for config (learnable at ilang.ai)

## File Responsibilities

| File | Responsibility |
|------|---------------|
| `.ilang/site.ilang` | Site rules: providers, fields, boundaries |
| `scraper.py` | Reads site.ilang → fetches provider pages → writes data/offers.json |
| `build.py` | Reads site.ilang + offers.json → renders site/ with JSON-LD + sitemap |
| `templates/*.html` | Page templates with `{{PLACEHOLDER}}` variables |
| `data/offers.json` | Scraped data (overwritten each run) |
| `.github/workflows/update.yml` | Cron: scrape → build → commit → push |
| `site/` | Generated static site (output of build.py) |

## I-Lang Protocol

This project uses the I-Lang protocol for configuration. The `.ilang/site.ilang` file is NOT a decorative comment — it is read by both `scraper.py` and `build.py` at runtime. It is the single source of truth for site configuration. Changing it changes the site. Protocol explained at [ilang.ai](https://ilang.ai).
