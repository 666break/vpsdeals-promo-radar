#!/usr/bin/env python3
# ::ILANG [TYPE:component][COMPONENT:scraper][LANG:py]
# RESPONSIBILITY: Read .ilang/site.ilang for provider list, fetch each provider's public offer page,
#                 extract real pricing data, write data/offers.json. Generic scraper driven by site.ilang.
# BOUNDARY: Only scrape public pages listed in site.ilang. Never fabricate prices or offers.
#           Skip fields that can't be scraped (per RULE). Never use anti-bot evasion.

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ─── ILANG PARSER ───────────────────────────────────────────────────────────

def parse_ilang(filepath):
    """Parse .ilang/site.ilang and return config dict with providers, fields, brand, niche, domain."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    config = {'providers': [], 'fields': [], 'rules': [], 'boundary': ''}

    # Extract STATE block
    state_match = re.search(
        r'::STATE\{@SITE,\s*brand:([^,]+),\s*niche:([^,]+),\s*domain:([^]}]+)',
        content
    )
    if state_match:
        config['brand'] = state_match.group(1).strip()
        config['niche'] = state_match.group(2).strip()
        config['domain'] = state_match.group(3).strip()

    # Extract PROVIDERS module
    providers_section = re.search(
        r'::MODULE\{PROVIDERS[^}]*\}\s*\n(.*?)(?=::MODULE\{|::RULE\{|::BOUNDARY\{|$)',
        content, re.DOTALL
    )
    if providers_section:
        for line in providers_section.group(1).strip().split('\n'):
            line = line.strip()
            if line and '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    affiliate = parts[3].strip() if len(parts) > 3 else ''
                    config['providers'].append({
                        'name': parts[0],
                        'website': parts[1],
                        'offer_url': parts[2],
                        'affiliate_url': affiliate if affiliate else parts[2],
                    })

    # Extract FIELDS module
    fields_section = re.search(
        r'::MODULE\{FIELDS[^}]*\}\s*\n(.*?)(?=::MODULE\{|::RULE\{|::BOUNDARY\{|$)',
        content, re.DOTALL
    )
    if fields_section:
        config['fields'] = fields_section.group(1).strip().split()

    # Extract RULES
    for rule_match in re.finditer(r'::RULE\{([^}]+)\}', content):
        config['rules'].append(rule_match.group(1).strip())

    # Extract BOUNDARY
    boundary_match = re.search(r'::BOUNDARY\{([^}]+)\}', content)
    if boundary_match:
        config['boundary'] = boundary_match.group(1).strip()

    return config


# ─── SCRAPE HELPERS ─────────────────────────────────────────────────────────

CURRENCY_MAP = {'$': 'USD', '€': 'EUR', '£': 'GBP'}
PRICE_RE = re.compile(r'([$€£])\s*(\d+(?:[.,]\d+)?)\s*/?\s*(?:mo|month|mo\.?)', re.IGNORECASE)
HEADINGS = ['h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b']
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'


def fetch(url):
    """Fetch a URL and return (text, status_code) or (None, error)."""
    try:
        resp = requests.get(url, timeout=30, headers={'User-Agent': UA})
        resp.raise_for_status()
        return resp.text, resp.status_code
    except Exception as e:
        return None, str(e)


def extract_jsonld_offers(html, provider_name, offer_url, website):
    """Try to extract offers from JSON-LD structured data in the page."""
    offers = []
    soup = BeautifulSoup(html, 'html.parser')

    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string)
        except (json.JSONDecodeError, TypeError):
            continue

        # Handle both single objects and arrays
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            _type = item.get('@type', '')
            if _type in ('Product', 'Service'):
                offers_inner = item.get('offers', {})
                if isinstance(offers_inner, dict):
                    offers_inner = offers_inner.get('offers', [offers_inner])
                for o in offers_inner if isinstance(offers_inner, list) else []:
                    price = o.get('price') or o.get('lowPrice')
                    currency = o.get('priceCurrency', 'USD')
                    if price:
                        offers.append({
                            'provider': provider_name,
                            'title': item.get('name', f'{provider_name} VPS'),
                            'price': float(str(price).replace(',', '')),
                            'currency': currency,
                            'offer_url': o.get('url', offer_url),
                            'valid_until': o.get('priceValidUntil') or o.get('validThrough'),
                            'source_url': offer_url,
                            'fetched_at': datetime.now(timezone.utc).isoformat(),
                        })
            elif _type == 'Offer':
                price = item.get('price') or item.get('lowPrice')
                currency = item.get('priceCurrency', 'USD')
                if price:
                    offers.append({
                        'provider': provider_name,
                        'title': item.get('name', f'{provider_name} VPS'),
                        'price': float(str(price).replace(',', '')),
                        'currency': currency,
                        'offer_url': item.get('url', offer_url),
                        'valid_until': item.get('priceValidUntil') or item.get('validThrough'),
                        'source_url': offer_url,
                        'fetched_at': datetime.now(timezone.utc).isoformat(),
                    })
    return offers


def extract_price_from_html(html, provider_name, offer_url, website):
    """Fallback: scan page text for price patterns near headings."""
    offers = []
    soup = BeautifulSoup(html, 'html.parser')
    seen_prices = set()

    # Strategy 1: find headings near prices
    for heading in soup.find_all(HEADINGS):
        htext = heading.get_text(strip=True)
        if not htext or len(htext) > 80:
            continue
        # Look in the parent/container for a price
        container = heading.find_parent()
        if not container:
            continue
        ctext = container.get_text(separator=' ')
        match = PRICE_RE.search(ctext)
        if match:
            sym, val = match.group(1), match.group(2).replace(',', '.')
            key = (provider_name, val)
            if key in seen_prices:
                continue
            seen_prices.add(key)
            offers.append({
                'provider': provider_name,
                'title': htext,
                'price': float(val),
                'currency': CURRENCY_MAP.get(sym, 'USD'),
                'offer_url': offer_url,
                'valid_until': None,
                'source_url': offer_url,
                'fetched_at': datetime.now(timezone.utc).isoformat(),
            })

    # Strategy 2: if nothing found, scan full text for price mentions
    if not offers:
        full_text = soup.get_text(separator=' ')
        for match in PRICE_RE.finditer(full_text):
            sym, val = match.group(1), match.group(2).replace(',', '.')
            key = (provider_name, val)
            if key in seen_prices:
                continue
            seen_prices.add(key)
            # Try to grab nearby text as a title
            start = max(0, match.start() - 60)
            snippet = re.sub(r'\s+', ' ', full_text[start:match.start()]).strip()[-40:]
            offers.append({
                'provider': provider_name,
                'title': snippet if snippet else f'{provider_name} VPS',
                'price': float(val),
                'currency': CURRENCY_MAP.get(sym, 'USD'),
                'offer_url': offer_url,
                'valid_until': None,
                'source_url': offer_url,
                'fetched_at': datetime.now(timezone.utc).isoformat(),
            })

    return offers


def scrape_hetzner_api(offer_url, provider_name, website):
    """Fetch Hetzner public pricing API (JSON) and extract server types."""
    offers = []
    text, err = fetch(offer_url)
    if text is None:
        print(f'  [{provider_name}] Fetch error: {err}', file=sys.stderr)
        return offers

    try:
        data = json.loads(text)
        pricing = data.get('pricing', {})
        currency = pricing.get('currency', 'EUR')

        for st in pricing.get('server_type', []):
            name = st.get('name', '')
            desc = st.get('description', '')
            prices = st.get('prices', [])
            if not prices:
                continue
            monthly = prices[0].get('price_monthly', {})
            price_gross = monthly.get('gross')
            if price_gross:
                offers.append({
                    'provider': provider_name,
                    'title': f'{name} — {desc}' if desc else name,
                    'price': float(price_gross),
                    'currency': currency,
                    'offer_url': f'{website}/cloud',
                    'valid_until': None,
                    'source_url': offer_url,
                    'fetched_at': datetime.now(timezone.utc).isoformat(),
                })
    except (json.JSONDecodeError, KeyError) as e:
        print(f'  [{provider_name}] Parse error: {e}', file=sys.stderr)

    return offers


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    script_dir = Path(__file__).parent
    ilang_path = script_dir / '.ilang' / 'site.ilang'

    if not ilang_path.exists():
        print(f'ERROR: {ilang_path} not found — scraper depends on site.ilang for config.', file=sys.stderr)
        sys.exit(1)

    config = parse_ilang(str(ilang_path))

    print(f'Brand:   {config.get("brand", "?")}')
    print(f'Niche:   {config.get("niche", "?")}')
    print(f'Domain:  {config.get("domain", "?")}')
    print(f'Providers: {len(config["providers"])}')
    print(f'Fields:  {config.get("fields", [])}')
    print()

    all_offers = []

    for prov in config['providers']:
        name = prov['name']
        offer_url = prov['offer_url']
        website = prov['website']

        print(f'Scraping {name} ...')
        print(f'  URL: {offer_url}')

        # Hetzner uses a JSON API — special handler
        if 'api.hetzner.com' in offer_url:
            offers = scrape_hetzner_api(offer_url, name, website)
        else:
            html, err = fetch(offer_url)
            if html is None:
                print(f'  Fetch error: {err}', file=sys.stderr)
                offers = []
            else:
                # Try JSON-LD first, then fallback to text scan
                offers = extract_jsonld_offers(html, name, offer_url, website)
                if not offers:
                    offers = extract_price_from_html(html, name, offer_url, website)

        # Filter out zero/negative prices (scraping artifacts, not real offers)
        offers = [o for o in offers if o.get('price') and o['price'] > 0]

        # Deduplicate by (provider, price) keeping the first
        seen = set()
        deduped = []
        for o in offers:
            key = (o['provider'], o.get('price'))
            if key not in seen:
                seen.add(key)
                deduped.append(o)
        offers = deduped

        print(f'  → {len(offers)} offers extracted')
        for o in offers[:5]:
            print(f'    {o["title"][:50]:50s}  {o.get("currency","?")} {o.get("price","?")}')
        if len(offers) > 5:
            print(f'    ... and {len(offers)-5} more')

        all_offers.extend(offers)

    # Write offers.json
    data_dir = script_dir / 'data'
    data_dir.mkdir(exist_ok=True)
    output_path = data_dir / 'offers.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_offers, f, indent=2, ensure_ascii=False)

    print(f'\n{"="*60}')
    print(f'Total offers: {len(all_offers)}')
    print(f'Written to: {output_path}')

    # Check RULE compliance
    without_price = [o for o in all_offers if 'price' not in o or o['price'] is None]
    if without_price:
        print(f'WARNING: {len(without_price)} offers have no price (should have been skipped per RULE)')

    return 0


if __name__ == '__main__':
    sys.exit(main())
