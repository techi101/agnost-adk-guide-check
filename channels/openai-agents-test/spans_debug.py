import json, socket, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).parent
s = socket.socket(); s.bind(("127.0.0.1", 0)); MP = s.getsockname()[1]; s.close()
pr = subprocess.Popen([sys.executable, str(HERE / "fake_chat.py"), str(MP)]); time.sleep(1.5)
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, RunConfig, Runner, function_tool, set_trace_processors
from agents.tracing import TracingProcessor
class Dbg(TracingProcessor):
    def on_trace_start(self, t): pass
    def on_trace_end(self, t): pass
    def on_span_start(self, s): pass
    def on_span_end(self, s):
        d = s.span_data; print("SPAN", d.type, getattr(d, "name", ""), str(getattr(d, "output", ""))[:60])
    def shutdown(self): pass
    def force_flush(self): pass
m = OpenAIChatCompletionsModel(model="gpt-4.1-mini", openai_client=AsyncOpenAI(api_key="t", base_url=f"http://127.0.0.1:{MP}/v1"))
@function_tool
def get_order_status(order_id: str) -> str:
    """Look up an order."""
    return json.dumps({"order_id": order_id, "status": "shipped", "card_last4": "4242"})
orders = Agent(name="orders-agent", instructions="x", tools=[get_order_status], model=m)
triage = Agent(name="triage-agent", instructions="x", handoffs=[orders], model=m)
set_trace_processors([Dbg()])
try:
    print("OUT", Runner.run_sync(triage, "Where is my order A-1042?", run_config=RunConfig(group_id="g")).final_output)
finally:
    pr.terminate()
