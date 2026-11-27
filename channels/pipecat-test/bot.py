"""Follows the skill's pipecat recipe exactly, against a local OTLP receiver and a fake OpenAI server."""
import asyncio, os
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry import trace
from pipecat.utils.tracing.setup import setup_tracing
from pipecat.frames.frames import LLMMessagesAppendFrame, EndFrame, UserStartedSpeakingFrame, UserStoppedSpeakingFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.worker import PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema

# recipe: env vars + setup_tracing(service_name=..., exporter=OTLPSpanExporter()) before the worker
setup_tracing(service_name="pipecat-agnost-test", exporter=OTLPSpanExporter())

async def get_order_status(params):
    await params.result_callback({"order_id": "A-1042", "status": "shipped"})

async def main():
    llm = OpenAILLMService(api_key="test", base_url=os.environ["FAKE_OPENAI"], model="gpt-4.1-mini")
    llm.register_function("get_order_status", get_order_status)
    tools = ToolsSchema(standard_tools=[FunctionSchema(name="get_order_status", description="Look up an order",
        properties={"order_id": {"type": "string"}}, required=["order_id"])])
    context = LLMContext([{"role": "system", "content": "You are a support agent."}], tools=tools)
    agg = LLMContextAggregatorPair(context)
    worker = PipelineWorker(Pipeline([agg.user(), llm, agg.assistant()]),
                            enable_tracing=True, conversation_id="call-123",
                            additional_span_attributes={"enduser.id": "user-42"})
    async def drive():
        await asyncio.sleep(1)
        for text in ["Hello", "Where is my order A-1042?"]:
            await worker.queue_frames([UserStartedSpeakingFrame(), UserStoppedSpeakingFrame(),
                                       LLMMessagesAppendFrame([{"role": "user", "content": text}], run_llm=True)])
            await asyncio.sleep(3)
        await worker.queue_frame(EndFrame())
    await asyncio.gather(PipelineRunner(handle_sigint=False).run(worker), drive())
    trace.get_tracer_provider().force_flush()  # recipe: flush before a short-lived bot exits
    print("context:", [(m.get("role"), str(m.get("content"))[:50]) for m in context.get_messages()])

asyncio.run(main())
