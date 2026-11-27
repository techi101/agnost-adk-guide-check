"""Minimal OpenAI-compatible /v1/chat/completions (streaming) so the test needs no API key.
First request with tools and no tool result -> calls get_order_status; otherwise replies with text."""
import json, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

def chunk(delta, finish=None):
    return {"id": "c1", "object": "chat.completion.chunk", "created": int(time.time()), "model": "gpt-4.1-mini",
            "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        msgs = req.get("messages", [])
        has_tool_result = any(m.get("role") == "tool" for m in msgs)
        last_user = next((m["content"] for m in reversed(msgs) if m.get("role") == "user"), "")
        self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.end_headers()
        out = []
        if req.get("tools") and "two orders" in str(last_user).lower() and not has_tool_result:
            for i, oid in enumerate(["A-1042", "B-2077"]):
                out.append(chunk({"role": "assistant", "tool_calls": [{"index": i, "id": f"call_{i+1}", "type": "function",
                           "function": {"name": "get_order_status", "arguments": json.dumps({"order_id": oid})}}]}))
            out.append(chunk({}, "tool_calls"))
        elif req.get("tools") and "order" in str(last_user).lower() and not has_tool_result:
            out.append(chunk({"role": "assistant", "tool_calls": [{"index": 0, "id": "call_1", "type": "function",
                       "function": {"name": "get_order_status", "arguments": ""}}]}))
            out.append(chunk({"tool_calls": [{"index": 0, "function": {"arguments": '{"order_id": "A-1042"}'}}]}))
            out.append(chunk({}, "tool_calls"))
        else:
            text = "Your order A-1042 shipped yesterday." if has_tool_result else "Hi! How can I help you today?"
            out.append(chunk({"role": "assistant", "content": ""}))
            for w in text.split(" "):
                out.append(chunk({"content": w + " "}))
            out.append(chunk({}, "stop"))
        u = {"id": "c1", "object": "chat.completion.chunk", "created": 0, "model": "gpt-4.1-mini", "choices": [],
             "usage": {"prompt_tokens": 42, "completion_tokens": 9, "total_tokens": 51}}
        out.append(u)
        for c in out:
            self.wfile.write(f"data: {json.dumps(c)}\n\n".encode()); self.wfile.flush()
        self.wfile.write(b"data: [DONE]\n\n"); self.wfile.flush()
    def log_message(self, *a): pass

ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
