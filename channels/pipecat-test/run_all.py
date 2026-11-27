"""One command: starts a local OTLP receiver (stand-in for otel.agnost.ai) and a fake OpenAI server, runs every
scenario with and without AgnostToolSpanObserver, and writes results.json.

  python run_all.py            (inside a venv with: pip install "pipecat-ai[tracing,openai]" opentelemetry-exporter-otlp-proto-http)
"""
import json, os, socket, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).parent
PY = sys.executable
SCENARIOS = ["baseline", "parallel", "no_followup", "hangup", "interrupt"]


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def spans_by_service(received):
    out = {}
    for e in received:
        for rs in e["body"].get("resourceSpans", []):
            svc = next(next(iter(a["value"].values())) for a in rs["resource"]["attributes"] if a["key"] == "service.name")
            for ss in rs.get("scopeSpans", []):
                out.setdefault(svc, []).extend(ss.get("spans", []))
    return out


def tool_calls_visible(spans):
    """Tool calls Agnost can see: execute_tool spans, or assistant tool_calls inside a later LLM span's input."""
    seen = set()
    for s in spans:
        a = {x["key"]: next(iter(x["value"].values()), None) for x in s.get("attributes", [])}
        if a.get("gen_ai.operation.name") == "execute_tool":
            seen.add(a.get("gen_ai.tool.call.id"))
        if s["name"] == "llm" and a.get("input"):
            for m in json.loads(a["input"]):
                for tc in m.get("tool_calls") or []:
                    seen.add(tc.get("id"))
    return sorted(x for x in seen if x)


def main():
    rport, fport = free_port(), free_port()
    out_file = HERE / "received.json"
    procs = [subprocess.Popen([PY, str(HERE / "receiver.py"), str(rport)]),
             subprocess.Popen([PY, str(HERE / "fake_openai.py"), str(fport)])]
    time.sleep(2)
    env = dict(os.environ, PYTHONPATH=str(HERE / "shim"), PYTHONIOENCODING="utf-8", PYTHONWARNINGS="ignore",
               OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=f"http://127.0.0.1:{rport}/v1/traces",
               OTEL_EXPORTER_OTLP_HEADERS="X-Agnost-Org-ID=00000000-test", OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf",
               FAKE_OPENAI=f"http://127.0.0.1:{fport}/v1")
    expected = {"baseline": 1, "parallel": 2, "no_followup": 1, "hangup": 1, "interrupt": 1}
    try:
        for scen in SCENARIOS:
            for flag in ([], ["--observer"]):
                subprocess.run([PY, str(HERE / "scenarios.py"), scen, *flag], env=env, timeout=90,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        by = spans_by_service(json.loads(out_file.read_text(encoding="utf-8")))
    finally:
        for p in procs:
            p.terminate()
    results = []
    for scen in SCENARIOS:
        row = {"scenario": scen, "tool_calls_made": expected[scen]}
        for mode, svc in (("recipe_only", f"pipecat-{scen}"), ("with_observer", f"pipecat-{scen}-fix")):
            row[mode] = len(tool_calls_visible(by.get(svc, [])))
        results.append(row)
        print(f"{scen:12} made {row['tool_calls_made']}  visible: recipe only {row['recipe_only']}, with observer {row['with_observer']}")
    (HERE / "results.json").write_text(json.dumps({"pipecat": "1.17.0", "results": results}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
