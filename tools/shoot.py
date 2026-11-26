"""Screenshot a URL at 1440 and 390 wide, report console errors and failed requests.

usage: python shoot.py <url> <out_prefix>
"""
import sys

from playwright.sync_api import sync_playwright

url, prefix = sys.argv[1], sys.argv[2]
bad = 0
with sync_playwright() as p:
    b = p.chromium.launch(args=["--mute-audio"])
    for w, h in [(1440, 900), (390, 844)]:
        pg = b.new_page(viewport={"width": w, "height": h})
        errs, fails = [], []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("requestfailed", lambda r: fails.append(r.url))
        pg.on("response", lambda r: fails.append(f"{r.status} {r.url}") if r.status >= 400 else None)
        pg.goto(url, wait_until="networkidle")
        pg.wait_for_timeout(1500)
        pg.screenshot(path=f"{prefix}_{w}.png")
        pg.screenshot(path=f"{prefix}_{w}_full.png", full_page=True)
        sw = pg.evaluate("document.documentElement.scrollWidth")
        print(f"{w}px: console errors={len(errs)} failed={len(fails)} scrollWidth={sw}", errs[:3], fails[:3])
        bad += len(errs) + len(fails) + (sw > w)
    b.close()
sys.exit(1 if bad else 0)
