import sys
from playwright.sync_api import sync_playwright
url=sys.argv[1]; out=sys.argv[2]
with sync_playwright() as p:
    b=p.chromium.launch(args=["--mute-audio"])
    for w,h in [(1440,900),(390,844)]:
        pg=b.new_page(viewport={"width":w,"height":h}); errs=[]
        pg.on("console",lambda m: errs.append(m.text) if m.type=="error" else None)
        pg.goto(url,wait_until="networkidle"); pg.wait_for_timeout(1200)
        sw=pg.evaluate("document.documentElement.scrollWidth")
        pg.screenshot(path=f"{out}_{w}.png",full_page=True)
        print(w,"scrollWidth",sw,"overflow" if sw>w else "no-overflow","errors",errs)
    b.close()
