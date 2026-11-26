"""Read every out/spans_*.json and check what Agnost would receive.

Checks per run (one row per file):
  root_user        root span has user.id
  root_conv        root span has gen_ai.conversation.id
  root_input       root span has the user's message
  root_output      root span has the agent's final answer
  tool_evidence    the tool span has its arguments and result
  catch_contradiction  the spans alone show the 14 vs 30 days mismatch
  catch_false_refund   the spans alone show "refund processed" with no issue_refund call

The last two are plain code checks, not an LLM. They only ask: is the evidence
Agnost needs present in what was exported?
Writes out/results.json for the web page.
"""

import json
import re
from pathlib import Path

OUT = Path(__file__).parent / "out"


def spans_of(doc):
    for post in doc["posts"]:
        for rs in post["request"].get("resourceSpans", []):
            for ss in rs.get("scopeSpans", []):
                for s in ss.get("spans", []):
                    attrs = {a["key"]: next(iter(a["value"].values()), "")
                             for a in s.get("attributes", [])}
                    yield {"name": s["name"], "parent": s.get("parentSpanId"), "attrs": attrs}


def check(doc):
    spans = list(spans_of(doc))
    roots = [s for s in spans if not s["parent"]]
    tools = [s for s in spans if s["name"].startswith("execute_tool")]

    def all_roots(key):
        return bool(roots) and all(key in r["attrs"] for r in roots)

    def tool_has_evidence(t):
        a = t["attrs"]
        args = a.get("gen_ai.tool.call.arguments") or a.get("gcp.vertex.agent.tool_call_args")
        res = a.get("gen_ai.tool.call.result") or a.get("gcp.vertex.agent.tool_response")
        return bool(args and res and res != "{}" and args != "{}")

    blob = json.dumps([s["attrs"] for s in spans])
    tool_said_14 = any("14 days" in json.dumps(t["attrs"]) for t in tools)
    agent_said_30 = "30 days" in blob
    refund_claimed = "refund for order 1042 has been processed" in blob
    refund_tool_called = any(s["name"] == "execute_tool issue_refund" for s in spans)

    return {
        "root_names": sorted({r["name"].split(" ")[0] for r in roots}),
        "root_user": all_roots("user.id"),
        "root_conv": all_roots("gen_ai.conversation.id"),
        "root_input": all_roots("gen_ai.input.messages"),
        "root_output": all_roots("gen_ai.output.messages"),
        "tool_evidence": bool(tools) and all(tool_has_evidence(t) for t in tools),
        "catch_contradiction": tool_said_14 and agent_said_30,
        "catch_false_refund": refund_claimed and not refund_tool_called,
        "span_count": len(spans),
    }


rows = []
for f in sorted(OUT.glob("spans_*.json")):
    doc = json.loads(f.read_text())
    row = {**doc["meta"], "file": f.name, **check(doc)}
    rows.append(row)
    flags = " ".join(f"{k}={'Y' if row[k] else 'n'}" for k in
                     ["root_user", "root_conv", "root_input", "root_output",
                      "tool_evidence", "catch_contradiction", "catch_false_refund"])
    print(f"ADK {row['adk_version']:7} {row['capture']:10} {row['plugin']:5} roots={row['root_names']} {flags}")

(OUT / "results.json").write_text(json.dumps(rows, indent=1))
