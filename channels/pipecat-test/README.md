# Do Pipecat tool calls reach Agnost?

Tested 27 Nov 2026 on Pipecat 1.17.0 with the setup from docs.agnost.ai/pipecat (HTTP/protobuf exporter,
`setup_tracing`, `enable_tracing=True`, `conversation_id`, `enduser.id`). Spans go to `receiver.py`, a local stand-in
for otel.agnost.ai; `fake_openai.py` is an OpenAI-compatible stub so no API key is needed.

| Scenario | Tool calls | Visible, recipe only | Visible, with observer |
|---|---|---|---|
| baseline (tool runs, bot answers) | 1 | 1 | 1 |
| parallel (two calls in one reply) | 2 | 2 | 2 |
| no_followup (`run_llm=False`, the end_call pattern) | 1 | **0** | 1 |
| hangup (caller disconnects mid-tool, `runner.cancel()`) | 1 | **0** | 1 |
| interrupt (user talks over a slow tool) | 1 | **0** | 1 |

Why: Pipecat makes no span for function execution; Agnost recovers calls from the next LLM request's context. With
no next request there is nothing to recover. `agnost_tool_spans.py` adds one `execute_tool <name>` span per call
(GenAI conventions, the shape Agnost already reads for other frameworks), parented to the turn; cancelled or
unfinished calls end with an error status and a reason.

Run: `pip install "pipecat-ai[tracing,openai]" opentelemetry-exporter-otlp-proto-http`, then `python run_all.py`.
`shim/` is only for Windows machines where an app-control policy blocks sentencex's compiled module.
