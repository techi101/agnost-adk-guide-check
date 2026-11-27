"""Compatibility checks for AgnostTracingProcessor against the real OpenAI Agents SDK (criterion 3 of the
openai-agents-python tracing listing policy). Nothing leaves this machine: the SDK's default OpenAI exporter is
replaced, the model is a local stub, and Agnost's capture API is a local stand-in.

  python check.py            -> prints a report and writes report.json
"""
import asyncio, importlib.metadata as md, json, socket, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).parent
PY = sys.executable


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


RPORT, MPORT = free_port(), free_port()
procs = [subprocess.Popen([PY, str(HERE / "capture_receiver.py"), str(RPORT)]),
         subprocess.Popen([PY, str(HERE / "fake_chat.py"), str(MPORT)])]
time.sleep(2)

from openai import AsyncOpenAI
from agents import (Agent, OpenAIChatCompletionsModel, RunConfig, Runner, function_tool, set_trace_processors)
from agnost.integrations.openai_agents import AgnostTracingProcessor

client = AsyncOpenAI(api_key="test", base_url=f"http://127.0.0.1:{MPORT}/v1")
model = OpenAIChatCompletionsModel(model="gpt-4.1-mini", openai_client=client)


@function_tool
def get_order_status(order_id: str) -> str:
    """Look up an order."""
    return json.dumps({"order_id": order_id, "status": "shipped", "card_last4": "4242"})


orders = Agent(name="orders-agent", instructions="Answer order questions.", tools=[get_order_status], model=model)
triage = Agent(name="triage-agent", instructions="Route to the right agent.", handoffs=[orders], model=model)


def received():
    return json.loads((HERE / "received.json").read_text(encoding="utf-8"))


def run(label, processor, include_sensitive=True, streamed=False):
    set_trace_processors([processor])  # replaces OpenAI's default exporter: nothing is sent to OpenAI
    before = len(received())
    cfg = RunConfig(group_id=f"conv-{label}", trace_metadata={"user_id": "u-42"},
                    trace_include_sensitive_data=include_sensitive)
    t0 = time.time()
    if streamed:
        async def go():
            r = Runner.run_streamed(triage, "Where is my order A-1042?", run_config=cfg)
            async for _ in r.stream_events():
                pass
            return r.final_output
        out = asyncio.run(go())
    else:
        out = Runner.run_sync(triage, "Where is my order A-1042?", run_config=cfg).final_output
    run_s = time.time() - t0
    t1 = time.time(); flushed = processor.force_flush(); flush_s = time.time() - t1
    time.sleep(0.5)
    return out, run_s, flushed, flush_s, received()[before:]


def summarize(posts):
    sessions = [p for p in posts if p["path"].endswith("capture-session")]
    events = [p for p in posts if p["path"].endswith("capture-event")]
    blob = json.dumps(posts)
    return {"sessions": len(sessions), "events": len(events), "org_headers": sorted({p["org"] for p in posts if p["org"]}),
            "event_names": sorted({str(p["body"].get("primitive_name") or p["body"].get("name") or p["body"].get("event_name") or "?") for p in events}),
            "has_tool_call": any(p["body"].get("primitive_type") == "tool" for p in events), "has_tool_args": "order_id" in blob, "has_tool_result": "4242" in blob, "has_handoff": "orders-agent" in blob,
            "has_user_text": "Where is my order" in blob, "has_answer": "shipped yesterday" in blob}


report = {"versions": {"agnost": md.version("agnost"), "openai-agents": md.version("openai-agents"),
                       "python": sys.version.split()[0]}}
try:
    ep = f"http://127.0.0.1:{RPORT}"
    out, rs, fl, fs, posts = run("basic", AgnostTracingProcessor(org_id="org-test", endpoint=ep))
    report["1_basic_run"] = {"final_output": out, "flushed": fl, **summarize(posts)}
    report["1_basic_run"]["sample_event"] = next((p["body"] for p in posts if p["path"].endswith("capture-event")), None)

    out, rs, fl, fs, posts = run("streamed", AgnostTracingProcessor(org_id="org-test", endpoint=ep), streamed=True)
    report["2_streamed_run"] = {"final_output": out, "flushed": fl, **summarize(posts)}

    out, rs, fl, fs, posts = run("no-sensitive", AgnostTracingProcessor(org_id="org-test", endpoint=ep), include_sensitive=False)
    report["3_trace_include_sensitive_data_false"] = {"final_output": out, **summarize(posts)}

    out, rs, fl, fs, posts = run("no-content", AgnostTracingProcessor(org_id="org-test", endpoint=ep, include_content=False))
    report["4_include_content_false"] = {"final_output": out, **summarize(posts)}

    (HERE / "FAIL_MODE").write_text("1")
    try:
        out, rs, fl, fs, posts = run("export-500", AgnostTracingProcessor(org_id="org-test", endpoint=ep, flush_timeout=5))
        report["5_export_returns_500"] = {"final_output": out, "run_seconds": round(rs, 2), "flushed": fl,
                                           "flush_seconds": round(fs, 2), "posts_attempted": len(posts)}
    finally:
        (HERE / "FAIL_MODE").unlink(missing_ok=True)

    dead = f"http://127.0.0.1:{free_port()}"  # nothing listening
    out, rs, fl, fs, posts = run("endpoint-down", AgnostTracingProcessor(org_id="org-test", endpoint=dead, timeout=2, flush_timeout=5))
    report["6_endpoint_unreachable"] = {"final_output": out, "run_seconds": round(rs, 2), "flushed": fl, "flush_seconds": round(fs, 2)}

    p = AgnostTracingProcessor(org_id="org-test", endpoint=ep)
    set_trace_processors([p]); before = len(received())
    Runner.run_sync(triage, "Where is my order A-1042?", run_config=RunConfig(group_id="conv-shutdown"))
    t1 = time.time(); p.shutdown(); sd = time.time() - t1; time.sleep(0.5)
    report["7_shutdown_delivers"] = {"shutdown_seconds": round(sd, 2), **summarize(received()[before:])}
finally:
    for pr in procs:
        pr.terminate()

(HERE / "report.json").write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
print(json.dumps({k: (v if k != "1_basic_run" else {x: y for x, y in v.items() if x != "sample_event"}) for k, v in report.items()}, indent=1, default=str))
