"""A version-tolerant take on the AgnostPlugin from docs.agnost.ai/google-adk.

Same idea as the guide's plugin, two changes:
  * it remembers the root span when the user's message arrives and writes the
    final answer to that same span later. On ADK 1.x the final-answer callback
    runs inside a child generate_content span, so the guide's
    trace.get_current_span() puts the answer on the wrong span there.
  * it also writes gen_ai.conversation.id on the root span, because ADK 1.x
    does not put it there (ADK 2.x does).
It still only sets span attributes and never changes how the agent runs.
"""

import json

from google.adk.plugins.base_plugin import BasePlugin
from opentelemetry import trace


def _text(content):
    return "".join(p.text for p in (content.parts or []) if p.text) if content else ""


class AgnostPlugin(BasePlugin):
    """Adds user.id, conversation id, input and answer to ADK's root span."""

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
