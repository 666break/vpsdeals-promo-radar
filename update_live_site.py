#!/usr/bin/env python3
"""Batch update existing live-site HTML pages with affiliate disclosure + nav links."""
import re
from pathlib import Path

live_site = Path(r'C:\Users\Administrator\vpsdeals-promo-radar\live-site')

# Pages to update (exclude the 3 new pages which already have correct nav/footer)
pages_to_update = [
    'index.html',
    'compare.html',
    'deal-1.html', 'deal-2.html', 'deal-3.html',
    'deal-4.html', 'deal-5.html', 'deal-6.html',
    'provider-ovhcloud.html',
]

# Affiliate disclosure sentence for footer
DISCLOSURE = '<p style="margin-top:0.5rem">This site will display third-party ads, and some links may be affiliate links that earn us a commission if you make a purchase.</p>'

# New nav links
NEW_NAV_LINKS = '            <a href="about.html">About</a>\n            <a href="privacy.html">Privacy</a>\n            <a href="contact.html">Contact</a>'

for page_name in pages_to_update:
    page_path = live_site / page_name
    if not page_path.exists():
        print(f'SKIP: {page_name} not found')
        continue

    html = page_path.read_text(encoding='utf-8')
    changed = False

    # 1. Add nav links before closing </div> of .nav
    # Pattern: find <div class="nav">...</div> and add links before closing </div>
    nav_pattern = r'(<div class="nav">.*?)(\s*</div>)'
    nav_match = re.search(nav_pattern, html, re.DOTALL)
    if nav_match and 'about.html' not in nav_match.group(0):
        html = re.sub(
            nav_pattern,
            lambda m: m.group(1) + '\n' + NEW_NAV_LINKS + m.group(2),
            html,
            count=1,
            flags=re.DOTALL
        )
        changed = True

    # 2. Add affiliate disclosure before </footer>
    if 'affiliate links' not in html:
        html = html.replace('</footer>', f'{DISCLOSURE}\n    </footer>', 1)
        changed = True

    if changed:
        page_path.write_text(html, encoding='utf-8')
        print(f'UPDATED: {page_name}')
    else:
        print(f'NO CHANGE: {page_name}')

print('\nDone.')
