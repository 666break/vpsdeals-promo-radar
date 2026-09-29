#!/usr/bin/env python3
# ::ILANG [TYPE:component][COMPONENT:inject_ga4][LANG:py]
# RESPONSIBILITY: Ensure EVERY .html page in a directory carries the GA4 snippet.
#                 Scope is "all html files found", never a hardcoded page list.
#                 Idempotent: a file that already contains the ID is left untouched.
# BOUNDARY: Never fabricate the measurement ID. Never rewrite page content other than
#           inserting the block immediately before </head>.
# HOOK: build.py imports inject_ga4_into_dir() and calls it for live-site/ and site/
#       on every generation, so no page can ever ship without GA4 again.

import pathlib

GA4_ID = "G-H2F4PWVG2P"

BLOCK = (
    "  <!-- Google Analytics (GA4) -->\n"
    "  <script async src=\"https://www.googletagmanager.com/gtag/js?id=" + GA4_ID + "\"></script>\n"
    "  <script>\n"
    "    window.dataLayer = window.dataLayer || [];\n"
    "    function gtag(){dataLayer.push(arguments);}\n"
    "    gtag('js', new Date());\n"
    "    gtag('config', '" + GA4_ID + "');\n"
    "  </script>\n"
)


def inject_ga4_into_dir(directory, recursive=True, verbose=True):
    """Inject the GA4 block into every .html file under `directory`.

    Returns (injected, skipped, missing_head, total).
    """
    base = pathlib.Path(directory)
    if not base.exists():
        if verbose:
            print("  GA4: dir not found, skipped ->", base)
        return (0, 0, 0, 0)

    globber = base.rglob("*.html") if recursive else base.glob("*.html")
    files = sorted(p for p in globber if p.is_file())

    injected = skipped = no_head = 0
    for p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception as e:
            if verbose:
                print("  GA4 READ-FAIL  {} ({})".format(p.name, e))
            continue
        if GA4_ID in text:
            skipped += 1
            if verbose:
                print("  GA4 SKIP       {} (already has it)".format(p.name))
            continue
        if "</head>" not in text:
            no_head += 1
            if verbose:
                print("  GA4 NO-HEAD    {} (no </head> found)".format(p.name))
            continue
        text = text.replace("</head>", BLOCK + "</head>", 1)
        p.write_text(text, encoding="utf-8")
        injected += 1
        if verbose:
            print("  GA4 INJECTED   {}".format(p.name))

    if verbose:
        print("  GA4 summary    {}: injected={} skipped={} no_head={} total={}".format(
            base.name, injected, skipped, no_head, len(files)))
    return (injected, skipped, no_head, len(files))


if __name__ == "__main__":
    root = pathlib.Path(__file__).parent
    print("=== GA4 full-coverage injection (all html, no hardcoded page list) ===")
    for d in (root / "live-site", root / "site"):
        print("\n[" + d.name + "/]")
        inject_ga4_into_dir(d)
    print("\nDone.")
