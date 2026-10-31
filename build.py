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
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import claim_check

# ─── GENERATED-PAGE MANIFEST ─────────────────────────────────────────────────
# Pages build.py produces from data/offers.json and writes straight into the deploy
# source (live-site/). verify_deploy_dir() whitelists exactly these: a page carrying
# an AggregateOffer that is NOT listed here did not come from the data, so the deploy
# is blocked instead of publishing a hand-written price range.
# Lives in data/ (tracked, not gitignored) so CI reads the same list the build wrote.
GENERATED_MANIFEST = Path('data') / 'generated_pages.json'

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


# ─── OFFER CLASSIFICATION: plan vs add-on ───────────────────────────────────
# Some scraped prices are VPS *add-ons* (automatic backup, snapshots), not servers:
# they are billed on top of a plan and cannot be bought on their own, so they must
# never set a provider page's "from" price. Two sources of truth, in this order:
#   1. an explicit `kind` field on the offer ("plan" / "addon"); legacy `type` works too
#   2. the offer title: words that only ever describe an option, never a server
# Deliberately NOT a price threshold: an add-on is not "anything cheaper than the
# cheapest plan", and a cheap plan is still a plan.
# Titles that only ever describe a VPS option, never a server. Kept narrow on
# purpose: a bare "backup" is ambiguous — DigitalOcean sells "Database & Backups"
# as its own product — so "backup" only counts when the title also says
# automatic / premium / manual / option.
ADDON_TITLE_WORDS = ('add-on', 'addon', 'snapshot')
ADDON_BACKUP_WORDS = ('automatic', 'premium', 'manual', 'option')


def offer_kind(offer):
    """Return 'plan' or 'addon' for one offer from offers.json."""
    explicit = str(offer.get('kind') or offer.get('type') or '').strip().lower()
    if explicit in ('plan', 'vps', 'server'):
        return 'plan'
    if explicit in ('addon', 'add-on', 'option'):
        return 'addon'
    title = str(offer.get('title') or offer.get('name') or '').lower()
    if any(w in title for w in ADDON_TITLE_WORDS):
        return 'addon'
    if 'backup' in title and any(w in title for w in ADDON_BACKUP_WORDS):
        return 'addon'
    return 'plan'


def check_aggregate(agg_offer, plan_offers, provider_name):
    """Build-time guard: an AggregateOffer may describe the plans and only the plans.

    Raises SystemExit — so the build dies instead of shipping a page whose "from"
    price is an add-on — when lowPrice or offerCount disagrees with the plan list.
    """
    expected_low = round(min(float(o['price']) for o in plan_offers), 2)
    got_low = round(float(agg_offer['lowPrice']), 2)
    if got_low != expected_low:
        raise SystemExit(
            f'BUILD ABORTED: {provider_name} AggregateOffer.lowPrice={got_low:.2f} but the '
            f'cheapest plan is {expected_low:.2f}. An add-on price is leaking into the plan '
            f'range — check offer_kind() and the offers.json data.')
    if int(agg_offer['offerCount']) != len(plan_offers):
        raise SystemExit(
            f'BUILD ABORTED: {provider_name} AggregateOffer.offerCount={agg_offer["offerCount"]} '
            f'but there are {len(plan_offers)} plans. Add-ons must be separate Offer entries, '
            f'not counted in the plan aggregate.')


def _jsonld_docs(html_text):
    """Yield every JSON object found in ld+json blocks (a block may hold several)."""
    for block in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html_text, re.S):
        dec = json.JSONDecoder()
        i = 0
        while True:
            m = re.search(r'\{', block[i:])
            if not m:
                break
            start = i + m.start()
            try:
                obj, end = dec.raw_decode(block[start:])
            except ValueError:
                i = start + 1
                continue
            yield obj
            i = start + end


def _aggregate_pairs(doc):
    """Yield (aggregate_offer, sibling_offers) pairs from one JSON-LD document."""
    offers = doc.get('offers')
    if isinstance(offers, dict):
        if offers.get('@type') == 'AggregateOffer':
            yield offers, []
    elif isinstance(offers, list):
        aggs = [o for o in offers if isinstance(o, dict) and o.get('@type') == 'AggregateOffer']
        sibs = [o for o in offers if isinstance(o, dict) and o.get('@type') == 'Offer']
        for a in aggs:
            yield a, sibs


def _page_price_rows(html_text):
    """[(price, is_addon)] from the page's own price table, in document order.

    A row is an add-on row when it carries the visible add-on marker
    (<span class="addon-tag">...), which is exactly what tells a reader it is not
    a server. Rows without a class="price" cell are ignored.
    """
    rows = []
    for row in re.findall(r'<tr[^>]*>(.*?)</tr>', html_text, re.S | re.I):
        m = re.search(r'class="price"[^>]*>\s*\$?\s*([0-9]+(?:\.[0-9]+)?)', row)
        if not m:
            continue
        rows.append((float(m.group(1)), 'addon-tag' in row))
    return rows


def load_generated_manifest(site_dir, manifest_path=None):
    """Read the whitelist of pages build.py generated from data/offers.json.

    A missing or malformed manifest is a hard failure, never a warning: without the
    list the gate cannot tell a generated page from a hand-written one, and "cannot
    tell" must never be treated as "fine". An empty list is legitimate — it means no
    page is data-generated, so every AggregateOffer page gets blocked, which is the
    safe direction.
    """
    root = Path(site_dir)
    path = Path(manifest_path) if manifest_path else root.parent / GENERATED_MANIFEST
    if not path.is_file():
        raise SystemExit(
            f'DEPLOY BLOCKED: generated-page manifest not found at {path}. Run build.py first — '
            f'the deploy gate refuses to run without its whitelist.')
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        raise SystemExit(f'DEPLOY BLOCKED: generated-page manifest {path} is unreadable ({e}).')
    pages = data.get('pages') if isinstance(data, dict) else None
    if not isinstance(pages, list):
        raise SystemExit(
            f'DEPLOY BLOCKED: generated-page manifest {path} has no "pages" list — the whitelist '
            f'is what makes the check meaningful, so a manifest without it is broken, not empty.')
    allowed = {str(p).replace('\\', '/').lstrip('/') for p in pages}
    return allowed, path


CANONICAL_RE = re.compile(r'<link\b[^>]*\brel\s*=\s*["\']canonical["\'][^>]*>', re.I)
HREF_RE = re.compile(r'\bhref\s*=\s*["\']([^"\']+)["\']', re.I)
LOC_RE = re.compile(r'<loc>\s*([^<\s]+)\s*</loc>', re.I)


def clean_path(rel):
    """The one public URL path for a page file, relative to the deploy dir root."""
    rel = rel[:-5] if rel.endswith('.html') else rel
    return '/' if rel == 'index' else '/' + rel


def sync_redirect_rules(site_dir):
    """Give every .html file its own exact 301 to the extensionless twin.

    Cloudflare Pages answers a bare /page.html with a 308 of its own when no rule
    matches. A 308 is permanent but it is not the 301 this site promises, and it
    means the rule set — not the redirect table — is deciding the address. So the
    table is kept complete here, in sorted position inside the existing block, and
    only rules that are missing are added: an existing line is never rewritten.
    """
    root = Path(site_dir)
    path = root / '_redirects'
    if not path.is_file():
        print('  redirects: no _redirects file, nothing to sync')
        return 0
    text = path.read_bytes().decode('utf-8')
    eol = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(eol)

    have = set()
    for line in lines:
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        parts = s.split()
        if len(parts) >= 3 and parts[0].startswith('/'):
            have.add(parts[0])

    is_rule = lambda s: bool(re.match(r'^/\S+\.html\s+/\S*\s+301\s*$', s.strip()))
    block = [i for i, line in enumerate(lines) if is_rule(line)]
    if not block:
        print('  redirects: no .html block found, nothing to sync')
        return 0
    # Only the FIRST contiguous run is the .html twin block; later .html rules
    # belong to page merges and point somewhere else, so never insert among them.
    lo = block[0]
    hi = lo
    while hi + 1 < len(lines) and is_rule(lines[hi + 1]):
        hi += 1

    wanted = []
    for page in sorted(root.rglob('*.html')):
        rel = page.relative_to(root).as_posix()
        src_path = '/' + rel
        if src_path in have:
            continue
        wanted.append(f'{src_path}  {clean_path(rel)}  301')
    if not wanted:
        print(f'  redirects: all {len(have)} rule(s) present, nothing added')
        return 0

    for rule in wanted:
        src_path = rule.split()[0]
        pos = hi
        for i in range(lo, hi + 1):
            parts = lines[i].strip().split()
            if parts and parts[0] > src_path:
                pos = i - 1
                break
        lines.insert(pos + 1, rule)
        lo, hi = min(lo, pos + 1), max(hi, pos + 1)

    path.write_bytes(eol.join(lines).encode('utf-8'))
    for rule in wanted:
        print(f'  redirects: added {rule}')
    return len(wanted)


def verify_one_url_per_page(site_dir):
    """One page, one address. Every other form of that address must 301 to it.

    Four separate places can hand a reader (or Google) a second address for the
    same page, so all four are checked before upload, and any hit is a SystemExit:

      1. sitemap.xml    — a <loc> ending in .html publishes the wrong form
      2. canonical      — exactly one per page, never .html, pointing at that page
      3. internal links — href="/x.html" keeps the old form alive in the crawl
      4. _redirects     — every .html file needs its exact 301; without one Pages
                          answers with its own 308 and the second form survives

    A missing sitemap, a missing _redirects, or a page with no canonical is a
    failure, never a warning: "cannot check" is not "fine".
    """
    root = Path(site_dir)
    problems = []

    sitemap = root / 'sitemap.xml'
    if not sitemap.is_file():
        problems.append('sitemap.xml is missing — the URL forms cannot be checked')
    else:
        text = sitemap.read_text(encoding='utf-8', errors='ignore')
        locs = LOC_RE.findall(text)
        if not locs:
            problems.append('sitemap.xml lists no <loc> — an empty sitemap is not a pass')
        for url in locs:
            if url.split('?')[0].split('#')[0].lower().endswith('.html'):
                problems.append(f'sitemap.xml lists the .html form: {url}  [file: sitemap.xml]')

    pages = sorted(root.rglob('*.html'))
    for page in pages:
        rel = page.relative_to(root).as_posix()
        text = page.read_text(encoding='utf-8', errors='ignore')
        tags = CANONICAL_RE.findall(text)
        want = clean_path(rel)
        if not tags:
            problems.append(f'no canonical link  [file: {rel}]')
        elif len(tags) > 1:
            problems.append(f'{len(tags)} canonical links, must be exactly one  [file: {rel}]')
        else:
            href = HREF_RE.search(tags[0])
            href = href.group(1) if href else ''
            if '.html' in href.split('?')[0].lower():
                problems.append(f'canonical points at the .html form: {href}  [file: {rel}]')
            else:
                path = re.sub(r'^https?://[^/]+', '', href).split('?')[0].split('#')[0]
                if path.rstrip('/') != want.rstrip('/'):
                    problems.append(f'canonical points at {path}, not at its own {want}  [file: {rel}]')
        for href in HREF_RE.findall(text):
            if href.startswith('/') and '.html' in href.split('?')[0].split('#')[0].lower():
                problems.append(f'internal link to the .html form: {href}  [file: {rel}]')

    redirects = root / '_redirects'
    if not redirects.is_file():
        problems.append('_redirects is missing — every .html address would fall back to a 308')
    else:
        have = set()
        for line in redirects.read_text(encoding='utf-8', errors='ignore').splitlines():
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            parts = s.split()
            if len(parts) >= 3 and parts[0].startswith('/') and parts[2] == '301':
                have.add(parts[0])
        for page in pages:
            rel = page.relative_to(root).as_posix()
            if '/' + rel not in have:
                problems.append(f'no exact 301 for /{rel} in _redirects  [file: _redirects]')

    if problems:
        raise SystemExit(
            'DEPLOY BLOCKED: one page must have one address, and these break that:\n  '
            + '\n  '.join(problems[:20])
            + (f'\n  ... and {len(problems) - 20} more' if len(problems) > 20 else ''))
    print(f'  one-url gate: {len(pages)} page(s), sitemap {len(LOC_RE.findall(sitemap.read_text(encoding="utf-8", errors="ignore")))} '
          f'loc(s) with 0 .html, 1 canonical each, 0 internal .html link, '
          f'{len(have)} exact 301 rule(s)')
    return True



def verify_deploy_dir(site_dir, manifest_path=None):
    """Deploy gate: no page may ship with an add-on price as its "from" price.

    Scans the files that are actually about to be uploaded (live-site/), not build
    output: prices that matter are the ones in the directory wrangler uploads.

    Two things are enforced, in this order:
      0. claims — every multiplier in prose must equal a pair of the amounts printed
         in the same sentence (0.02 tolerance), every "there is no such thing"
         sentence must carry a signed entry in data/absence_claims.json, and no page
         may keep a claim that ledger has already refuted.
      0. whitelist — a page carrying an AggregateOffer must be listed in the
         generated-page manifest. Pages outside it were not built from the data, so
         nothing guarantees their price range is a server price; the deploy stops.
      1. numbers — plan evidence comes from sibling Offer entries in the same JSON-LD,
         else from the page's own price table (plans = rows without the visible add-on
         marker). Both feed the SAME check_aggregate() the generator calls — there is
         no second copy of the rule.

    No evidence, an unlisted page, or any mismatch raises SystemExit: the deploy
    fails, it never warns and continues.
    """
    root = Path(site_dir)
    if not root.is_dir():
        raise SystemExit(f'DEPLOY BLOCKED: {site_dir} is not a directory — refusing to deploy '
                         f'without running the AggregateOffer check.')
    pages = sorted(root.rglob('*.html'))
    if not pages:
        raise SystemExit(f'DEPLOY BLOCKED: {site_dir} holds no .html pages — an empty scan is '
                         f'not a pass.')
    verify_one_url_per_page(root)
    # A conclusion printed on a page has to be checkable from that page's own table.
    # Runs here, before wrangler is ever invoked, so a sentence that disagrees with
    # the data below it stops the upload instead of shipping.
    claim_check.verify_claim_consistency(root)
    allowed, manifest_file = load_generated_manifest(root, manifest_path)
    verified = []
    for page in pages:
        text = page.read_text(encoding='utf-8', errors='ignore')
        if 'AggregateOffer' not in text:
            continue
        rel = page.relative_to(root).as_posix()
        if rel not in allowed:
            raise SystemExit(
                f'DEPLOY BLOCKED: {rel} carries an AggregateOffer but is not in the generated-page '
                f'manifest ({manifest_file.name}). Only pages build.py generates from '
                f'data/offers.json may publish structured pricing — give this page a generator, '
                f'or drop its AggregateOffer.  [file: {rel}]')
        rows = _page_price_rows(text)
        table_plans = [{'price': p} for p, is_addon in rows if not is_addon]
        table_addons = [{'price': p} for p, is_addon in rows if is_addon]
        for doc in _jsonld_docs(text):
            for agg, siblings in _aggregate_pairs(doc):
                json_plans = [o for o in siblings if offer_kind(o) == 'plan' and o.get('price') is not None]
                json_addons = [o for o in siblings if offer_kind(o) == 'addon' and o.get('price') is not None]
                plans = json_plans or table_plans
                addons = json_addons or table_addons
                if not plans:
                    raise SystemExit(
                        f'DEPLOY BLOCKED: {rel} has an AggregateOffer but no plan prices to check '
                        f'it against (no plan Offer entries in the JSON-LD, and no unmarked rows '
                        f'in its price table).  [file: {rel}]')
                try:
                    check_aggregate(agg, plans, rel)
                except SystemExit as e:
                    raise SystemExit(f'{e}  [file: {rel}]')
                low = float(agg['lowPrice'])
                for a in addons:
                    if abs(low - float(a['price'])) < 0.005:
                        raise SystemExit(
                            f'DEPLOY BLOCKED: {rel} AggregateOffer.lowPrice={low:.2f} is an '
                            f'add-on price, not a server.  [file: {rel}]')
                verified.append((rel, agg.get('lowPrice'), agg.get('offerCount'),
                                 'json' if json_plans else 'table'))
    print(f'  deploy gate: scanned {len(pages)} html page(s) under {root.name}/, '
          f'verified {len(verified)} AggregateOffer(s), '
          f'whitelist {len(allowed)} generated page(s) from {manifest_file.name}')
    for rel, low, count, src in verified:
        print(f'    {rel}: lowPrice={low} offerCount={count} (plans from {src})')
    return verified


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

    # JSON-LD: Service whose AggregateOffer covers the PLANS only; add-ons are
    # separate Offer entries, never folded into lowPrice/highPrice/offerCount.
    plan_offers = [o for o in prov_offers if offer_kind(o) == 'plan']
    addon_offers = [o for o in prov_offers if offer_kind(o) == 'addon']

    jsonld_parts = []
    if prov_offers:
        offers_jsonld = []
        if plan_offers:
            prices = [o['price'] for o in plan_offers]
            agg_offer = {
                "@type": "AggregateOffer",
                "lowPrice": f'{min(prices):.2f}',
                "highPrice": f'{max(prices):.2f}',
                "priceCurrency": plan_offers[0].get('currency', 'USD'),
                "offerCount": len(plan_offers),
            }
            check_aggregate(agg_offer, plan_offers, provider['name'])
            offers_jsonld.append(agg_offer)
        for o in addon_offers:
            offers_jsonld.append({
                "@type": "Offer",
                "name": f'{provider["name"]} add-on - {o["title"]}',
                "price": f'{o["price"]:.2f}',
                "priceCurrency": o.get('currency', 'USD'),
                "description": ('VPS add-on billed on top of a VPS plan; it needs a plan to be '
                                'ordered first and is not a server, so it is not counted in the '
                                'plan price range.'),
            })
        agg = {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": f'{provider["name"]} VPS Hosting',
            "url": provider['website'],
            # one aggregate keeps the old single-object shape; with add-ons it is a list
            "offers": offers_jsonld[0] if len(offers_jsonld) == 1 else offers_jsonld,
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
    headline_offer = plan_offers[0] if plan_offers else (prov_offers[0] if prov_offers else None)
    desc = f'{provider["name"]} VPS plans from {fmt_price(headline_offer.get("price"), headline_offer.get("currency","USD")) if headline_offer else "N/A"}/mo. {len(prov_offers)} live plans with real prices.'

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


# ─── OVHCLOUD PAGE — GENERATED FROM DATA ─────────────────────────────────────
# This page used to be hand-written and copied into the build; its "from" price could
# therefore drift from offers.json and no build assertion ever saw it. It is now
# rendered from the same data as every other page. Layout, prose, table structure and
# the add-on markers are reproduced verbatim — only the source of the numbers changed.

NUM_WORDS = {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six'}


def _ovh_offers(offers):
    """(plans, addons) for OVHcloud, ordered by the data's own 'order' field."""
    ovh = [o for o in offers
           if o.get('provider') == 'OVHcloud' and o.get('price') is not None]

    def key(o):
        order = o.get('order')
        return (order if isinstance(order, int) else 999, float(o['price']))

    plans = sorted([o for o in ovh if offer_kind(o) == 'plan'], key=key)
    addons = sorted([o for o in ovh if offer_kind(o) == 'addon'], key=key)
    return plans, addons


def gen_ovhcloud_page(offers, domain):
    """Render provider-ovhcloud.html from data/offers.json."""
    plans, addons = _ovh_offers(offers)
    if not plans:
        raise SystemExit(
            'BUILD ABORTED: data/offers.json holds no OVHcloud plan offers — the generated '
            'OVHcloud page would ship with no server rows. Check scraper.py\'s OVHcloud handler '
            'and the carried-forward data.')

    # Price table: every row in price order. Add-ons carry the visible marker that tells
    # a reader the row is not a server.
    rows = []
    for o in sorted(plans + addons, key=lambda x: float(x['price'])):
        price = fmt_price(o['price'], o.get('currency', 'USD'))
        if offer_kind(o) == 'addon':
            label = f'OVHcloud add-on — {esc(o["title"])}'
            marker = '<br><span class="addon-tag">Add-on — needs a VPS plan</span>'
        else:
            label = f'From {price} /month'
            marker = ''
        rows.append(
            '        <tr>\n'
            f'          <td><a href="{esc(o.get("deal_url", "#"))}">{label}</a>{marker}</td>\n'
            f'          <td class="price">{price}</td>\n'
            f'          <td>{esc(o.get("currency", "USD"))}</td>\n'
            '        </tr>')

    # Structured data: the AggregateOffer covers the plans and only the plans.
    prices = [float(o['price']) for o in plans]
    agg = {
        "@type": "AggregateOffer",
        "lowPrice": f'{min(prices):.2f}',
        "highPrice": f'{max(prices):.2f}',
        "offerCount": len(plans),
        "priceCurrency": plans[0].get('currency', 'USD'),
        "description": (
            f'{NUM_WORDS.get(len(plans), str(len(plans)))} OVHcloud VPS plans, each priced per '
            'month: '
            + ', '.join(f'{o["title"]} ${float(o["price"]):.2f}' for o in plans)
            + '. VPS add-ons are listed as separate offers below and are not part of this price range.'),
    }
    check_aggregate(agg, plans, 'OVHcloud')

    offer_list = [agg]
    for o in addons:
        offer_list.append({
            "@type": "Offer",
            "name": f'OVHcloud add-on - {o["title"]}',
            "price": f'{float(o["price"]):.2f}',
            "priceCurrency": o.get('currency', 'USD'),
            "description": (
                f'VPS add-on billed on top of a VPS plan, from ${float(o["price"]):.2f} per month. '
                'It needs a VPS plan to be ordered first and is not a server, so it is not '
                'counted in the plan price range.'),
        })

    product = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "OVHcloud VPS plans and VPS add-ons",
        "offers": offer_list,
    }
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"https://{domain}/"},
            {"@type": "ListItem", "position": 2, "name": "OVHcloud",
             "item": f"https://{domain}/provider-ovhcloud"},
        ],
    }

    tpl = load_template('provider-ovhcloud.html')
    return render(tpl, {
        'JSONLD_PRODUCT': json.dumps(product, indent=2),
        'JSONLD_BREADCRUMB': json.dumps(breadcrumb, indent=2),
        'ROWS': '\n'.join(rows),
    })


def write_generated_manifest(repo_dir, pages):
    """Write the whitelist of data-generated pages.

    Deterministic on purpose — no timestamp, sorted list — so an unchanged data set
    produces a byte-identical file and CI does not commit noise every six hours.
    """
    path = Path(repo_dir) / GENERATED_MANIFEST
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        'note': ('Pages build.py generates from data/offers.json. verify_deploy_dir() blocks any '
                 'page that carries an AggregateOffer without being listed here.'),
        'pages': sorted(pages),
    }
    text = json.dumps(doc, indent=2, ensure_ascii=False) + '\n'
    path.write_bytes(text.replace('\n', '\r\n').encode('utf-8'))
    return path


# ─── PRICE-PER-GB COMPARE PAGE ───────────────────────────────────────────────
# One page, three tiers. Every number is either read from data/offers.json or
# divided out of two numbers that are, and every cell keeps the page and the read
# date it came from. Nothing here is typed by hand; a provider that cannot enter a
# tier is listed with the reason instead of being dropped from the table.

COMPARE_PAGE = 'vps-price-compare.html'
COMPARE_URL_PATH = '/vps-price-compare'
MID_TIER = (2, 4)  # vCPU, RAM in GB — the tier every provider can be normalised to

COMPARE_TIERS = (
    ('entry', 'Entry tier',
     'the cheapest plan each provider sells with a published spec'),
    ('mid', 'Mid tier — 2 vCPU / 4 GB',
     'an exact 2 vCPU and 4 GB match, nothing bent to the nearest'),
    ('high', 'High tier',
     'the most expensive plan each provider sells with a published spec'),
)


def _d(value):
    return Decimal(str(value))


def _q2(value):
    return _d(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _unit(value):
    """The exact quotient where it terminates, at least two decimals.

    Displayed so a reader can redo the division and land on the same digits:
    4.54 / 4 shows as 1.135, 23.37 / 24 as 0.97375. Only a quotient that never
    terminates (e.g. 71.21 / 24) is rounded, to four decimals.
    """
    d = _d(value)
    for places in range(2, 7):
        q = d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
        if q == d:
            return f'{q:.{places}f}'
    return f'{d:.4f}'


def spec_plans(offers):
    """Plans that carry a price and all three specs — the only rows a tier can use."""
    out = []
    for o in offers:
        if offer_kind(o) != 'plan' or o.get('price') is None:
            continue
        if not (o.get('vcpu') and o.get('ram_gb') and o.get('disk_gb')):
            continue
        out.append(o)
    return out


def pick_tier(offers, key):
    """One plan per provider for one tier. A neighbouring tier is never bent to fit."""
    by_prov = {}
    for o in spec_plans(offers):
        by_prov.setdefault(o['provider'], []).append(o)
    picked = []
    for prov in sorted(by_prov):
        cand = by_prov[prov]
        if key == 'mid':
            cand = [o for o in cand if (o['vcpu'], o['ram_gb']) == MID_TIER]
            if not cand:
                continue
            picked.append(min(cand, key=lambda o: (_d(o['price']), o.get('order') or 0)))
        elif key == 'entry':
            picked.append(min(cand, key=lambda o: (_d(o['price']), o.get('order') or 0)))
        else:
            picked.append(max(cand, key=lambda o: (_d(o['price']), o.get('order') or 0)))
    return picked


def tier_exclusions(offers, key, picked):
    """Every priced provider that is not in this tier, and why. Never silently dropped."""
    inside = {o['provider'] for o in picked}
    priced = sorted({o['provider'] for o in offers if o.get('price') is not None})
    spec = spec_plans(offers)
    out = []
    for prov in priced:
        if prov in inside:
            continue
        mine = [o for o in spec if o['provider'] == prov]
        if not mine:
            out.append((prov, 'price only — data/offers.json holds a monthly price but no '
                              'vCPU, RAM or storage for this provider, so it cannot be placed '
                              'on a tier without inventing the specs'))
            continue
        near = min(mine, key=lambda o: abs(o['vcpu'] - MID_TIER[0]) + abs(o['ram_gb'] - MID_TIER[1]))
        out.append((prov, f'no exact {MID_TIER[0]} vCPU / {MID_TIER[1]} GB plan; the nearest '
                          f'published is {near["vcpu"]} vCPU / {near["ram_gb"]} GB at '
                          f'${_q2(near["price"]):.2f}/mo'))
    return out


def unit_costs(offer):
    """$/GB RAM, $/vCPU, $/GB storage — one division each, no weighting."""
    price = _d(offer['price'])
    return {
        'ram': price / _d(offer['ram_gb']),
        'vcpu': price / _d(offer['vcpu']),
        'disk': price / _d(offer['disk_gb']),
    }


def _spread(values):
    lo, hi = min(values), max(values)
    return (lo, hi, _q2(hi / lo)) if lo else (lo, hi, None)


def newest_read(offers):
    return max(str(o.get('fetched_at') or '')[:10] for o in offers if o.get('fetched_at'))


def build_tier(offers, key, label, basis):
    """Rows, unit costs, spreads and the rendered section for one tier."""
    rows = pick_tier(offers, key)
    if len(rows) < 2:
        raise SystemExit(
            f'BUILD ABORTED: the {key} tier has only {len(rows)} provider(s) with a published '
            f'spec — a comparison needs at least two, and inventing the missing one is not '
            f'an option.')
    costs = {o['provider']: unit_costs(o) for o in rows}
    p_lo, p_hi, p_spread = _spread([_d(o['price']) for o in rows])
    r_lo, r_hi, r_spread = _spread([c['ram'] for c in costs.values()])
    v_lo, v_hi, v_spread = _spread([c['vcpu'] for c in costs.values()])
    d_lo, d_hi, d_spread = _spread([c['disk'] for c in costs.values()])
    best_ram = min(costs, key=lambda p: costs[p]['ram'])
    total_priced = len({o['provider'] for o in offers if o.get('price') is not None})

    conclusion = (
        f'{label} — <strong>{len(rows)} of {total_priced}</strong> priced providers take part. '
        f'Monthly price ${_q2(p_lo):.2f} to ${_q2(p_hi):.2f}, a <strong>{p_spread:.2f}×</strong> '
        f'spread; per GB of RAM ${_unit(r_lo)} to ${_unit(r_hi)}, {r_spread:.2f}×; per vCPU '
        f'${_unit(v_lo)} to ${_unit(v_hi)}, {v_spread:.2f}×; per GB of storage ${_unit(d_lo)} to '
        f'${_unit(d_hi)}, {d_spread:.2f}×. Cheapest per GB of RAM: {esc(best_ram)} at '
        f'${_unit(costs[best_ram]["ram"])}.')

    body = []
    for o in rows:
        c = costs[o['provider']]
        mark = ' best' if o['provider'] == best_ram else ''
        note = ''
        if o.get('billing_term_months'):
            note = (f'<span class="cell-note">billed {o["billing_term_months"]} months up front; '
                    f'renews ${_q2(o["renewal_price"]):.2f}/mo</span>')
        src = (f'<a href="{esc(o["source_url"])}">official page</a>'
               f'<br><span class="src">read {esc(str(o.get("fetched_at") or "")[:10])}</span>')
        body.append(
            '        <tr>\n'
            f'          <td><strong>{esc(o["provider"])}</strong></td>\n'
            f'          <td>{esc(o["title"])}{note}</td>\n'
            f'          <td>{o["vcpu"]}</td>\n'
            f'          <td>{o["ram_gb"]} GB</td>\n'
            f'          <td>{o["disk_gb"]} GB</td>\n'
            f'          <td class="price">${_q2(o["price"]):.2f}</td>\n'
            f'          <td class="unit{mark}">${_unit(c["ram"])}</td>\n'
            f'          <td class="unit">${_unit(c["vcpu"])}</td>\n'
            f'          <td class="unit">${_unit(c["disk"])}</td>\n'
            f'          <td>{src}</td>\n'
            '        </tr>')

    exc = tier_exclusions(offers, key, rows)
    if exc:
        exc_html = ('<div class="excluded"><p><strong>Not in this tier, and why:</strong></p><ul>'
                    + ''.join(f'<li><strong>{esc(p)}</strong> — {esc(r)}</li>' for p, r in exc)
                    + '</ul></div>')
    else:
        exc_html = ('<div class="excluded"><p>Every priced provider takes part in this tier.</p></div>')

    html = (
        f'<h2 id="tier-{key}">{esc(label)} '
        f'<span class="count">{len(rows)} providers</span></h2>\n'
        f'<p class="basis">Tier definition: {esc(basis)}.</p>\n'
        f'<p class="conclusion">{conclusion}</p>\n'
        f'<div class="table-wrap">\n'
        f'<table>\n'
        f'    <thead><tr><th>Provider</th><th>Plan</th><th>vCPU</th><th>RAM</th><th>Storage</th>'
        f'<th>$/mo</th><th>$/GB RAM</th><th>$/vCPU</th><th>$/GB storage</th><th>Source</th></tr></thead>\n'
        f'    <tbody>\n' + '\n'.join(body) + '\n    </tbody>\n'
        f'</table>\n'
        f'</div>\n'
        + exc_html)

    return {
        'key': key, 'label': label, 'basis': basis, 'rows': rows, 'costs': costs,
        'p_lo': p_lo, 'p_hi': p_hi, 'p_spread': p_spread,
        'r_lo': r_lo, 'r_hi': r_hi, 'r_spread': r_spread,
        'v_lo': v_lo, 'v_hi': v_hi, 'v_spread': v_spread,
        'd_lo': d_lo, 'd_hi': d_hi, 'd_spread': d_spread,
        'best_ram': best_ram, 'html': html,
    }


def _renewal_table(entry_rows, hidden):
    """What the entry plan renews at, and the size of the gap. Computed, never assumed."""
    body = []
    for o in entry_rows:
        block = (hidden.get('providers') or {}).get(o['provider']) or {}
        term = ((block.get('cells') or {}).get('term') or {}).get('value') or 'none listed on official page'
        if o.get('renewal_price'):
            gap = _q2(_d(o['renewal_price']) / _d(o['price']))
            renew = f'${_q2(o["renewal_price"]):.2f}/mo'
            gap_cell = f'<strong>{gap:.2f}×</strong>'
        else:
            renew = 'none published on the official page'
            gap_cell = 'cannot compute'
        body.append(
            '        <tr>\n'
            f'          <td><strong>{esc(o["provider"])}</strong></td>\n'
            f'          <td>{esc(o["title"])}</td>\n'
            f'          <td class="price">${_q2(o["price"]):.2f}</td>\n'
            f'          <td>{esc(renew)}</td>\n'
            f'          <td>{gap_cell}</td>\n'
            f'          <td>{esc(term)}</td>\n'
            '        </tr>')
    return '\n'.join(body)


def gen_price_compare_page(offers, hidden, domain):
    """Render /vps-price-compare from offers.json + data/vps_compare.json."""
    tiers = [build_tier(offers, k, label, basis) for k, label, basis in COMPARE_TIERS]
    entry, mid, high = tiers[0], tiers[1], tiers[2]
    entry_rows = entry['rows']
    read_date = newest_read(offers)
    total_priced = len({o['provider'] for o in offers if o.get('price') is not None})

    lead = (
        f'Three tiers, {total_priced} providers priced in data/offers.json, '
        f'{len(entry_rows)} of them with a published spec. The entry tier runs '
        f'${_q2(entry["p_lo"]):.2f} to ${_q2(entry["p_hi"]):.2f} a month '
        f'({entry["p_spread"]:.2f}× apart) and ${_unit(entry["r_lo"])} to '
        f'${_unit(entry["r_hi"])} per GB of RAM ({entry["r_spread"]:.2f}×); the 2 vCPU / 4 GB '
        f'tier ${_q2(mid["p_lo"]):.2f} to ${_q2(mid["p_hi"]):.2f} '
        f'({mid["p_spread"]:.2f}×) and ${_unit(mid["r_lo"])} to ${_unit(mid["r_hi"])} per GB '
        f'({mid["r_spread"]:.2f}×); the high tier ${_q2(high["p_lo"]):.2f} to '
        f'${_q2(high["p_hi"]):.2f} ({high["p_spread"]:.2f}×) and ${_unit(high["r_lo"])} to '
        f'${_unit(high["r_hi"])} per GB ({high["r_spread"]:.2f}×). Every figure is a published '
        f'price divided by a published spec.')

    # hidden-cost matrix — entry tier, because that is the plan a first-time buyer picks
    items = hidden.get('items') or []
    head = ''.join(f'<th>{esc(o["provider"])}</th>' for o in entry_rows)
    hrows = []
    for item in items:
        cells = [f'          <td><strong>{esc(item["label"])}</strong></td>']
        for o in entry_rows:
            block = (hidden.get('providers') or {}).get(o['provider']) or {}
            cell = (block.get('cells') or {}).get(item['key']) or {}
            value = cell.get('value') or 'none listed on official page'
            url = cell.get('source_url') or block.get('source_url') or o.get('source_url', '')
            cells.append(f'          <td>{esc(value)}<br><a class="src" href="{esc(url)}">source</a></td>')
        hrows.append('        <tr>\n' + '\n'.join(cells) + '\n        </tr>')

    # the sentences the numbers came from
    evidence = []
    for o in entry_rows:
        block = (hidden.get('providers') or {}).get(o['provider']) or {}
        quotes = ''.join(
            f'<p class="quote"><b>{esc(item["label"])}:</b> '
            f'{esc(((block.get("cells") or {}).get(item["key"]) or {}).get("quote", "none listed on official page"))}</p>'
            for item in items)
        evidence.append(
            f'<h3>{esc(o["provider"])} — <a href="{esc(block.get("source_url") or o["source_url"])}">'
            f'{esc(block.get("source_url") or o["source_url"])}</a>, read {esc(block.get("read_at") or read_date)}</h3>\n'
            + quotes)

    renewal_rows = _renewal_table(entry_rows, hidden)

    title = (f'VPS price per GB: entry, 2 vCPU / 4 GB and high tiers at '
             f'{len(entry_rows)} providers | ServerBudget')
    desc = (f'Three tiers priced across ' + ', '.join(o['provider'] for o in entry_rows)
            + f': entry ${_q2(entry["p_lo"]):.2f}-${_q2(entry["p_hi"]):.2f}, 2 vCPU / 4 GB '
            f'${_q2(mid["p_lo"]):.2f}-${_q2(mid["p_hi"]):.2f}, high '
            f'${_q2(high["p_lo"]):.2f}-${_q2(high["p_hi"]):.2f} per month.')

    jsonld = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "url": f"https://{domain}{COMPARE_URL_PATH}",
        "dateModified": read_date,
        "breadcrumb": {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"https://{domain}/"},
                {"@type": "ListItem", "position": 2, "name": "Price per GB",
                 "item": f"https://{domain}{COMPARE_URL_PATH}"},
            ],
        },
    }

    tpl = load_template('vps-price-compare.html')
    return render(tpl, {
        'DOMAIN': domain,
        'TITLE': esc(title),
        'DESCRIPTION': esc(desc),
        'H1': esc('VPS price per GB of RAM — three tiers, '
                  + str(len(entry_rows)) + ' providers, one division per number'),
        'LEAD': lead,
        'TIER_SECTIONS': '\n'.join(t['html'] for t in tiers),
        'ENTRY_LOW': f'{_q2(entry["p_lo"]):.2f}',
        'HIDDEN_HEAD': head,
        'HIDDEN_ROWS': '\n'.join(hrows),
        'RENEWAL_ROWS': renewal_rows,
        'EVIDENCE': '\n'.join(evidence),
        'READ_DATE': read_date,
        'JSONLD': json.dumps(jsonld, indent=2),
    })


# ─── HOMEPAGE STATS BAR ──────────────────────────────────────────────────────
# The bar used to carry three typed-in figures: 14, 7 and a date. The 7 counted the
# providers registered in .ilang/site.ilang, not the ones with a price — four of the
# seven had no data at all. Now every figure is counted from data/offers.json on
# every build, and the build refuses to publish if the page and the data disagree.

HOME_PAGE = 'index.html'
HOME_ADDON_GROUP = 'addons'
STATS_START = '<!-- STATS:START'
STATS_END = '<!-- STATS:END -->'
_GROUP_RE = re.compile(r'<h2 class="group-head" id="([^"]+)">')


def home_stats(offers):
    """What the homepage bar counts, straight out of offers.json.

    A plan only counts if it carries all three specs, because only those become a
    card on the page — the four Hostinger rows are priced but spec-less, so counting
    them would print a figure no reader could find by counting.
    """
    plans = [o for o in spec_plans(offers)]
    addons = [o for o in offers if offer_kind(o) == 'addon']
    spec_provs = sorted({o['provider'] for o in plans})
    return {
        'plans': len(plans),
        'addons': len(addons),
        'providers': len(spec_provs),
        'provider_names': spec_provs,
        'read': newest_read(offers),
    }


def home_page_counts(text):
    """Count the cards actually rendered on the homepage, per group."""
    marks = list(_GROUP_RE.finditer(text))
    counts = {'plans': 0, 'addons': 0, 'providers': 0, 'groups': {}}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        cards = text[m.end():end].count('class="card"')
        gid = m.group(1)
        counts['groups'][gid] = cards
        if gid == HOME_ADDON_GROUP:
            counts['addons'] += cards
        else:
            counts['providers'] += 1 if cards else 0
            counts['plans'] += cards
    return counts


def refresh_home_stats(live_dir, offers):
    """Rewrite the homepage stats bar from offers.json, or abort if the page disagrees."""
    path = Path(live_dir) / HOME_PAGE
    raw = path.read_bytes().decode('utf-8')
    crlf = '\r\n' in raw
    text = raw.replace('\r\n', '\n')
    stats = home_stats(offers)
    page = home_page_counts(text)

    mismatches = [f'{k}: page {page[k]} vs data {stats[k]}'
                  for k in ('plans', 'addons', 'providers') if page[k] != stats[k]]
    if mismatches:
        raise SystemExit(
            'BUILD ABORTED: the homepage cards and data/offers.json disagree, so any figure '
            'printed above them would be unbacked — ' + '; '.join(mismatches)
            + f' (groups seen: {page["groups"]})')

    names = ', '.join(stats['provider_names'])
    cards = stats['plans'] + stats['addons']
    block = (
        f'{STATS_START} — generated by build.py from data/offers.json, do not hand-edit -->\n'
        f'    <div class="stats">\n'
        f'        <div class="stat"><div class="stat-num">{stats["plans"]}</div>'
        f'<div class="stat-label">VPS plans</div></div>\n'
        f'        <div class="stat"><div class="stat-num">{stats["addons"]}</div>'
        f'<div class="stat-label">Add-ons</div></div>\n'
        f'        <div class="stat"><div class="stat-num">{stats["providers"]}</div>'
        f'<div class="stat-label">Providers with specs</div></div>\n'
        f'        <div class="stat"><div class="stat-num"><span class="vdate">{stats["read"]}</span></div>'
        f'<div class="stat-label">Newest read</div></div>\n'
        f'    </div>\n'
        f'    <p class="stats-note">Counted at build time from data/offers.json — '
        f'<strong>{stats["plans"]}</strong> plans that publish a vCPU, RAM and storage spec are '
        f'the {stats["plans"]} plan cards below, <strong>{stats["addons"]}</strong> add-on offers '
        f'are the other {stats["addons"]} cards, <strong>{stats["providers"]}</strong> providers '
        f'({esc(names)}) publish those specs, and the date is the newest '
        f'<code>fetched_at</code> among them; Hostinger\'s rows carry a monthly price but no '
        f'spec, so they are not counted as comparable.</p>\n'
        f'    {STATS_END}')

    start = text.find(STATS_START)
    end = text.find(STATS_END)
    if start < 0 or end < 0:
        raise SystemExit(f'BUILD ABORTED: {HOME_PAGE} has no stats markers '
                         f'({STATS_START} … {STATS_END}) to fill in.')
    text = text[:start] + block + text[end + len(STATS_END):]
    text = re.sub(r'(<span class="vdate">)[^<]*(</span>)',
                  lambda m: m.group(1) + stats['read'] + m.group(2), text, count=1)
    path.write_bytes((text.replace('\n', '\r\n') if crlf else text).encode('utf-8'))
    print(f'  stats: {stats["plans"]} plans, {stats["addons"]} add-ons, '
          f'{stats["providers"]} providers, read {stats["read"]} — matches the {cards} cards on the page')
    return stats


def ensure_nav_link(live_dir, href, label):
    """Add one nav link to every page that carries the shared nav block.

    Done here rather than by hand so a new page cannot be published unlinked, and
    idempotent so the six-hourly build does not keep re-adding it.
    """
    changed = skipped = 0
    for page in sorted(Path(live_dir).glob('*.html')):
        text = page.read_bytes().decode('utf-8', 'ignore')
        m = re.search(r'(<div class="nav">)(.*?)(</div>)', text, re.S)
        if not m:
            continue
        inner = m.group(2)
        if href in inner:
            skipped += 1
            continue
        indent_m = re.search(r'\n([ \t]*)<a ', inner)
        indent = indent_m.group(1) if indent_m else '            '
        trailing = re.search(r'\s*$', inner).group(0)
        body = inner[:len(inner) - len(trailing)] if trailing else inner
        eol = '\r\n' if '\r\n' in text else '\n'
        new_inner = body + eol + indent + f'<a href="{href}">{label}</a>' + trailing
        page.write_bytes((text[:m.start()] + m.group(1) + new_inner + m.group(3)
                          + text[m.end():]).encode('utf-8'))
        changed += 1
    print(f'  nav: {href} added to {changed} page(s), already present on {skipped}')
    return changed


def ensure_sitemap_url(live_dir, url, lastmod):
    """Add one <url> to live-site/sitemap.xml if it is not already listed."""
    path = Path(live_dir) / 'sitemap.xml'
    if not path.is_file():
        return False
    text = path.read_bytes().decode('utf-8')
    if f'<loc>{url}</loc>' in text:
        print(f'  sitemap: {url} already listed')
        return False
    eol = '\r\n' if '\r\n' in text else '\n'
    entry = f'  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod></url>'
    text = text.replace('</urlset>', entry + eol + '</urlset>', 1)
    path.write_bytes(text.encode('utf-8'))
    print(f'  sitemap: added {url}')
    return True


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
    hidden_path = script_dir / 'data' / 'vps_compare.json'
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
        sitemap_pages.append((f'https://{domain}/provider/{slug(prov["name"])}', ts))

    # 2b. OVHcloud page — generated from data/offers.json, written into the deploy source
    #     (live-site/) as well as site/, so the published page cannot drift from the data.
    #     Its name goes into the generated-page manifest that the deploy gate whitelists.
    print('Generating provider-ovhcloud.html from data/offers.json ...')
    live_dir = script_dir / 'live-site'
    generated = {'provider-ovhcloud.html'}
    ovh_html = gen_ovhcloud_page(offers, domain).replace('\n', '\r\n').encode('utf-8')
    for target_dir in (live_dir, site_dir):
        target_dir.mkdir(exist_ok=True)
        (target_dir / 'provider-ovhcloud.html').write_bytes(ovh_html)

    # 2c. Price-per-GB comparison page — same rule: generated, never typed.
    print('Generating vps-price-compare.html from data/offers.json + data/vps_compare.json ...')
    hidden = {}
    if hidden_path.exists():
        hidden = json.loads(hidden_path.read_text(encoding='utf-8'))
    else:
        print(f'WARNING: {hidden_path.name} missing — hidden-cost cells will read "none listed"',
              file=sys.stderr)
    cmp_html = gen_price_compare_page(offers, hidden, domain).replace('\n', '\r\n').encode('utf-8')
    for target_dir in (live_dir, site_dir):
        (target_dir / COMPARE_PAGE).write_bytes(cmp_html)
    generated.add(COMPARE_PAGE)

    # 2d. Publish plumbing for generated pages: nav link on every page, sitemap entry.
    ensure_nav_link(live_dir, COMPARE_URL_PATH, 'Price per GB')
    ensure_sitemap_url(live_dir, f'https://{domain}{COMPARE_URL_PATH}',
                       newest_read(offers))

    # 2e. Homepage stats bar — counted from offers.json, aborts if the page disagrees.
    refresh_home_stats(live_dir, offers)

    # 2f. One page, one address: every .html file gets its exact 301 to the
    #     extensionless twin, added in sorted position if it is not already there.
    sync_redirect_rules(live_dir)

    manifest_path = write_generated_manifest(script_dir, generated)
    print(f'  generated {len(generated)} page(s); manifest: '
          f'{manifest_path.relative_to(script_dir).as_posix()}')

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
        sitemap_pages.append((f'https://{domain}/deal/{p_slug}-{d_slug}', ts))

    # 4. Compare page
    print('Generating compare.html ...')
    html_out = gen_compare_page(brand, niche, domain, offers, providers)
    (site_dir / 'compare.html').write_text(html_out, encoding='utf-8')
    sitemap_pages.append((f'https://{domain}/compare', ts))

    # 5. About page
    print('Generating about.html ...')
    html_out = gen_about(brand, domain)
    (site_dir / 'about.html').write_text(html_out, encoding='utf-8')
    sitemap_pages.append((f'https://{domain}/about', ts))

    # 6. Privacy page
    print('Generating privacy.html ...')
    html_out = gen_privacy(brand, domain)
    (site_dir / 'privacy.html').write_text(html_out, encoding='utf-8')
    sitemap_pages.append((f'https://{domain}/privacy', ts))

    # 7. Contact page
    contact_email = os.environ.get('CONTACT_EMAIL', '')
    print(f'Generating contact.html ... (email: {"set" if contact_email else "NOT SET"})')
    html_out = gen_contact(brand, domain, contact_email)
    (site_dir / 'contact.html').write_text(html_out, encoding='utf-8')
    sitemap_pages.append((f'https://{domain}/contact', ts))

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
    #     Exception: pages in `generated` are written by the build itself (step 2b), so they
    #     are NOT copied — copying them was the path that let a hand-written page survive.
    print('Copying live-site/ files to site/ ...')
    import shutil
    live_dir = script_dir / 'live-site'

    # 10a. GA4 coverage HOOK — runs on every generation, never a manual step.
    #      Scope is "all .html found", so newly added pages are covered automatically.
    #      live-site/ is the deploy source, so it must carry GA4 BEFORE the copy.
    print('Ensuring GA4 snippet on every page (live-site/) ...')
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    from inject_ga4 import inject_ga4_into_dir
    if live_dir.exists():
        inject_ga4_into_dir(live_dir)

    if live_dir.exists():
        copied = 0
        for item in live_dir.iterdir():
            if item.is_file():
                if item.name in generated:
                    print(f'  Skipped {item.name} (generated from data, never copied)')
                    continue
                dest = site_dir / item.name
                shutil.copy2(str(item), str(dest))
                print(f'  Copied {item.name}')
                copied += 1
        print(f'  Total: {copied} files copied from live-site/')

    # 10b. Second pass over site/ so template-generated pages are covered too.
    print('Ensuring GA4 snippet on every page (site/) ...')
    inject_ga4_into_dir(site_dir)

    print(f'\n{"="*60}')
    print(f'Site generated in: {site_dir}')
    print(f'Pages: {len(sitemap_pages)}')
    print(f'Sitemap: {site_dir / "sitemap.xml"}')
    print(f'Robots:  {site_dir / "robots.txt"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
