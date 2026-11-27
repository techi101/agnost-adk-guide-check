"""Reads received.json and reports, per service (scenario), whether the tool call reached the trace."""
import json, sys
from collections import defaultdict
d = json.load(open("received.json", encoding="utf-8"))
by = defaultdict(list)
for e in d:
    for rs in e["body"].get("resourceSpans", []):
        svc = next((next(iter(a["value"].values())) for a in rs["resource"]["attributes"] if a["key"] == "service.name"), "?")
        for ss in rs.get("scopeSpans", []):
            by[svc] += ss.get("spans", [])
out = {}
for svc, spans in by.items():
    found = []
    for s in spans:
        attrs = {a["key"]: next(iter(a["value"].values()), None) for a in s.get("attributes", [])}
        for k, v in attrs.items():
            if k == "tools":  # the tool *definitions* list, not a call
                continue
            if "A-1042" in str(v) and ("get_order_status" in str(v) or "tool" in k or s["name"].startswith("tool")):
                found.append(f"{s['name']}.{k}")
    out[svc] = {"spans": len(spans), "names": sorted({s['name'] for s in spans}), "tool_call_visible_in": sorted(set(found))}
print(json.dumps(out, indent=1))
