"""Records a captioned ~80 s walkthrough of the live proof pages (Playwright video), then converts to MP4.
Run: python video/record.py   ->  video/agnost_walkthrough.mp4"""
import shutil, subprocess, time
from pathlib import Path
from playwright.sync_api import sync_playwright
import imageio_ffmpeg

HERE = Path(__file__).parent
BASE = "https://agnost-adk-guide-check.vercel.app"
W, H = 1440, 810

CAPTION_CSS = """
#vocap{position:fixed;left:50%;bottom:34px;transform:translateX(-50%) translateY(12px);max-width:980px;width:calc(100% - 120px);
 background:rgba(12,12,12,.92);color:#fff;font:500 25px/1.38 "Instrument Sans",system-ui,sans-serif;padding:18px 26px;border-radius:12px;
 box-shadow:0 20px 50px -20px rgba(0,0,0,.5);z-index:99999;opacity:0;transition:opacity .35s cubic-bezier(.23,1,.32,1),transform .35s cubic-bezier(.23,1,.32,1);text-align:center}
#vocap.on{opacity:1;transform:translateX(-50%)}
#vocap b{color:#C9BCF7;font-weight:600}
#tagline{position:fixed;top:18px;right:22px;z-index:99999;font:500 13px "Instrument Sans",sans-serif;color:#6B6B6B;background:#fff;border:1px solid #E4E4E4;padding:6px 10px;border-radius:999px}
"""


def setup(pg):
    pg.add_style_tag(content=CAPTION_CSS)
    pg.evaluate("""()=>{const c=document.createElement('div');c.id='vocap';document.body.appendChild(c);
      const t=document.createElement('div');t.id='tagline';t.textContent='Nitesh for Agnost AI';document.body.appendChild(t);}""")


def say(pg, html, hold):
    pg.evaluate("""h=>{const c=document.getElementById('vocap');c.classList.remove('on');setTimeout(()=>{c.innerHTML=h;c.classList.add('on')},260)}""", html)
    time.sleep(hold)


def scroll_to(pg, selector, offset=40, dur=1.2):
    pg.evaluate("""([s,o])=>{const e=document.querySelector(s);window.scrollTo({top:e.getBoundingClientRect().top+scrollY-o,behavior:'smooth'})}""", [selector, offset])
    time.sleep(dur)


def open_page(pg, path):
    pg.goto(BASE + path, wait_until="networkidle")
    pg.evaluate("document.fonts.ready")
    pg.evaluate("()=>{try{auto=false}catch(e){}}")  # stop the viewer's auto-flip; we flip it on camera
    setup(pg)
    time.sleep(1.2)


with sync_playwright() as p:
    b = p.chromium.launch(args=["--mute-audio"])
    ctx = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=1,
                        record_video_dir=str(HERE / "raw"), record_video_size={"width": W, "height": H})
    pg = ctx.new_page()

    open_page(pg, "/start")
    say(pg, "I set up Agnost the way your customers do, <b>and tested it.</b>", 4.5)
    scroll_to(pg, "#viewer", 20)
    say(pg, "On Pipecat, following your docs exactly, <b>5 of 10 tool calls</b> can't be recovered.", 5)
    say(pg, "The missing ones: end call and transfer tools, hang&#8209;ups, interruptions, and bots on Claude.", 5)
    pg.click("#b-fix")
    say(pg, "An 80&#8209;line observer sends each call as an <b>execute_tool</b> span. <b>10 of 10.</b>", 5.5)

    open_page(pg, "/pipecat-tool-calls")
    scroll_to(pg, "#why", 30)
    say(pg, "Why: Pipecat writes no span for a tool, and Agnost reads the next request. <b>Sometimes there isn't one.</b>", 6)
    scroll_to(pg, "#fix", 30)
    say(pg, "The fix needs <b>no backend change</b>, and the whole test runs in one command.", 4.5)
    pg.evaluate("()=>{const p=document.querySelector('#fix pre');p.scrollTo({top:900,behavior:'smooth'})}")
    time.sleep(2.5)

    open_page(pg, "/start")
    scroll_to(pg, "#openai", 30)
    say(pg, "You got Agnost into Vercel's and Mastra's docs. OpenAI's list is next: <b>9 compatibility checks pass.</b>", 6)
    scroll_to(pg, "#audit", 30)
    say(pg, "Plus <b>12 onboarding gaps</b>, each with a fix ready, including 8 skill patches.", 5)
    scroll_to(pg, "#me", 120)
    say(pg, "Happy to walk through all of it on our call. <b>Nitesh</b>", 4.5)

    ctx.close()
    raw = pg.video.path()
    b.close()

ff = imageio_ffmpeg.get_ffmpeg_exe()
out = HERE / "agnost_walkthrough.mp4"
subprocess.run([ff, "-y", "-i", str(raw), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
                "-movflags", "+faststart", "-an", str(out)], check=True, capture_output=True)
print("video:", out, round(out.stat().st_size / 1e6, 2), "MB")
