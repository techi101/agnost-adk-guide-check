<!-- Drop-in replacement for the plugin section of docs.agnost.ai/google-adk (draft, 27 Nov 2026).
Why: the current plugin writes the final answer with trace.get_current_span(). On ADK 2.x that is the root
invoke_workflow span; on ADK 1.x the final-answer callback runs inside a child generate_content span, so the answer
lands on a child and the root (named "invocation" in 1.x) also has no gen_ai.conversation.id.
Tested offline with a local OTLP receiver and a scripted model (techi101/agnost-adk-guide-check, check/out/results.json):
  ADK 2.15.1, current plugin: root has user, input, answer, conversation id
  ADK 1.39.1, current plugin: root has user and input; answer and conversation id missing
  ADK 1.39.1 and 2.15.1, plugin below: root has user, input, answer and conversation id
Tested against a local receiver, not Agnost's dashboard. -->

### Supported ADK versions

This plugin works on ADK 1.x and 2.x. It remembers each turn's root span when the user's message arrives and writes
the final answer to that span, because on ADK 1.x the final-answer callback runs inside a child span.

```python
import json

from google.adk.plugins.base_plugin import BasePlugin
from opentelemetry import trace


def _text(content):
    return "".join(p.text for p in (content.parts or []) if p.text) if content else ""


class AgnostPlugin(BasePlugin):
    """Adds user.id, the conversation id, and each turn's input and answer to ADK's root span."""

    def __init__(self):
        super().__init__(name="agnost")
        self._roots = {}  # invocation_id -> root span of that turn

    async def on_user_message_callback(self, *, invocation_context, user_message):
        span = trace.get_current_span()  # root span: invoke_workflow (2.x) or invocation (1.x)
        self._roots[invocation_context.invocation_id] = span
        span.set_attribute("user.id", invocation_context.session.user_id)
        span.set_attribute("gen_ai.conversation.id", invocation_context.session.id)
        span.set_attribute("gen_ai.input.messages", json.dumps(
            [{"role": "user", "parts": [{"type": "text", "content": _text(user_message)}]}]))

    async def on_event_callback(self, *, invocation_context, event):
        if event.is_final_response() and _text(event.content):
            span = self._roots.get(invocation_context.invocation_id) or trace.get_current_span()
            span.set_attribute("gen_ai.output.messages", json.dumps(
                [{"role": "assistant", "parts": [{"type": "text", "content": _text(event.content)}]}]))

    async def after_run_callback(self, *, invocation_context):
        self._roots.pop(invocation_context.invocation_id, None)
```

`gen_ai.conversation.id` is set explicitly because ADK 1.x doesn't put it on the root span (ADK 2.x does; setting it
again is harmless).
