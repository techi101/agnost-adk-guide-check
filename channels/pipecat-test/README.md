# Do Pipecat tool calls reach Agnost?

Tested 27 Nov 2026 on Pipecat 1.17.0 with the setup from docs.agnost.ai/pipecat (HTTP/protobuf exporter,
`setup_tracing`, `enable_tracing=True`, `conversation_id`, `enduser.id`). Spans go to `receiver.py`, a local stand-in
for otel.agnost.ai; `fake_openai.py` and `fake_anthropic.py` are API stubs so no API key is needed.

| Scenario | Tool calls | Recoverable, recipe only | With observer |
|---|---|---|---|
| baseline (tool runs, bot answers) | 1 | 1 | 1 |
| parallel (two calls in one reply) | 2 | 2 | 2 |
| no_followup (`run_llm=False`, the end_call pattern) | 1 | **0** | 1 |
| hangup (caller disconnects mid-tool, `runner.cancel()`) | 1 | **0** | 1 |
| interrupt (user talks over a slow tool) | 1 | **0** | 1 |
| timeout (`timeout_secs` exceeded) | 1 | 1 (only as `CANCELLED`) | 1 (with reason) |
| error (tool raises) | 1 | 1 (generic message) | 1 (with exception type) |
| baseline, Claude (`AnthropicLLMService`) | 1 | **0** (*) | 1 |
| no_followup, Claude | 1 | **0** | 1 |

\* The call is in the next `llm` span as an Anthropic `tool_use` block; Agnost's docs say context recovery covers
OpenAI-compatible services, so it is counted as not recoverable. If Agnost parses Anthropic's format, this row changes.

Why: Pipecat makes no span for function execution; Agnost recovers calls from the next LLM request's context. With
no next request there is nothing to recover. `agnost_tool_spans.py` adds one `execute_tool <name>` span per call
(GenAI conventions, the shape Agnost already reads for other frameworks), parented to the turn; cancelled or
unfinished calls end with an error status and a reason.

Run: `pip install "pipecat-ai[tracing,openai,anthropic]" opentelemetry-exporter-otlp-proto-http`, then `python run_all.py`.
`shim/` is only for Windows machines where an app-control policy blocks sentencex's compiled module.

Possible v2: Pipecat 1.17 ships `FunctionCallObserver` (observers/function_call_observer.py), which reports each call
as started, in progress, completed, failed, timed out or cancelled. A v2 could subclass it to get Pipecat's own
outcome labels, keeping this observer's turn-context lookup and its end-of-call cleanup (no event settles a call that
is still running when the call is cancelled).
