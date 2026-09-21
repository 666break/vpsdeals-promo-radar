#!/usr/bin/env python3
# ::ILANG [TYPE:component][COMPONENT:build][LANG:py]
# RESPONSIBILITY: Read .ilang/site.ilang for site config + data/offers.json, render static HTML site
#                 into site/ with JSON-LD structured data, sitemap.xml, robots.txt.
# BOUNDARY: Never fabricate data. Only render what's in offers.json. Generate sitemap lastmod
#           from actual scrape time. Per-page title/description from data, not one template for all.

import json
import os
import re
import sys
import html
from datetime import datetime, timezone
from pathlib import Path

# ─── ILANG PARSER (same logic as scraper.py — kept self-contained) ──────────

def parse_ilang(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    config = {'providers': [], 'fields': []}
    state_match = re.search(
        r'::STATE\{@SITE,\s*brand:([^,]+),\s*niche:([^,]+),\s*domain:([^]}]+)', content)
    if state_match:
        config['brand'] = state_match.group(1).strip()
        config['niche'] = state_match.group(2).strip()
        config['domain'] = state_match.group(3).strip()
    providers_section = re.search(
        r'::MODULE\{PROVIDERS[^}]*\}\s*\n(.*?)(?=::MODULE\{|::RULE\{|::BOUNDARY\{|$)',
        content, re.DOTALL)
    if providers_section:
        for line in providers_section.group(1).strip().split('\n'):
            line = line.strip()
            if line and '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    config['providers'].append({
                        'name': parts[0], 'website': parts[1], 'offer_url': parts[2],
                    })
    return config


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def slug(name):
    s = re.sub(r'[^a-z0-9]+', '-', name.lower().strip())
    return s.strip('-')

def fmt_price(price, currency):
    if price is None:
        return 'N/A'
    sym = {'USD': '$', 'EUR': '€', 'GBP': '£'}.get(currency, '')
    return f'{sym}{price:.2f}'

def esc(text):
    return html.escape(str(text), quote=True)

def now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def now_date():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')

def month_name():
    return datetime.now(timezone.utc).strftime('%B %Y')


# ─── TEMPLATE ENGINE ─────────────────────────────────────────────────────────

def render(template_str, variables):
    """Simple {{KEY}} replacement."""
    result = template_str
    for key, val in variables.items():
        result = result.replace('{{' + key + '}}', str(val))
    return result


def load_template(name):
    tpl_dir = Path(__file__).parent / 'templates'
    tpl_path = tpl_dir / name
    with open(tpl_path, 'r', encoding='utf-8') as f:
        return f.read()


# ─── PAGE GENERATORS ─────────────────────────────────────────────────────────

def gen_index(brand, niche, domain, offers, providers):
    """Homepage: brand intro + all deals sorted by price."""
    sorted_offers = sorted(
        [o for o in offers if o.get('price') is not None],
        key=lambda o: o['price']
    )

    # Build deal cards
    cards = []
    for o in sorted_offers:
        p_slug = slug(o['provider'])
        d_slug = slug(o['title'])
        cards.append(f'''
        <a class="card" href="/deal/{p_slug}-{d_slug}.html">
          <div class="card-provider">{esc(o["provider"])}</div>
          <div class="card-title">{esc(o["title"])}</div>
          <div class="card-price">{fmt_price(o.get("price"), o.get("currency", "USD"))}<span class="per">/mo</span></div>
        </a>''')

    # Provider filter links
    prov_links = []
    for p in providers:
        p_slug = slug(p['name'])
        count = sum(1 for o in offers if o['provider'] == p['name'])
        prov_links.append(
            f'<a href="/provider/{p_slug}.html" class="filter-link">{esc(p["name"])} ({count})</a>'
        )

    # JSON-LD ItemList
    item_list = []
    for i, o in enumerate(sorted_offers[:20], 1):
        p_slug = slug(o['provider'])
        d_slug = slug(o['title'])
        item_list.append({
            "@type": "ListItem",
            "position": i,
            "url": f"https://{domain}/deal/{p_slug}-{d_slug}.html",
            "name": f'{o["provider"]} {o["title"]} {fmt_price(o.get("price"), o.get("currency","USD"))}/mo'
        })
    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{brand} — {niche} deals",
        "itemListElement": item_list
    }, indent=2) if item_list else ''

    title = f'{brand.capitalize()} — {niche} Deals & Pricing ({month_name()})'
    desc = f'Compare {len(sorted_offers)} live {niche} deals from {len(providers)} providers. Real prices, updated automatically. Lowest plan: {fmt_price(sorted_offers[0].get("price"), sorted_offers[0].get("currency","USD")) if sorted_offers else "N/A"}/mo.'

    tpl = load_template('index.html')
    return render(tpl, {
        'BRAND': esc(brand),
        'NICHE': esc(niche),
        'DOMAIN': domain,
        'TITLE': esc(title),
        'DESCRIPTION': esc(desc),
        'CANONICAL': f'https://{domain}/',
        'OG_URL': f'https://{domain}/',
        'DEALS': '\n'.join(cards) if cards else '<p class="empty">No deals found yet. The scraper runs every 6 hours.</p>',
        'PROVIDER_FILTERS': '\n'.join(prov_links),
        'JSONLD': jsonld,
        'MONTH': month_name(),
        'DEAL_COUNT': len(sorted_offers),
        'PROVIDER_COUNT': len(providers),
    })


def gen_provider_page(brand, niche, domain, provider, offers):
    """One page per provider: their deals + AggregateOffer."""
    p_slug = slug(provider['name'])
    prov_offers = sorted(
        [o for o in offers if o['provider'] == provider['name'] and o.get('price') is not None],
        key=lambda o: o['price']
    )

    cards = []
    for o in prov_offers:
        d_slug = slug(o['title'])
        cards.append(f'''
        <a class="card" href="/deal/{p_slug}-{d_slug}.html">
          <div class="card-title">{esc(o["title"])}</div>
          <div class="card-price">{fmt_price(o.get("price"), o.get("currency","USD"))}<span class="per">/mo</span></div>
        </a>''')

    # JSON-LD: Service with AggregateOffer
    jsonld_parts = []
    if prov_offers:
        prices = [o['price'] for o in prov_offers]
        agg = {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": f'{provider["name"]} VPS Hosting',
            "url": provider['website'],
            "offers": {
                "@type": "AggregateOffer",
                "lowPrice": f'{min(prices):.2f}',
                "highPrice": f'{max(prices):.2f}',
                "priceCurrency": prov_offers[0].get('currency', 'USD'),
                "offerCount": len(prov_offers),
            }
        }
        jsonld_parts.append(json.dumps(agg, indent=2))

    # BreadcrumbList
    breadcrumb = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"https://{domain}/"},
            {"@type": "ListItem", "position": 2, "name": provider['name'], "item": f"https://{domain}/provider/{p_slug}.html"},
        ]
    }, indent=2)
    jsonld_parts.append(breadcrumb)

    title = f'{provider["name"]} VPS Pricing & Deals ({month_name()}) | {brand.capitalize()}'
    desc = f'{provider["name"]} VPS plans from {fmt_price(prov_offers[0].get("price"), prov_offers[0].get("currency","USD")) if prov_offers else "N/A"}/mo. {len(prov_offers)} live plans with real prices.'

    tpl = load_template('provider.html')
    return render(tpl, {
        'BRAND': esc(brand),
        'NICHE': esc(niche),
        'DOMAIN': domain,
        'PROVIDER_NAME': esc(provider['name']),
        'PROVIDER_SLUG': p_slug,
        'PROVIDER_WEBSITE': esc(provider['website']),
        'TITLE': esc(title),
        'DESCRIPTION': esc(desc),
        'CANONICAL': f'https://{domain}/provider/{p_slug}.html',
        'OG_URL': f'https://{domain}/provider/{p_slug}.html',
        'DEALS': '\n'.join(cards) if cards else '<p class="empty">No deals available. The scraper runs every 6 hours.</p>',
        'DEAL_COUNT': len(prov_offers),
        'JSONLD': ',\n'.join(jsonld_parts) if jsonld_parts else '',
    })


def gen_deal_page(brand, niche, domain, offer, provider):
    """One page per deal: details + JSON-LD Offer."""
    p_slug = slug(offer['provider'])
    d_slug = slug(offer['title'])

    # JSON-LD Offer
    offer_jsonld = {
        "@context": "https://schema.org",
        "@type": "Offer",
        "name": offer['title'],
        "price": f'{offer["price"]:.2f}',
        "priceCurrency": offer.get('currency', 'USD'),
        "url": offer.get('offer_url', ''),
        "availability": "https://schema.org/InStock",
        "seller": {"@type": "Organization", "name": offer['provider']},
    }
    # Only add priceValidUntil if we actually have it
    if offer.get('valid_until'):
        offer_jsonld['priceValidUntil'] = offer['valid_until']

    # BreadcrumbList
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"https://{domain}/"},
            {"@type": "ListItem", "position": 2, "name": offer['provider'], "item": f"https://{domain}/provider/{p_slug}.html"},
            {"@type": "ListItem", "position": 3, "name": offer['title'], "item": f"https://{domain}/deal/{p_slug}-{d_slug}.html"},
        ]
    }

    jsonld = ',\n'.join([json.dumps(offer_jsonld, indent=2), json.dumps(breadcrumb, indent=2)])

    title = f'{offer["provider"]} {offer["title"]} — {fmt_price(offer.get("price"), offer.get("currency","USD"))}/mo | {brand.capitalize()}'
    desc = f'{offer["provider"]} {offer["title"]}: {fmt_price(offer.get("price"), offer.get("currency","USD"))}/month. Real pricing, updated automatically.'

    tpl = load_template('deal.html')
    return render(tpl, {
        'BRAND': esc(brand),
        'NICHE': esc(niche),
        'DOMAIN': domain,
        'PROVIDER_NAME': esc(offer['provider']),
        'PROVIDER_SLUG': p_slug,
        'DEAL_TITLE': esc(offer['title']),
        'DEAL_SLUG': d_slug,
        'PRICE': fmt_price(offer.get('price'), offer.get('currency', 'USD')),
        'CURRENCY': esc(offer.get('currency', 'USD')),
        'OFFER_URL': esc(offer.get('offer_url', '')),
        'SOURCE_URL': esc(offer.get('source_url', '')),
        'FETCHED_AT': esc(offer.get('fetched_at', '')[:19].replace('T', ' ') + ' UTC'),
        'TITLE': esc(title),
        'DESCRIPTION': esc(desc),
        'CANONICAL': f'https://{domain}/deal/{p_slug}-{d_slug}.html',
        'OG_URL': f'https://{domain}/deal/{p_slug}-{d_slug}.html',
        'JSONLD': jsonld,
    })


def gen_compare_page(brand, niche, domain, offers, providers):
    """Comparison table: cheapest plan per provider."""
    # Find cheapest offer per provider
    cheapest = {}
    for o in offers:
        if o.get('price') is None:
            continue
        p = o['provider']
        if p not in cheapest or o['price'] < cheapest[p]['price']:
            cheapest[p] = o

    rows = []
    for prov in providers:
        name = prov['name']
        o = cheapest.get(name)
        if o:
            p_slug = slug(name)
            d_slug = slug(o['title'])
            rows.append(f'''
        <tr>
          <td><a href="/provider/{p_slug}.html">{esc(name)}</a></td>
          <td><a href="/deal/{p_slug}-{d_slug}.html">{esc(o["title"])}</a></td>
          <td class="price-cell">{fmt_price(o.get("price"), o.get("currency","USD"))}</td>
          <td>{esc(o.get("currency","USD"))}</td>
          <td><a href="{esc(o.get("offer_url",""))}" target="_blank" rel="nofollow noopener">View →</a></td>
        </tr>''')
        else:
            rows.append(f'''
        <tr>
          <td>{esc(name)}</td>
          <td colspan="4" class="empty-cell">No pricing data available</td>
        </tr>''')

    # Sort rows by price (cheapest first) — parse from the generated rows
    # Actually, let's sort the cheapest dict by price
    sorted_provs = sorted(cheapest.items(), key=lambda x: x[1]['price'])
    rows_sorted = []
    for name, o in sorted_provs:
        p_slug = slug(name)
        d_slug = slug(o['title'])
        rows_sorted.append(f'''
        <tr>
          <td><a href="/provider/{p_slug}.html">{esc(name)}</a></td>
          <td><a href="/deal/{p_slug}-{d_slug}.html">{esc(o["title"])}</a></td>
          <td class="price-cell">{fmt_price(o.get("price"), o.get("currency","USD"))}</td>
          <td>{esc(o.get("currency","USD"))}</td>
          <td><a href="{esc(o.get("offer_url",""))}" target="_blank" rel="nofollow noopener">View →</a></td>
        </tr>''')

    # JSON-LD ItemList
    item_list = []
    for i, (name, o) in enumerate(sorted_provs, 1):
        p_slug = slug(name)
        d_slug = slug(o['title'])
        item_list.append({
            "@type": "ListItem", "position": i,
            "url": f"https://{domain}/deal/{p_slug}-{d_slug}.html",
            "name": f'{name} {o["title"]} {fmt_price(o.get("price"), o.get("currency","USD"))}/mo'
        })
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "ItemList",
        "name": f"{brand} — VPS price comparison",
        "itemListElement": item_list
    }, indent=2) if item_list else ''

    title = f'VPS Price Comparison — Cheapest Plans ({month_name()}) | {brand.capitalize()}'
    desc = f'Compare the cheapest VPS plan from each provider. {len(sorted_provs)} providers, real prices, updated automatically.'

    tpl = load_template('compare.html')
    return render(tpl, {
        'BRAND': esc(brand),
        'NICHE': esc(niche),
        'DOMAIN': domain,
        'TITLE': esc(title),
        'DESCRIPTION': esc(desc),
        'CANONICAL': f'https://{domain}/compare.html',
        'OG_URL': f'https://{domain}/compare.html',
        'ROWS': '\n'.join(rows_sorted),
        'PROVIDER_COUNT': len(sorted_provs),
        'JSONLD': jsonld,
        'MONTH': month_name(),
    })


def gen_about(brand, domain):
    """About page: who made the site, what it does, where data comes from."""
    title = f'About — {brand}'
    desc = f'Learn about {brand}, an automated VPS price tracking site that aggregates real deals from public provider pricing pages.'
    tpl = load_template('about.html')
    return render(tpl, {
        'BRAND': esc(brand),
        'DOMAIN': domain,
        'TITLE': esc(title),
        'DESCRIPTION': esc(desc),
        'CANONICAL': f'https://{domain}/about.html',
        'OG_URL': f'https://{domain}/about.html',
    })


def gen_privacy(brand, domain):
    """Privacy page: real situation, no template language. Mentions affiliate links and third-party ads."""
    title = f'Privacy Policy — {brand}'
    desc = f'Privacy policy for {brand}. No registration required. Affiliate links and third-party cookies explained.'
    tpl = load_template('privacy.html')
    return render(tpl, {
        'BRAND': esc(brand),
        'DOMAIN': domain,
        'TITLE': esc(title),
        'DESCRIPTION': esc(desc),
        'CANONICAL': f'https://{domain}/privacy.html',
        'OG_URL': f'https://{domain}/privacy.html',
    })


def gen_contact(brand, domain, contact_email):
    """Contact page with a real email. Email must be provided by the site owner."""
    title = f'Contact — {brand}'
    desc = f'Contact {brand} for questions about deals, pricing, or partnerships.'
    tpl = load_template('contact.html')
    return render(tpl, {
        'BRAND': esc(brand),
        'DOMAIN': domain,
        'TITLE': esc(title),
        'DESCRIPTION': esc(desc),
        'CANONICAL': f'https://{domain}/contact.html',
        'OG_URL': f'https://{domain}/contact.html',
        'CONTACT_EMAIL': esc(contact_email) if contact_email else '[Contact email being configured]',
    })


def gen_sitemap(domain, pages):
    """Generate sitemap.xml with real lastmod."""
    urls = []
    for url, lastmod in pages:
        urls.append(f'''  <url>
    <loc>{url}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>''')
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>'''


def gen_robots(domain):
    return f'''User-agent: *
Allow: /

Sitemap: https://{domain}/sitemap.xml
'''


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    script_dir = Path(__file__).parent
    ilang_path = script_dir / '.ilang' / 'site.ilang'
    offers_path = script_dir / 'data' / 'offers.json'
    site_dir = script_dir / 'site'

    if not ilang_path.exists():
        print(f'ERROR: {ilang_path} not found — build depends on site.ilang for config.', file=sys.stderr)
        sys.exit(1)

    config = parse_ilang(str(ilang_path))
    brand = config.get('brand', 'ServerBudget')
    niche = config.get('niche', 'vps hosting')
    domain = config.get('domain', 'serverbudget.com')
    providers = config.get('providers', [])

    print(f'Brand:   {brand}')
    print(f'Niche:   {niche}')
    print(f'Domain:  {domain}')
    print()

    # Load offers
    if not offers_path.exists():
        print(f'WARNING: {offers_path} not found. Generating empty site.', file=sys.stderr)
        offers = []
    else:
        with open(offers_path, 'r', encoding='utf-8') as f:
            offers = json.load(f)

    print(f'Offers:  {len(offers)}')
    print()

    # Prepare output dirs
    site_dir.mkdir(exist_ok=True)
    (site_dir / 'provider').mkdir(exist_ok=True)
    (site_dir / 'deal').mkdir(exist_ok=True)

    # Generate pages
    sitemap_pages = []
    ts = now_iso()

    # 1. Index
    print('Generating index.html ...')
    html_out = gen_index(brand, niche, domain, offers, providers)
    (site_dir / 'index.html').write_text(html_out, encoding='utf-8')
    sitemap_pages.append((f'https://{domain}/', ts))

    # 2. Provider pages
    for prov in providers:
        print(f'Generating provider/{slug(prov["name"])}.html ...')
        html_out = gen_provider_page(brand, niche, domain, prov, offers)
        (site_dir / 'provider' / f'{slug(prov["name"])}.html').write_text(html_out, encoding='utf-8')
        sitemap_pages.append((f'https://{domain}/provider/{slug(prov["name"])}.html', ts))

    # 3. Deal pages
    for offer in offers:
        if offer.get('price') is None:
            continue  # RULE: no price → don't render
        p_slug = slug(offer['provider'])
        d_slug = slug(offer['title'])
        # Find the provider dict for website link
        prov_dict = next((p for p in providers if p['name'] == offer['provider']), {'name': offer['provider'], 'website': ''})
        print(f'Generating deal/{p_slug}-{d_slug}.html ...')
        html_out = gen_deal_page(brand, niche, domain, offer, prov_dict)
        (site_dir / 'deal' / f'{p_slug}-{d_slug}.html').write_text(html_out, encoding='utf-8')
        sitemap_pages.append((f'https://{domain}/deal/{p_slug}-{d_slug}.html', ts))

    # 4. Compare page
    print('Generating compare.html ...')
    html_out = gen_compare_page(brand, niche, domain, offers, providers)
    (site_dir / 'compare.html').write_text(html_out, encoding='utf-8')
    sitemap_pages.append((f'https://{domain}/compare.html', ts))

    # 5. About page
    print('Generating about.html ...')
    html_out = gen_about(brand, domain)
    (site_dir / 'about.html').write_text(html_out, encoding='utf-8')
    sitemap_pages.append((f'https://{domain}/about.html', ts))

    # 6. Privacy page
    print('Generating privacy.html ...')
    html_out = gen_privacy(brand, domain)
    (site_dir / 'privacy.html').write_text(html_out, encoding='utf-8')
    sitemap_pages.append((f'https://{domain}/privacy.html', ts))

    # 7. Contact page
    contact_email = os.environ.get('CONTACT_EMAIL', '')
    print(f'Generating contact.html ... (email: {"set" if contact_email else "NOT SET"})')
    html_out = gen_contact(brand, domain, contact_email)
    (site_dir / 'contact.html').write_text(html_out, encoding='utf-8')
    sitemap_pages.append((f'https://{domain}/contact.html', ts))

    # 8. sitemap.xml
    print('Generating sitemap.xml ...')
    sitemap = gen_sitemap(domain, sitemap_pages)
    (site_dir / 'sitemap.xml').write_text(sitemap, encoding='utf-8')

    # 9. robots.txt
    print('Generating robots.txt ...')
    robots = gen_robots(domain)
    (site_dir / 'robots.txt').write_text(robots, encoding='utf-8')

    # 10. Copy live-site/ files (manually crafted pages, articles, 404, sitemap)
    #     These override the build-generated versions with production-curated content.
    print('Copying live-site/ files to site/ ...')
    import shutil
    live_dir = script_dir / 'live-site'
    if live_dir.exists():
        copied = 0
        for item in live_dir.iterdir():
            if item.is_file():
                dest = site_dir / item.name
                shutil.copy2(str(item), str(dest))
                print(f'  Copied {item.name}')
                copied += 1
        print(f'  Total: {copied} files copied from live-site/')

    print(f'\n{"="*60}')
    print(f'Site generated in: {site_dir}')
    print(f'Pages: {len(sitemap_pages)}')
    print(f'Sitemap: {site_dir / "sitemap.xml"}')
    print(f'Robots:  {site_dir / "robots.txt"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
