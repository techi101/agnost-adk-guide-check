"""OpenAI chat-completions stub (stream and non-stream). Triage agent hands off to the orders agent, which calls
get_order_status, then answers. Decides from the tools offered and whether a tool result is present."""
import json, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
def decide(req):
    tools = [t["function"]["name"] for t in req.get("tools", [])]
    msgs = req.get("messages", [])
    last = msgs[-1] if msgs else {}
    if any(n.startswith("transfer_to_") for n in tools) and last.get("role") == "user":
        n = next(n for n in tools if n.startswith("transfer_to_"))
        return {"tool": (n, "{}")}
    called = any(tc.get("function", {}).get("name") == "get_order_status"
                 for m in msgs for tc in (m.get("tool_calls") or []))
    if "get_order_status" in tools and not called:
        return {"tool": ("get_order_status", '{"order_id": "A-1042"}')}
    return {"text": "Your order A-1042 shipped yesterday."}
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        d = decide(req); cid = f"call_{int(time.time()*1000)%100000}"
        usage = {"prompt_tokens": 40, "completion_tokens": 8, "total_tokens": 48}
        if d.get("tool"):
            msg = {"role": "assistant", "content": None, "tool_calls": [{"id": cid, "type": "function",
                   "function": {"name": d["tool"][0], "arguments": d["tool"][1]}}]}; fin = "tool_calls"
        else:
            msg = {"role": "assistant", "content": d["text"]}; fin = "stop"
        if not req.get("stream"):
            out = {"id": "c1", "object": "chat.completion", "created": int(time.time()), "model": req.get("model"),
                   "choices": [{"index": 0, "message": msg, "finish_reason": fin}], "usage": usage}
            b = json.dumps(out).encode(); self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b); return
        self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.end_headers()
        delta = dict(msg); 
        if delta.get("tool_calls"): delta["tool_calls"] = [dict(delta["tool_calls"][0], index=0)]
        for c in [{"choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
                  {"choices": [{"index": 0, "delta": {}, "finish_reason": fin}]}, {"choices": [], "usage": usage}]:
            c.update({"id": "c1", "object": "chat.completion.chunk", "created": 0, "model": req.get("model")})
            self.wfile.write(f"data: {json.dumps(c)}\n\n".encode())
        self.wfile.write(b"data: [DONE]\n\n"); self.wfile.flush()
    def log_message(self, *a): pass
ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
