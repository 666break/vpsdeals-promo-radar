#!/usr/bin/env python3
"""Batch fix live-site files: FIX1 (disclosure) + FIX2 (brand name)."""
import re
from pathlib import Path

live_site = Path(r'C:\Users\Administrator\vpsdeals-promo-radar\live-site')

# FIX1: Old disclosure -> New disclosure (verbatim, one word unchanged)
OLD_DISCLOSURE = 'Some links on this site are affiliate links. We may earn a commission if you buy through them, at no extra cost to you.'
NEW_DISCLOSURE = 'This site will display third-party ads, and some links may be affiliate links that earn us a commission if you make a purchase.'

all_changes = []

for html_file in sorted(live_site.glob('*.html')):
    content = html_file.read_text(encoding='utf-8')
    original = content
    changes = []

    # --- FIX1: Replace old disclosure sentence with new one ---
    c1 = content.count(OLD_DISCLOSURE)
    if c1 > 0:
        content = content.replace(OLD_DISCLOSURE, NEW_DISCLOSURE)
        changes.append(f'FIX1: replaced {c1} disclosure sentence(s)')

    # --- FIX2: Replace "vpsdeals" (no hyphen) -> "ServerBudget" ---
    # Safe to blanket-replace: never appears in URLs or as keyword
    c2 = content.count('vpsdeals')
    if c2 > 0:
        content = content.replace('vpsdeals', 'ServerBudget')
        changes.append(f'FIX2: replaced {c2} "vpsdeals" -> "ServerBudget"')

    # --- FIX2: Replace "vps-deals" (hyphenated) -> "ServerBudget" ---
    # MUST NOT change "vps-deals-promo-radar" (GitHub URL path)
    # Regex: match vps-deals NOT followed by -promo
    pattern = r'vps-deals(?!-promo)'
    matches = list(re.finditer(pattern, content))
    if matches:
        content = re.sub(pattern, 'ServerBudget', content)
        changes.append(f'FIX2: replaced {len(matches)} "vps-deals" -> "ServerBudget" (skipped GitHub URL)')

    if content != original:
        html_file.write_text(content, encoding='utf-8')
        all_changes.append((html_file.name, changes))
        print(f'=== {html_file.name} ===')
        for c in changes:
            print(f'  {c}')
    else:
        print(f'{html_file.name}: no changes')

# Verification: check no remaining brand variants (excluding GitHub URL)
print('\n=== VERIFICATION ===')
for html_file in sorted(live_site.glob('*.html')):
    content = html_file.read_text(encoding='utf-8')
    vpsdeals_left = content.count('vpsdeals')
    vps_deals_left = len(re.findall(r'vps-deals(?!-promo)', content))
    old_disc_left = content.count(OLD_DISCLOSURE)
    new_disc_found = content.count(NEW_DISCLOSURE)
    keyword_intact = content.count('VPS Deals')  # Must be preserved
    issues = []
    if vpsdeals_left: issues.append(f'vpsdeals={vpsdeals_left}')
    if vps_deals_left: issues.append(f'vps-deals={vps_deals_left}')
    if old_disc_left: issues.append(f'old_disclosure={old_disc_left}')
    if issues:
        print(f'  WARNING {html_file.name}: {", ".join(issues)}')
    else:
        print(f'  OK {html_file.name}: new_disclosure={new_disc_found}, keyword_VPS_Deals={keyword_intact}')

print('\nDone.')
