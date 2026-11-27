# AgnostTracingProcessor × OpenAI Agents SDK: compatibility report

Purpose: the evidence that criterion 3 of openai-agents-python's tracing-listing policy asks for ("reproducible checks
against the real Agents SDK ... trace/span relationships and the advertised event types, plus applicable export
failure, flush/shutdown, and sensitive-data controls"). Run 27 Nov 2026 by Nitesh Kumar Yadav (not an Agnost employee;
in a hiring conversation with Agnost).

Versions: `agnost` 0.2.2 · `openai-agents` **0.26.0** (newer than the latest version on docs.agnost.ai/openai-agents,
0.24.0) · Python 3.12.10 · Windows 11.

Setup: real Agents SDK, two agents (triage hands off to orders, orders calls a `function_tool`). The model is a local
OpenAI chat-completions stub (`fake_chat.py`), Agnost's capture API is a local stand-in (`capture_receiver.py`), and
`set_trace_processors([...])` replaces the SDK's default exporter, so nothing leaves the machine.
Run: `pip install "agnost[openai-agents]"`, then `python check.py` (writes `report.json`).

| # | Check | Result |
|---|---|---|
| 1 | Non-streamed run (`Runner.run_sync`) | 1 session + 8 events: root agent turn, 2 agent spans, 3 LLM calls, handoff, tool. Tool name, arguments and result present; user message and final answer present |
| 2 | Streamed run (`Runner.run_streamed`) | Same 1 + 8, same content |
| 3 | Nesting | tool and orders-agent LLM calls → orders-agent; handoff and triage LLM call → triage-agent; orders-agent → triage-agent; root turn has no parent |
| 4 | Conversation and user | `group_id` → `session_id`; `trace_metadata.user_id` → session `user_data.user_id`; SDK versions in session metadata |
| 5 | `trace_include_sensitive_data=False` | Events still arrive with names and structure; no user text, tool arguments, tool result or answer in any payload |
| 6 | `include_content=False` (processor option) | Same as 5 |
| 7 | Capture API returns 500 | Agent run unaffected (0.06 s); 10 posts attempted; no exception |
| 8 | Capture API unreachable | Agent run unaffected (0.05 s); `force_flush()` returns at the 5 s `flush_timeout` bound |
| 9 | `shutdown()` | Delivers the full session and all 8 events (0.08 s) |

Two documentation notes for Agnost, not failures:
- docs.agnost.ai/openai-agents says requests carry `X-Org-Id`; agnost 0.2.2 sends `X-Project-Id`
  (`_Exporter._post`). The server may accept both (the voice webhooks accept both `org_id` and `project_id`); not tested
  against the real API.
- The supported-versions table could add 0.26.0 after this check.

Still needed for a listing request (not engineering): criterion 4, one independent team using the integration with a
public write-up or usage report; criterion 5, a named maintainer and support channel. Per the policy, open an issue
first, before any listing PR.
