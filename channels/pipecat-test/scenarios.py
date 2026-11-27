"""Which Pipecat tool calls reach Agnost? Follows the skill/docs recipe exactly, then checks the exported spans.

Agnost's Pipecat docs: "Pipecat does not create spans for function execution. Agnost recovers each call and its
result from the context of the LLM request that follows it." This script tests the cases where no LLM request follows.

Usage: python scenarios.py <scenario> [--observer]
  baseline   user asks about an order, tool runs, LLM answers            (a following LLM request exists)
  no_followup  end_call-style tool returns with run_llm=False            (no following request)
  hangup     caller hangs up while the tool is still running             (worker cancelled mid-call)
  interrupt  user talks over a slow tool; Pipecat cancels the call       (FunctionCallCancelFrame)
--observer adds AgnostToolSpanObserver (agnost_tool_spans.py), the proposed fix.
"""
import asyncio, json, os, sys
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from pipecat.utils.tracing.setup import setup_tracing
from pipecat.frames.frames import (EndFrame, FunctionCallResultProperties, LLMMessagesAppendFrame,
                                   UserStartedSpeakingFrame, UserStoppedSpeakingFrame, InterruptionFrame)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.worker import PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema

SCEN = sys.argv[1]
USE_OBS = "--observer" in sys.argv
LLM = os.environ.get("LLM", "openai")
setup_tracing(service_name=f"pipecat-{SCEN}" + ("-fix" if USE_OBS else "") + ("" if LLM == "openai" else f"-{LLM}"), exporter=OTLPSpanExporter())

PROMPTS = {"baseline": "Where is my order A-1042?", "no_followup": "Please end the call, order A-1042 is fine.",
           "hangup": "Where is my order A-1042?", "interrupt": "Where is my order A-1042?", "parallel": "Check my two orders A-1042 and B-2077.", "timeout": "Where is my order A-1042?", "error": "Where is my order A-1042?"}


async def get_order_status(params):
    if SCEN in ("hangup", "interrupt"):
        await asyncio.sleep(4)  # slow backend
    if SCEN == "timeout":
        await asyncio.sleep(10)  # longer than timeout_secs below
    if SCEN == "error":
        raise RuntimeError("order service returned 503")
    if SCEN == "no_followup":
        await params.result_callback({"ended": True}, properties=FunctionCallResultProperties(run_llm=False))
    else:
        await params.result_callback({"order_id": params.arguments.get("order_id"), "status": "shipped"})


async def main():
    if LLM == "anthropic":
        from anthropic import AsyncAnthropic
        from pipecat.services.anthropic.llm import AnthropicLLMService
        llm = AnthropicLLMService(api_key="test", model="claude-sonnet-4-5",
                                  client=AsyncAnthropic(api_key="test", base_url=os.environ["FAKE_ANTHROPIC"]))
    else:
        llm = OpenAILLMService(api_key="test", base_url=os.environ["FAKE_OPENAI"], model="gpt-4.1-mini")
    llm.register_function("get_order_status", get_order_status, cancel_on_interruption=True,
                          timeout_secs=2 if SCEN == "timeout" else None)
    tools = ToolsSchema(standard_tools=[FunctionSchema(name="get_order_status", description="Look up an order",
                                                       properties={"order_id": {"type": "string"}}, required=["order_id"])])
    context = LLMContext([{"role": "system", "content": "You are a support agent."}], tools=tools)
    agg = LLMContextAggregatorPair(context)
    observers = []
    if USE_OBS:
        from agnost_tool_spans import AgnostToolSpanObserver
        observers.append(AgnostToolSpanObserver())
    worker = PipelineWorker(Pipeline([agg.user(), llm, agg.assistant()]), observers=observers,
                            enable_tracing=True, conversation_id=f"call-{SCEN}",
                            additional_span_attributes={"enduser.id": "user-42"})

    async def drive():
        await asyncio.sleep(1)
        await worker.queue_frames([UserStartedSpeakingFrame(), UserStoppedSpeakingFrame(),
                                   LLMMessagesAppendFrame([{"role": "user", "content": PROMPTS[SCEN]}], run_llm=True)])
        if SCEN == "hangup":
            await asyncio.sleep(1.5)
            await worker.cancel(reason="caller hung up")
            return
        if SCEN == "interrupt":
            await asyncio.sleep(1.5)
            await worker.queue_frames([UserStartedSpeakingFrame(), InterruptionFrame()])
            await asyncio.sleep(0.5)
            await worker.queue_frames([UserStoppedSpeakingFrame()])
            await asyncio.sleep(1)
            await worker.cancel(reason="caller hung up")
            return
        await asyncio.sleep(6 if SCEN == "timeout" else 3)
        await worker.queue_frame(EndFrame())

    await asyncio.gather(PipelineRunner(handle_sigint=False).run(worker), drive())
    trace.get_tracer_provider().force_flush()
    roles = [(m.get("role"), "tool_calls" in m) for m in context.get_messages()]
    print("CONTEXT", json.dumps(roles))


asyncio.run(main())
