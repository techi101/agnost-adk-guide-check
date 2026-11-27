"""Builds site/pipecat-tool-calls/index.html (v2 design, Agnost visual language). Data: channels/pipecat-test/results.json,
code: channels/pipecat-test/agnost_tool_spans.py. Reuses /start's CSS and trace viewer."""
import html, io, json, keyword, tokenize
from pathlib import Path

ROOT = Path("D:/proofs/agnost-growth")
start = (ROOT / "site/start/index.html").read_text(encoding="utf-8")
css = start[start.index("<style>") + 7:start.index("</style>")]
res = json.loads((ROOT / "channels/pipecat-test/results.json").read_text(encoding="utf-8"))["results"]
made = sum(r["tool_calls_made"] for r in res); rec = sum(r["recipe_only"] for r in res); fixd = sum(r["with_observer"] for r in res)
code = (ROOT / "channels/pipecat-test/agnost_tool_spans.py").read_text(encoding="utf-8").replace("\r\n", "\n")


def highlight(src):
    lines = src.splitlines(keepends=True)
    def pos(rc):
        r, c = rc; return sum(len(l) for l in lines[:r - 1]) + c
    out, last = [], 0
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        a, b = pos(tok.start), pos(tok.end)
        if a < last: continue
        out.append(html.escape(src[last:a])); t = html.escape(src[a:b])
        if tok.type == tokenize.COMMENT: t = f'<i class="c">{t}</i>'
        elif tok.type == tokenize.STRING: t = f'<i class="{"c" if tok.string.startswith('"""') else "s"}">{t}</i>'
        elif tok.type == tokenize.NAME and keyword.iskeyword(tok.string): t = f'<i class="k">{t}</i>'
        elif tok.type == tokenize.NUMBER: t = f'<i class="n">{t}</i>'
        out.append(t); last = b
    out.append(html.escape(src[last:]))
    return "".join(out)


extra_css = """
.hero{padding:52px 32px 28px}
h1{max-width:20ch}
.why{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:56px;align-items:center}
.lanes{border:1px solid var(--line-2);border-radius:14px;overflow:hidden}
.lane{padding:18px 20px;border-bottom:1px solid var(--line)}
.lane:last-child{border-bottom:0;background:#FFF8F9}
.lane h3{margin:0 0 12px;font:500 13px var(--sans);color:var(--ink-2);display:flex;justify-content:space-between;gap:12px}
.lane h3 em{font-style:normal;color:var(--green)}
.lane:last-child h3 em{color:var(--red)}
.flow{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font:500 12px var(--mono)}
.flow span{padding:8px 10px;border-radius:6px;background:#F1F1F1;color:var(--ink-2)}
.flow .tc{background:var(--violet);color:#fff}
.flow .nx{background:#E9E5F8;color:#5A4A93;box-shadow:0 0 0 2px var(--violet-mid)}
.flow .gone{background:#fff;border:1.5px dashed #E0A3B0;color:var(--red)}
.flow b{color:var(--muted);font-weight:400}
.lane p{margin:12px 0 0;font-size:14px;color:var(--ink-2)}
.fixgrid{display:grid;grid-template-columns:minmax(0,4fr) minmax(0,8fr);gap:48px;align-items:start}
.attrs{list-style:none;padding:0;margin:18px 0 0;display:grid;gap:10px}
.attrs li{font-size:15px;color:var(--ink-2);padding-left:18px;position:relative}
.attrs li::before{content:"";position:absolute;left:0;top:.6em;width:7px;height:7px;border-radius:2px;background:var(--violet);transform:rotate(45deg)}
.win{border-radius:12px;overflow:hidden;background:#111114;box-shadow:0 0 0 1px rgba(0,0,0,.08),0 30px 70px -35px rgba(30,10,90,.55);min-width:0}
.win .tabs{display:flex;align-items:center;gap:8px;padding:10px 14px;background:#1B1B20;color:#A9A9B3;font:400 12.5px var(--mono)}
.win .tabs i{width:10px;height:10px;border-radius:50%;background:#3A3A42;display:inline-block}
.win .tabs b{margin-left:10px;color:#ECECF1;font-weight:400}
.win pre{margin:0;padding:18px 20px;max-height:560px;overflow:auto;font:400 12.8px/1.62 var(--mono);color:#D9D9E3;tab-size:4}
.win pre code{background:none;color:inherit;padding:0;font:inherit}
.win pre i{font-style:normal}
.win pre .c{color:#85859A;font-style:italic}.win pre .s{color:#B9F2C9}.win pre .k{color:#B8A3FF}.win pre .n{color:#FFC48A}.win pre .p{color:#7BE0A9}
.facts{list-style:none;margin:0;padding:0}
.facts li{display:grid;grid-template-columns:110px minmax(0,1fr);gap:16px;padding:16px 0;border-top:1px solid var(--line);font-size:15px;color:var(--ink-2)}
.facts li:last-child{border-bottom:1px solid var(--line)}
.facts li b{font:italic 400 24px/1.1 var(--serif);color:var(--violet-ink)}
.facts .more{margin-left:4px}
.limits{margin:18px 0 0;padding:0;list-style:none;display:grid;gap:8px;font-size:14px;color:var(--muted)}
@media (max-width:980px){.why,.fixgrid{grid-template-columns:1fr;gap:24px}}
@media (max-width:640px){.facts li{grid-template-columns:1fr;gap:4px}.win pre{font-size:11.5px;padding:14px}}
"""

viewer_js = start[start.index("<script>") + 8:start.index("</script>")]
v0 = start.index('<div class="viewer"'); v1 = start.index('<section id="openai">')
viewer = start[v0:v1].rstrip()
viewer = viewer[:viewer.rstrip().rfind("</div>")].rstrip()  # drop the closing tag of .hero

results_lines = "\n".join(f"{r['scenario'][:21]:21} made {r['tool_calls_made']}  recipe only {r['recipe_only']}  with fix {r['with_observer']}" for r in res)

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pipecat tool-call test</title>
<meta name="description" content="Tested on Pipecat 1.17.0 with Agnost's documented setup: {made - rec} of {made} tool calls are not recoverable. An 80-line observer brings it to {fixd} of {made}.">
<meta property="og:title" content="{made - rec} of {made} Pipecat tool calls never make it into an Agnost trace">
<meta property="og:description" content="Tested on Pipecat 1.17.0 following Agnost's docs. An 80-line observer fixes it. One-command test.">
<meta property="og:image" content="https://agnost-adk-guide-check.vercel.app/start/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Instrument+Sans:wght@400..600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{css}{extra_css}</style>
</head>
<body>
<div class="frame">
  <div class="bar">
    <div><b><a href="/start" style="text-decoration:none">Nitesh Kumar Yadav</a></b> <span>Pipecat tool-call test for Agnost AI</span></div>
    <nav aria-label="Page"><a href="#why">Why</a><a href="#fix">The fix</a><a href="#reproduce">Reproduce</a></nav>
  </div>

  <div class="hero">
    <div class="rise">
      <div class="from"><i></i>Pipecat 1.17.0, tested 27 Nov 2026</div>
      <h1>{made - rec} of {made} tool calls <em>never make it</em> into an Agnost trace.</h1>
      <p class="lede">Your Pipecat page says Agnost recovers each tool call “from the context of the LLM request that follows it.” I tested what happens when nothing follows. These are the calls that end a conversation, hand it off, or break.</p>
      <div class="ctas">
        <a class="btn solid" href="#fix">See the 80&#8209;line fix</a>
        <a class="btn dash" href="#reproduce">Run it yourself</a>
      </div>
    </div>
    {viewer}
  </div>

  <section id="why">
    <div class="why">
      <div>
        <div class="num">Why they go missing</div>
        <h2>Pipecat never writes a span for a tool. Agnost reads the next request. Sometimes there isn't one.</h2>
        <p style="color:var(--ink-2);max-width:46ch">When the bot ends the call, transfers it, gets hung up on, or gets interrupted, no LLM request comes after the tool, so the call is in no span at all. With Claude, the next request exists but carries Anthropic's <code>tool_use</code> format, which your docs say recovery doesn't cover.</p>
      </div>
      <div class="lanes" aria-label="Two timelines compared">
        <div class="lane">
          <h3>Normal turn <em>recovered</em></h3>
          <div class="flow"><span>user</span><b>→</b><span class="tc">llm asks for get_order_status</span><b>→</b><span>tool runs</span><b>→</b><span class="nx">next llm request carries it</span></div>
          <p>The call and its result ride along in the next request's context. Agnost reads them there.</p>
        </div>
        <div class="lane">
          <h3>Bot ends the call <em>lost</em></h3>
          <div class="flow"><span>user</span><b>→</b><span class="tc">llm asks for end_call</span><b>→</b><span>tool runs</span><b>→</b><span class="gone">nothing follows</span></div>
          <p>The tool returns with <code>run_llm=False</code>, so no next request carries the call. A hang-up or an interruption ends the same way.</p>
        </div>
      </div>
    </div>
  </section>

  <section id="fix">
    <div class="fixgrid">
      <div>
        <div class="num">The fix</div>
        <h2>One observer. No backend change.</h2>
        <p style="color:var(--ink-2)">Add it to the worker with <code>observers=[AgnostToolSpanObserver()]</code>. It writes every tool call as its own span under the current turn, in the shape your other framework pages already read.</p>
        <ul class="attrs">
          <li>An <code>execute_tool</code> span with tool name, call id, arguments and result</li>
          <li>Parent is the <code>turn</code> span, in the conversation's trace</li>
          <li>Cancelled, timed-out or unfinished calls close as errors, with the reason</li>
          <li>Same result whichever LLM the bot uses, Claude included</li>
        </ul>
      </div>
      <div class="win">
        <div class="tabs"><i></i><i></i><i></i><b>agnost_tool_spans.py</b></div>
        <pre><code>{highlight(code)}</code></pre>
      </div>
    </div>
  </section>

  <section id="evidence">
    <div class="split">
      <div>
        <div class="num">Outside evidence</div>
        <h2>Pipecat users hit the same edge. Pipecat's own fix has waited since April.</h2>
      </div>
      <ul class="facts">
        <li><b>#5790</b><div>Open since 16 Sep: a tool call still running when the call ends isn't settled when <code>on_pipeline_finished</code> runs, and a contributor reproduced on main that it's cancelled during cleanup. That's the hang-up row. <a class="more" href="https://github.com/pipecat-ai/pipecat/issues/5790">Issue →</a></div></li>
        <li><b>#4266</b><div>A pull request adding <code>function_call</code> spans, opened 9 Apr by finchvox's main developer, unreviewed for 232 days and now conflicting. If it lands, its attributes are named <code>tool.*</code>, not the <code>gen_ai.tool.*</code> your ingest reads. <a class="more" href="https://github.com/pipecat-ai/pipecat/pull/4266">PR →</a></div></li>
        <li><b>LiveKit</b><div>LiveKit Agents already wraps every tool in a <code>function_tool</code> span, so your LiveKit customers get these calls. Pipecat is the framework where they go missing. <a class="more" href="https://github.com/livekit/agents/blob/main/livekit-agents/livekit/agents/voice/generation.py">Source →</a></div></li>
      </ul>
    </div>
  </section>

  <section id="reproduce">
    <div class="fixgrid">
      <div>
        <div class="num">Reproduce</div>
        <h2>About a minute. No API keys.</h2>
        <p style="color:var(--ink-2)">The script starts a stand-in for otel.agnost.ai and fake OpenAI and Anthropic servers, then runs all nine scenarios with and without the observer.</p>
        <ul class="limits">
          <li>Tested against a local receiver, not your ingest, so I couldn't see how Agnost renders the new spans.</li>
          <li>Where a request does follow, the call now arrives twice; dedupe on <code>gen_ai.tool.call.id</code>.</li>
          <li>Windows only: an app-control policy blocked sentencex's compiled module, so <code>shim/</code> stands in for it.</li>
        </ul>
        <p style="margin-top:18px"><a class="more" href="https://github.com/techi101/agnost-adk-guide-check/tree/main/channels/pipecat-test">All files on GitHub →</a></p>
      </div>
      <div class="win">
        <div class="tabs"><i></i><i></i><i></i><b>terminal</b></div>
<pre><code><i class="p">$</i> pip install "pipecat-ai[tracing,openai,anthropic]" opentelemetry-exporter-otlp-proto-http
<i class="p">$</i> python run_all.py
{html.escape(results_lines)}
</code></pre>
      </div>
    </div>
  </section>

  <footer>
    <span><a href="/start">← Back to the overview</a></span>
    <span>Independent work by Nitesh Kumar Yadav, not affiliated with Agnost AI.</span>
  </footer>
</div>
<script>{viewer_js}</script>
</body>
</html>
"""
(ROOT / "site/pipecat-tool-calls/index.html").write_text(page, encoding="utf-8")
print("written", len(page), "lost", made - rec, "made", made, "fixed", fixd)
