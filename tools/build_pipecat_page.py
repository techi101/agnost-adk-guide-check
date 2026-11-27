import html, json, re
from pathlib import Path

ROOT = Path("D:/proofs/agnost-growth")
audit = (ROOT / "site/onboarding-audit/index.html").read_text(encoding="utf-8")
css = audit[audit.index("<style>"):audit.index("</style>") + 8]
css = css.replace("@media (prefers-reduced-motion", "pre code{background:none;color:inherit;padding:0;font:inherit}\npre{font:400 .82rem/1.55 var(--mono);background:#18201D;color:#E6ECE7;padding:18px 20px;border-radius:12px;overflow-x:auto;margin:12px 0 0}\n.big{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:26px}\n.kpi{background:var(--win);border-radius:12px;box-shadow:0 0 0 1px var(--line);padding:18px 20px}\n.kpi .v{font:600 2.4rem/1 var(--display);letter-spacing:-.02em}\n.kpi .l{color:var(--muted);font-size:.92rem;margin-top:6px}\n.kpi.bad .v{color:var(--wine)}.kpi.good .v{color:var(--cobalt)}\ntd.zero{color:var(--wine);font-weight:600}td.ok{color:var(--cobalt);font-weight:600}\n@media (max-width:520px){.big{grid-template-columns:1fr}}\n@media (prefers-reduced-motion")
res = json.loads((ROOT / "channels/pipecat-test/results.json").read_text(encoding="utf-8"))["results"]
obs = (ROOT / "channels/pipecat-test/agnost_tool_spans.py").read_text(encoding="utf-8")

what = {
    "baseline": ("User asks about an order; the tool runs; the bot answers", "A following LLM request carries the call"),
    "parallel": ("Two tool calls in one LLM reply", "Same: both are in the next request"),
    "no_followup": ("Tool returns with <code>run_llm=False</code> (the usual <code>end_call</code> / <code>transfer_call</code> pattern)", "No LLM request follows"),
    "hangup": ("Caller hangs up while the tool is running (Pipecat's examples call <code>runner.cancel()</code> on disconnect)", "Call ends before any follow-up"),
    "interrupt": ("User talks over a slow tool; Pipecat cancels it", "<code>FunctionCallCancelFrame</code>, no follow-up"),
    "timeout": ("Tool exceeds <code>timeout_secs</code>; Pipecat cancels it and asks the LLM to continue", "Visible, but only as <code>CANCELLED</code>; the span adds the reason"),
    "error": ("Tool raises (order service returns 503)", "Visible, but only as \"failed and returned no result\"; the span keeps <code>RuntimeError: order service returned 503</code>"),
    "baseline (Claude)": ("Baseline with Pipecat's <code>AnthropicLLMService</code>", "Next request carries <code>tool_use</code> blocks, not OpenAI <code>tool_calls</code>*"),
    "no_followup (Claude)": ("<code>run_llm=False</code> with Claude", "No LLM request follows"),
}
rows = []
made = lost = fixed = 0
for r in res:
    made += r["tool_calls_made"]; lost += r["tool_calls_made"] - r["recipe_only"]; fixed += r["with_observer"]
    c1 = "zero" if r["recipe_only"] < r["tool_calls_made"] else "ok"
    c2 = "zero" if r["with_observer"] < r["tool_calls_made"] else "ok"
    rows.append(f'<tr><td>{what[r["scenario"]][0]}</td><td class="n">{r["tool_calls_made"]}</td><td class="n {c1}">{r["recipe_only"]}</td><td class="n {c2}">{r["with_observer"]}</td><td>{what[r["scenario"]][1]}</td></tr>')

page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pipecat tool-call test</title>
<meta name="description" content="Tested on Pipecat 1.17.0: tool calls with no follow-up LLM request, and Claude tool calls, are not recoverable through the documented OpenTelemetry setup. An 80-line observer fixes it.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..700&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
{css}
</head>
<body>
<div class="wrap">
  <header class="top">
    <span><b>Pipecat tool-call test</b> for Agnost AI</span>
    <nav aria-label="Page"><a href="#results">Results</a><a href="#fix">The fix</a><a href="#upstream">Upstream</a><a href="#reproduce">Reproduce</a><a href="/onboarding-audit">Onboarding audit</a></nav>
  </header>

  <div class="hero">
    <h1>The tool calls a voice bot makes right before a call ends don't reach Agnost</h1>
    <p class="lede">Your Pipecat page says Pipecat creates no span for function execution, so Agnost <em>"recovers each call and its result from the context of the LLM request that follows it."</em> I tested what happens when nothing follows. <strong>On Pipecat 1.17.0, following your setup exactly, {lost} of {made} tool calls in my test weren't recoverable: 4 appeared in no exported span at all, and 1 (with Claude) only in Anthropic's format, which your docs don't cover.</strong> An 80-line observer brings it to {fixed} of {made}, in the span shape your ingest already reads.</p>
    <div class="big">
      <div class="kpi bad"><div class="v">{made - lost} / {made}</div><div class="l">tool calls recoverable with the documented setup</div></div>
      <div class="kpi good"><div class="v">{fixed} / {made}</div><div class="l">with <code>AgnostToolSpanObserver</code> added</div></div>
    </div>
  </div>

  <section id="results">
    <h2>Nine scenarios, one local run</h2>
    <p class="sub">Each scenario ran twice: your recipe as written, then with the observer. Spans went to a local OTLP/HTTP receiver standing in for <code>otel.agnost.ai</code> (same protobuf, same <code>X-Agnost-Org-ID</code> header). "Visible" means the call's tool name and arguments are in some exported span, either an <code>execute_tool</code> span or an assistant <code>tool_calls</code> entry inside a later <code>llm</code> span's <code>input</code>.</p>
    <div class="tw"><table>
      <thead><tr><th>Scenario</th><th>Tool calls made</th><th>Visible, recipe only</th><th>Visible, with observer</th><th>Why</th></tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table></div>
    <p class="note" style="margin-top:14px">* Your docs say recovery "works for OpenAI-compatible LLM services, which send context in OpenAI chat format." Pipecat writes each provider's own format into the <code>llm</code> span: OpenAI <code>tool_calls</code>, Anthropic <code>tool_use</code> blocks (tested here), AWS Bedrock <code>toolUse</code> and Gemini <code>function_call</code> parts (from Pipecat's adapter source). I counted Claude calls as not recoverable by that stated condition; if your ingest already parses Anthropic's format, those two rows change. The observer's span is the same whichever LLM the bot uses.</p>
    <p class="note" style="margin-top:10px">The three lost cases are the ones your product exists for. An <code>end_call</code> or <code>transfer_call</code> tool is how a voice bot finishes or escalates a call, and GitHub code search finds 165 public Python files containing both <code>run_llm=False</code> and <code>end_call</code>. A caller who hangs up mid-lookup and a tool cut off by an interruption are the calls where something went wrong. In all three, the LLM span that requested the tool has no <code>output</code> attribute, so the request itself isn't in the trace either.</p>
  </section>

  <section id="fix">
    <h2>The fix: one observer, no backend change</h2>
    <p class="sub">It writes each function call as an <code>execute_tool &lt;name&gt;</code> span under the current turn, with <code>gen_ai.tool.name</code>, <code>gen_ai.tool.call.id</code>, <code>gen_ai.tool.call.arguments</code> and <code>gen_ai.tool.call.result</code>. That is the shape your Vercel eve and Inngest AgentKit pages already list as "a tool call with its arguments, result, latency, and outcome". A call that is cancelled, or still open when the call ends, is closed with an error status and the reason. Each call is handled once, even though its frames pass through several processors.</p>
    <pre><code>{html.escape(obs)}</code></pre>
    <p class="note" style="margin-top:12px">Add it with <code>PipelineWorker(pipeline, observers=[AgnostToolSpanObserver()], enable_tracing=True, ...)</code>. Checked in the test: every tool span shares the conversation's trace and have the <code>turn</code> span as parent; the two parallel calls keep their own IDs, arguments and results. In the baseline cases Agnost now gets the call twice (the span and the next request's context), so the ingest should dedupe on <code>gen_ai.tool.call.id</code>, or the docs could say to use the observer instead of context recovery.</p>
  </section>

  <section id="upstream">
    <h2>Why not wait for Pipecat?</h2>
    <p class="sub">Pipecat has an open pull request that adds <code>function_call</code> spans: <a href="https://github.com/pipecat-ai/pipecat/pull/4266">#4266</a>, opened 9 Apr 2026 by the main developer of finchvox, an open-source observability tool for Pipecat. As of 27 Nov it has no review, now conflicts with main, and has waited 232 days. Two things matter for Agnost if it ever lands: it names attributes <code>tool.function_name</code>, <code>tool.arguments</code> and <code>tool.result</code>, not the <code>gen_ai.tool.*</code> names your ingest reads for other frameworks, so it needs a mapping; and its notes say the span for an async function call ends before the final result arrives. The observer works on the Pipecat release your customers run today.</p>
    <p class="note">Pipecat users are hitting the same edge from the other side: <a href="https://github.com/pipecat-ai/pipecat/issues/5790">#5790</a> (open since 16 Sep) reports that a function call still running when the call ends is not settled when <code>on_pipeline_finished</code> runs, and a contributor reproduced on <code>main</code> that the tool is then cancelled during cleanup. That is the "hangup" row above; the observer records it as an error with "call ended before the tool returned".</p>
    <p class="note">For comparison, LiveKit Agents already wraps every tool in a <code>function_tool</code> span with GenAI tool attributes (name, call id, arguments; <a href="https://github.com/livekit/agents/blob/main/livekit-agents/livekit/agents/voice/generation.py">voice/generation.py</a>), so your LiveKit customers get these calls whether or not a reply follows. Pipecat is the framework where they go missing.</p>
  </section>

  <section id="reproduce">
    <h2>Reproduce it in about a minute</h2>
    <pre><code>python -m venv .venv &amp;&amp; .venv/bin/pip install "pipecat-ai[tracing,openai,anthropic]" opentelemetry-exporter-otlp-proto-http
.venv/bin/python run_all.py    # starts the receiver and fake OpenAI and Anthropic servers, runs 9 scenarios x 2, writes results.json</code></pre>
    <p class="note">Files: <code>run_all.py</code>, <code>scenarios.py</code>, <code>fake_openai.py</code> (an OpenAI-compatible stub, so no API key), <code>receiver.py</code>, <code>agnost_tool_spans.py</code>, in <a href="https://github.com/techi101/agnost-adk-guide-check/tree/main/channels/pipecat-test">channels/pipecat-test</a>. Honest limits: I ran it against a local receiver, not your ingest, so I couldn't see how Agnost renders the new spans; the turn split needs real TTS frames, so this text-only test produces one turn per call; and on my Windows laptop an app-control policy blocks the compiled <code>sentencex</code> module, so the test puts a small pure-Python stand-in on <code>PYTHONPATH</code> (<code>shim/</code>; not needed on Linux or macOS).</p>
    <p class="note">Ready to hand over: a skill patch that adds the observer to the Pipecat recipe, and a docs section for docs.agnost.ai/pipecat.</p>
  </section>
</div>
<footer>
  <div class="wrap">
    <span>Nitesh Kumar Yadav · NSUT Delhi · 27 Nov 2026</span>
    <span>Independent work, not affiliated with Agnost AI. Nothing was sent to Agnost's API in this test.</span>
  </div>
</footer>
</body>
</html>
'''
out = ROOT / "site/pipecat-tool-calls"
out.mkdir(exist_ok=True)
(out / "index.html").write_text(page, encoding="utf-8")
print("written", len(page), "lost", lost, "made", made, "fixed", fixed)
