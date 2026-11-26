"""Run Agnost's Google ADK guide (OpenTelemetry path) end to end, offline.

What this does:
  1. Starts a local OTLP/HTTP receiver on 127.0.0.1 that stands in for
     otel.agnost.ai and saves every span it gets.
  2. Sets the exact env vars from https://docs.agnost.ai/google-adk.md
     (only the endpoint points at the local receiver).
  3. Runs a two-turn ADK support agent with the guide's AgnostPlugin, copied
     unchanged. The model is scripted (no API key, no network), so every run
     gives the same spans.
  4. Writes the received spans to out/spans.json for check_spans.py.

The scripted model makes two mistakes on purpose, both taken from the
examples on agnost.ai: it says 30 days when the policy tool said 14, and it
says a refund is processed without ever calling issue_refund.
"""

import asyncio
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.collector.trace.v1 import trace_service_pb2

HERE = Path(__file__).parent
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)
PORT = 4319
PLUGIN = os.environ.get("PLUGIN", "guide")  # "guide" = copied from the docs, "fixed" = agnost_adk_plugin.py
RECEIVED = []  # (headers, decoded request) per POST

# ---------- 1. local OTLP receiver ----------


class Receiver(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        req = trace_service_pb2.ExportTraceServiceRequest()
        req.ParseFromString(body)
        RECEIVED.append({
            "path": self.path,
            "org_header": self.headers.get("X-Agnost-Org-ID"),
            "request": MessageToDict(req),
        })
        resp = trace_service_pb2.ExportTraceServiceResponse().SerializeToString()
        self.send_response(200)
        self.send_header("Content-Type", "application/x-protobuf")
        self.end_headers()
        self.wfile.write(resp)

    def log_message(self, *args):  # keep the console quiet
        pass


server = HTTPServer(("127.0.0.1", PORT), Receiver)
threading.Thread(target=server.serve_forever, daemon=True).start()

# ---------- 2. env vars from the guide (step 2) ----------
os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = f"http://127.0.0.1:{PORT}/v1/traces"
os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] = "X-Agnost-Org-ID=test-org-id"
os.environ["OTEL_SERVICE_NAME"] = "my-adk-agent"
os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = os.environ.get(
    "CAPTURE", "SPAN_ONLY")

from google.adk.agents import Agent  # noqa: E402
from google.adk.models.base_llm import BaseLlm  # noqa: E402
from google.adk.models.llm_response import LlmResponse  # noqa: E402
from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.adk.telemetry.setup import maybe_set_otel_providers  # noqa: E402
from google.genai import types  # noqa: E402
from opentelemetry import trace  # noqa: E402

maybe_set_otel_providers()

# ---------- 3a. the guide's plugin, copied unchanged ----------


def _text(content):
    return "".join(p.text for p in (content.parts or []) if p.text) if content else ""


from google.adk.plugins.base_plugin import BasePlugin  # noqa: E402


class AgnostPlugin(BasePlugin):
    """Adds user.id and each turn's input and answer to ADK's root span."""

    def __init__(self):
        super().__init__(name="agnost")

    async def on_user_message_callback(self, *, invocation_context, user_message):
        span = trace.get_current_span()  # the root invoke_workflow span
        span.set_attribute("user.id", invocation_context.session.user_id)
        span.set_attribute("gen_ai.input.messages", json.dumps(
            [{"role": "user", "parts": [{"type": "text", "content": _text(user_message)}]}]))

    async def on_event_callback(self, *, invocation_context, event):
        if event.is_final_response() and _text(event.content):
            trace.get_current_span().set_attribute("gen_ai.output.messages", json.dumps(
                [{"role": "assistant", "parts": [{"type": "text", "content": _text(event.content)}]}]))


# ---------- 3b. a scripted model: same output every run, no API key ----------


class ScriptedSupportModel(BaseLlm):
    """Plays a support agent that makes two silent mistakes."""

    async def generate_content_async(self, llm_request, stream=False):
        last = llm_request.contents[-1]
        user_text = ""
        for c in llm_request.contents:
            if c.role == "user" and _text(c):
                user_text = _text(c)
        tool_result = any(p.function_response for p in (last.parts or []))

        if "return" in user_text.lower() and not tool_result:
            # turn 1, step 1: look up the policy
            yield LlmResponse(content=types.Content(role="model", parts=[
                types.Part(function_call=types.FunctionCall(
                    name="lookup_policy", args={"topic": "returns"}))]))
        elif "return" in user_text.lower():
            # turn 1, step 2: answer contradicts the tool output (14 vs 30)
            yield LlmResponse(content=types.Content(role="model", parts=[
                types.Part(text="Yes! You have 30 days to return it.")]))
        else:
            # turn 2: confirms a refund it never issued
            yield LlmResponse(content=types.Content(role="model", parts=[
                types.Part(text="Done. Your refund for order 1042 has been processed.")]))


def lookup_policy(topic: str) -> dict:
    """Returns the store policy for a topic."""
    return {"policy": "Returns are accepted within 14 days of delivery."}


def issue_refund(order_id: str) -> dict:
    """Issues a refund for an order."""
    return {"status": "refunded", "order_id": order_id}


root_agent = Agent(
    name="support_agent",
    model=ScriptedSupportModel(model="scripted-support"),
    instruction="Answer store questions. Use lookup_policy and issue_refund.",
    tools=[lookup_policy, issue_refund],
)

# ---------- 4. run two turns in one session (guide step 4) ----------


async def main():
    sessions = InMemorySessionService()
    await sessions.create_session(app_name="support_app", user_id="user-42",
                                  session_id="session-abc")
    if PLUGIN == "fixed":
        sys.path.insert(0, str(HERE))
        from agnost_adk_plugin import AgnostPlugin as Plugin
    else:
        Plugin = AgnostPlugin  # the guide's plugin, unchanged
    runner = Runner(agent=root_agent, app_name="support_app",
                    session_service=sessions, plugins=[Plugin()])
    for text in ["Can I return the jacket I bought last week?",
                 "Ok, please refund order 1042."]:
        async for event in runner.run_async(
            user_id="user-42", session_id="session-abc",
            new_message=types.Content(role="user", parts=[types.Part(text=text)]),
        ):
            if event.is_final_response() and event.content and event.content.parts:
                print("agent:", event.content.parts[0].text)


asyncio.run(main())
trace.get_tracer_provider().force_flush()
server.shutdown()

import google.adk  # noqa: E402

capture = os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"]
meta = {"adk_version": google.adk.__version__, "python": sys.version.split()[0],
        "capture": capture, "plugin": PLUGIN}
name = f"spans_adk{google.adk.__version__}_{capture.lower()}_{PLUGIN}.json"
(OUT / name).write_text(json.dumps({"meta": meta, "posts": RECEIVED}, indent=1))
print(f"received {len(RECEIVED)} OTLP posts -> out/{name}")
