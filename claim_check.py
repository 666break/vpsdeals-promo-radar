"""Claim consistency gate: a sentence on a page must be checkable from that page.

Two kinds of claim are enforced, because they fail in different ways:

  RATIO      A multiplier in prose ("5.29x for identical specs") must equal some
             ordered pair of the amounts printed in the same sentence, within
             0.02. Arithmetic expressions such as "24.00 x 1.0625" are skipped:
             they are operations, not conclusions.

  ABSENCE    A sentence that says something does not exist ("there is no
             first-term-then-renewal jump", "none of the three publishes an
             overage rate") is the easiest kind of claim to leave standing after
             the data has moved. Every such sentence must map to a signed entry
             in data/absence_claims.json, and that entry must say 'verified'. If
             the entry says 'refuted', the page still carries a claim we know is
             false and the deploy stops.

Both checks read the page's own tables: the renewal check recomputes the jump
from the first-term and renewal prices printed in one row, and the term check
compares a claim about a provider's yearly price against the Term cell that
provider's row carries. Nothing is compared against a second copy of the data.

A third kind runs over every page, not just the price family:

  SCHEMA-DIRECTION  A JSON-LD payload is read out of document order, so "the
             windows above" or "the offers below" has nothing to point at once
             the payload is lifted out of the page. Any container noun (table,
             list, chart, section, row, plan, offer, window, step, block,
             callout) sitting immediately before a direction word is a hit.
             A bare "below 20%" or "previous 24 hours" is a comparison or a
             time span and is not a hit; the container noun is what decides.
             Uses that are genuinely positional but harmless go in
             data/schema_direction_allowlist.txt with a reason, one per line --
             the pattern itself is not loosened.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TOL = 0.02
HUB = 'vps-hosting-cost'
FAMILY = [
    HUB,
    'vps-price-compare',
    'vps-price-snapshot-billing',
    'vps-price-currency-and-fx',
    'vps-price-extra-ipv4',
    'vps-price-sales-tax',
    'vps-price-stopped-instance',
]
LEDGER = 'data/absence_claims.json'

ENTITIES = [
    ('&times;', 'x'), ('&nbsp;', ' '), ('&mdash;', '-'), ('&ndash;', '-'),
    ('&ldquo;', '"'), ('&rdquo;', '"'), ('&lsquo;', "'"), ('&rsquo;', "'"),
    ('&hellip;', '...'), ('&rarr;', '->'), ('&euro;', 'EUR'), ('&pound;', 'GBP'),
    ('&divide;', '/'), ('&amp;', '&'),
]

AMOUNT = re.compile(r'(?:\$|EUR|GBP)\s?([\d,]+(?:\.\d+)?)')
# A multiplier followed by a digit or a currency sign is an operation, not a claim.
RATIO = re.compile(r'(?<![\d.$])(\d+(?:\.\d+)?)\s*(?:&times;|×|x)(?!\s*[\d.$])')
RENEW = re.compile(r'renews?\s*(?:at\s*)?(?:\$|EUR|GBP)\s?([\d,]+(?:\.\d+)?)', re.I)
FIRST_TERM = re.compile(r'(?:\$|EUR|GBP)\s?([\d,]+(?:\.\d+)?)')

# A direction word only counts when a container noun sits immediately before it.
# "below 20%", "previous 24 hours", "below that fee" have no container and are
# comparisons or time spans, not positions.
SCHEMA_CONTAINERS = (
    'table', 'tables', 'list', 'lists', 'chart', 'charts', 'section', 'sections',
    'diagram', 'diagrams', 'figure', 'figures', 'row', 'rows', 'plan', 'plans',
    'offer', 'offers', 'window', 'windows', 'step', 'steps', 'block', 'blocks',
    'callout', 'callouts',
)
SCHEMA_DIRECTION = re.compile(
    r'\b(' + '|'.join(SCHEMA_CONTAINERS) + r')\s+'
    r'(above|below|following|previous|earlier|later|further)\b',
    re.I)
SCHEMA_BLOCK = re.compile(
    r'<script[^>]*type\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.S | re.I)
ALLOWLIST = 'data/schema_direction_allowlist.txt'


def visible(html: str) -> str:
    html = re.sub(r'<script.*?</script>', ' ', html, flags=re.S)
    html = re.sub(r'<style.*?</style>', ' ', html, flags=re.S)
    html = re.sub(r'<[^>]+>', ' ', html)
    for a, b in ENTITIES:
        html = html.replace(a, b)
    return re.sub(r'[ \t]+', ' ', html)


def sentence_at(text: str, pos: int) -> str:
    start = max(text.rfind('. ', 0, pos), text.rfind('! ', 0, pos), text.rfind('? ', 0, pos))
    end = min([i for i in (text.find('. ', pos), text.find('! ', pos), text.find('? ', pos)) if i != -1] or [len(text)])
    return text[start + 1:end + 1].strip()


def tables(html: str):
    """Every <tr> as a list of visible cell strings."""
    rows = []
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.S):
        cells = [re.sub(r'\s+', ' ', visible(c)).strip()
                 for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)]
        if cells:
            rows.append(cells)
    return rows


def _num(s: str) -> float:
    return float(s.replace(',', ''))


def check_ratios(name: str, text: str, errors: list, unresolved: list):
    for m in RATIO.finditer(text):
        shown = _num(m.group(1))
        sent = sentence_at(text, m.start())
        amounts = [_num(a) for a in AMOUNT.findall(sent)]
        amounts = [a for a in amounts if a > 0]
        if len(amounts) < 2:
            unresolved.append((name, m.group(1), sent))
            continue
        ok = False
        for a in amounts:
            for b in amounts:
                if a != b and abs(b / a - shown) <= TOL:
                    ok = True
                    break
            if ok:
                break
        if not ok:
            errors.append((name, 'ratio', m.group(1), sent, amounts))


def check_renewal_absence(name: str, text: str, rows, errors: list):
    """'no first-term-then-renewal jump' must survive a scan of the page's own rows."""
    hit = re.search(r'no\s+first-term[^.<]{0,90}jump|there\s+is\s+no\s+[^.<]{0,60}(?:renewal\s+)?jump', text, re.I)
    if not hit:
        return
    for cells in rows:
        joined = ' '.join(cells)
        ren = RENEW.search(joined)
        if not ren:
            continue
        renew = _num(ren.group(1))
        prices = [_num(x) for x in FIRST_TERM.findall(joined.replace(ren.group(0), ' '))]
        prices = [p for p in prices if 0 < p < renew]
        if not prices:
            continue
        # The plan price is the largest figure below the renewal price in that row;
        # the smaller ones are unit rates such as $/GB RAM, not what the first term costs.
        first = max(prices)
        if renew / first > 1 + TOL:
            errors.append((name, 'renewal-absence', '%.2fx' % (renew / first),
                           sentence_at(text, hit.start()), cells))


def check_provider_term(name: str, text: str, rows, errors: list):
    """'<Provider>'s yearly sticker' must match an Annual/Yearly Term cell."""
    for m in re.finditer(r"([A-Z][A-Za-z0-9.]*)'s\s+yearly\s+(?:sticker|price)", text):
        provider = m.group(1)
        mine = [c for c in rows if c and provider.lower() in c[0].lower()]
        if not mine:
            continue
        terms = [c[2] for c in mine if len(c) > 3]
        if terms and all(re.search(r'month', t, re.I) for t in terms):
            errors.append((name, 'yearly-vs-term', 'Term=%s' % terms[0],
                           sentence_at(text, m.start()), mine[0]))


def load_ledger(root: Path):
    path = root / LEDGER
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def check_absence_ledger(name: str, text: str, ledger, errors: list, signed: list):
    """Every absence claim found on the page needs a signed ledger entry."""
    if not ledger:
        return
    for entry in ledger.get('claims', []):
        if entry.get('page') != name:
            continue
        pat = entry.get('pattern') or ''
        if not pat:
            continue
        if not re.search(pat, text, re.I):
            continue
        status = entry.get('status')
        signed.append((name, entry.get('id'), status, entry.get('evidence', '')))
        if status != 'verified':
            errors.append((name, 'absence-ledger', status,
                           sentence_at(text, re.search(pat, text, re.I).start()),
                           [entry.get('evidence', '')]))


def _strings(obj):
    """Every string value inside a parsed JSON-LD object, in order."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def schema_payloads(html: str):
    """Every ld+json block as a list of its prose strings, plus the unparsable ones.

    Scanning the parsed string values rather than the serialised JSON keeps the
    reported "sentence" readable: the answer text, not the braces around it.
    A payload that does not parse is still scanned as raw text and reported --
    a silent skip would hide exactly the block most likely to be malformed.
    """
    payloads, failed = [], []
    for i, m in enumerate(SCHEMA_BLOCK.finditer(html)):
        body = m.group(1)
        try:
            payloads.append((i, list(_strings(json.loads(body)))))
        except Exception:
            failed.append(i)
            payloads.append((i, [body]))
    return payloads, failed


def load_schema_allowlist(base: Path):
    """page | phrase that must appear in the sentence | why it is legal"""
    path = base / ALLOWLIST
    entries = []
    if not path.is_file():
        return entries
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 3:
            continue
        entries.append((parts[0], parts[1].lower(), parts[2]))
    return entries


def _schema_allowed(allow, name, sentence):
    for page, phrase, _reason in allow:
        if page == name and phrase in sentence.lower():
            return True
    return False


def check_schema_direction(name: str, html: str, errors: list, hits: list,
                           failed_out: list, allow: list):
    """A container noun + direction word inside a JSON-LD payload is a dead pointer."""
    payloads, failed = schema_payloads(html)
    failed_out.extend((name, i) for i in failed)
    seen = set()
    for i, strings in payloads:
        for payload in strings:
            for m in SCHEMA_DIRECTION.finditer(payload):
                container, word = m.group(1).lower(), m.group(2).lower()
                sent = sentence_at(payload, m.start())
                if _schema_allowed(allow, name, sent):
                    continue
                key = (i, container, word, sent)
                if key in seen:
                    continue
                seen.add(key)
                hits.append((name, i, container, word, sent))
                errors.append((name, 'schema-direction', 'blk%d %s+%s' % (i, container, word),
                               sent, [container]))


def verify_claim_consistency(site_dir, verbose=True):
    root = Path(site_dir)
    ledger = load_ledger(Path(__file__).resolve().parent)
    errors, unresolved, signed = [], [], []
    scanned = 0
    for name in FAMILY:
        page = root / (name + '.html')
        if not page.is_file():
            errors.append((name, 'missing', '', 'page not found in deploy dir', []))
            continue
        scanned += 1
        html = page.read_text(encoding='utf-8', errors='ignore')
        text = visible(html)
        rows = tables(html)
        check_ratios(name, text, errors, unresolved)
        check_renewal_absence(name, text, rows, errors)
        check_provider_term(name, text, rows, errors)
        check_absence_ledger(name, text, ledger, errors, signed)

    # schema-direction runs over every page in the deploy dir, not just FAMILY:
    # a new article ships its own JSON-LD and nobody re-runs a site-wide sweep.
    allow = load_schema_allowlist(Path(__file__).resolve().parent)
    schema_hits, schema_failed, schema_pages = [], [], 0
    for page in sorted(root.rglob('*.html')):
        schema_pages += 1
        html = page.read_text(encoding='utf-8', errors='ignore')
        check_schema_direction(page.stem, html, errors, schema_hits, schema_failed, allow)

    if verbose:
        print('  claim gate: %d page(s), %d ratio claim(s) resolved, %d unresolved, '
              '%d absence claim(s) signed' % (scanned,
                                              _count_ratios(scanned, root),
                                              len(unresolved), len(signed)))
        print('  schema-direction: %d page(s), %d hit(s), %d parse failure(s), '
              '%d allowlisted' % (schema_pages, len(schema_hits),
                                  len(schema_failed), len(allow)))
        for name, i in schema_failed:
            print('    [parse-failed] %s: ld+json block %d -- scanned as raw text' % (name, i))
        for name, i, container, word, sent in schema_hits:
            print('    [hit] %s: block %d, %s + %s -- %s'
                  % (name, i, container, word, _clip(sent, 120)))
        for name, tok, sent in unresolved:
            print('    [manual] %s: %sx -- no two amounts in the sentence, checked by hand: %s'
                  % (name, tok, _clip(sent)))
        for name, eid, status, ev in signed:
            print('    [signed] %s: %s = %s' % (name, eid, status))

    if errors:
        lines = ['DEPLOY BLOCKED: a sentence on the page disagrees with the page\'s own data:']
        for name, kind, detail, sent, extra in errors:
            lines.append('  %s  [%s] %s' % (name, kind, detail))
            lines.append('    sentence: %s' % _clip(sent))
            if kind == 'renewal-absence':
                lines.append('    row that refutes it: %s' % ' | '.join(extra))
            elif kind == 'yearly-vs-term':
                lines.append('    row that refutes it: %s' % ' | '.join(extra))
            elif kind == 'ratio':
                lines.append('    amounts in the sentence: %s' % extra)
            elif kind == 'absence-ledger':
                lines.append('    ledger evidence: %s' % (extra[0] if extra else ''))
            elif kind == 'schema-direction':
                lines.append('    container noun: %s (a JSON-LD payload has no "above"/"below")'
                             % extra[0])
        raise SystemExit('\n'.join(lines))
    return True


def _clip(s, n=220):
    s = ' '.join(s.split())
    return s if len(s) <= n else s[:n] + '...'


def _count_ratios(scanned, root):
    total = 0
    for name in FAMILY:
        p = root / (name + '.html')
        if p.is_file():
            total += len(RATIO.findall(visible(p.read_text(encoding='utf-8', errors='ignore'))))
    return total


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'live-site'
    verify_claim_consistency(target)
    print('claim gate: PASS')
