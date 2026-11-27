<!-- Drop-in section for docs.agnost.ai/pipecat, after "What appears in Agnost AI". Tested on Pipecat 1.17.0:
     channels/pipecat-test (python run_all.py). 
     Note for engineers: when a follow-up request exists, the call now arrives twice (span + context); dedupe on gen_ai.tool.call.id. -->

## Tool calls at the end of a call

Agnost recovers each function call from the LLM request that follows it. Some calls have no follow-up request:

* a tool that returns with `run_llm=False`, such as `end_call` or `transfer_call`
* a caller who hangs up while a tool is still running
* a call that Pipecat cancels because the user interrupted it

Add `AgnostToolSpanObserver` so these calls appear too. It writes one `execute_tool <name>` span per call under the
current turn, with the tool name, arguments and result, and marks a cancelled or unfinished call as an error.

```python
from agnost_tool_spans import AgnostToolSpanObserver

worker = PipelineWorker(
    pipeline,
    observers=[AgnostToolSpanObserver()],
    enable_tracing=True,
    conversation_id=call_id,
    additional_span_attributes={"enduser.id": customer_id},
)
```

Copy `agnost_tool_spans.py` from the Agnost skill (`references/pipecat-tool-spans.py`) into your bot. To check it,
end one test call with a tool (for example, ask the bot to transfer you) and confirm the tool call appears in the
conversation.
