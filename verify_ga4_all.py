"""VERIFY: open every URL in the live sitemap and count the GA4 id in the source.

No fabrication: prints the real HTTP code and the real occurrence count per URL,
then a tally of how many pages are 0.
"""
import re
import urllib.request

GA4_ID = "G-H2F4PWVG2P"
SITEMAP = "https://serverbudget.com/sitemap.xml"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:  # noqa: F821
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)


code, sm = get(SITEMAP)
print("sitemap", SITEMAP, "-> HTTP", code)
urls = re.findall(r"<loc>(.*?)</loc>", sm)
print("URLs in sitemap:", len(urls))
print()

zero = []
for u in urls:
    c, body = get(u)
    n = body.count(GA4_ID)
    flag = "" if n > 0 else "   <== 0"
    print("%-3s  GA4=%-2d  %s%s" % (c, n, u, flag))
    if n == 0:
        zero.append(u)

print()
print("TOTAL: %d urls, %d with GA4, %d WITHOUT GA4 (0)" % (len(urls), len(urls) - len(zero), len(zero)))
for u in zero:
    print("   zero:", u)
