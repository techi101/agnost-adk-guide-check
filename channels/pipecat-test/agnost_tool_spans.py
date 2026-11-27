"""AgnostToolSpanObserver: one OpenTelemetry span per Pipecat function call.

Why: Pipecat creates no span for function execution, so Agnost recovers a tool call from the context of the LLM
request that follows it. When nothing follows (a tool that returns with run_llm=False, such as end_call or
transfer_call; a caller who hangs up while the tool runs; a call cancelled by an interruption) the call never
reaches Agnost. This observer writes each call as an `execute_tool` span (OpenTelemetry GenAI conventions) under
the current turn, and closes any span still open when the call ends, marked as an error.

Use: PipelineWorker(pipeline, observers=[AgnostToolSpanObserver()], enable_tracing=True, ...)
"""
import json

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from pipecat.frames.frames import (CancelFrame, EndFrame, FunctionCallCancelFrame, FunctionCallInProgressFrame,
                                   FunctionCallResultFrame)
from pipecat.observers.base_observer import BaseObserver, FramePushed

MAX_LEN = 4000  # keep span attributes small


def _json(value):
    try:
        text = value if isinstance(value, str) else json.dumps(value, default=str)
    except Exception:
        text = str(value)
    return text[:MAX_LEN]


class AgnostToolSpanObserver(BaseObserver):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tracer = trace.get_tracer("agnost.pipecat.tools")
        self._open = {}  # tool_call_id -> span
        self._done = set()  # frames pass through several processors; handle each call once

    async def on_push_frame(self, data: FramePushed):
        frame = data.frame
        if isinstance(frame, FunctionCallInProgressFrame):
            if frame.tool_call_id in self._open or frame.tool_call_id in self._done:
                return
            tracing = getattr(data.source, "_tracing_context", None)
            parent = tracing.get_turn_context() if tracing else None
            span = self._tracer.start_span(f"execute_tool {frame.function_name}", context=parent,
                                           kind=trace.SpanKind.INTERNAL)
            span.set_attribute("gen_ai.operation.name", "execute_tool")
            span.set_attribute("gen_ai.tool.name", frame.function_name)
            span.set_attribute("gen_ai.tool.call.id", frame.tool_call_id)
            span.set_attribute("gen_ai.tool.call.arguments", _json(frame.arguments))
            if tracing and tracing.conversation_id:
                span.set_attribute("conversation.id", tracing.conversation_id)
            self._open[frame.tool_call_id] = span
        elif isinstance(frame, FunctionCallResultFrame):
            span = self._open.pop(frame.tool_call_id, None)
            if not span:
                return
            span.set_attribute("gen_ai.tool.call.result", _json(frame.result))
            error = getattr(frame, "error", None)
            if error:
                span.set_status(Status(StatusCode.ERROR, str(error)[:200]))
            if frame.run_llm is False:
                span.set_attribute("agnost.tool.run_llm", False)
            span.end()
            self._done.add(frame.tool_call_id)
        elif isinstance(frame, FunctionCallCancelFrame):
            self._close(frame.tool_call_id, "cancelled (interruption or timeout)")
        elif isinstance(frame, (EndFrame, CancelFrame)):
            for call_id in list(self._open):
                self._close(call_id, "call ended before the tool returned")

    def _close(self, call_id, reason):
        span = self._open.pop(call_id, None)
        if span:
            span.set_status(Status(StatusCode.ERROR, reason))
            span.set_attribute("agnost.tool.outcome", reason)
            span.end()
            self._done.add(call_id)
