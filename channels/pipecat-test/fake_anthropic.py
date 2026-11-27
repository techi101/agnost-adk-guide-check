"""Minimal Anthropic Messages API (streaming) stub. Calls get_order_status once per order mentioned, then answers."""
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

def ev(t, d):
    d["type"] = t
    return f"event: {t}\ndata: {json.dumps(d)}\n\n".encode()

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        msgs = req.get("messages", [])
        has_result = any(isinstance(m.get("content"), list) and any(b.get("type") == "tool_result" for b in m["content"]) for m in msgs)
        last_user = ""
        for m in reversed(msgs):
            if m.get("role") == "user":
                c = m.get("content"); last_user = c if isinstance(c, str) else json.dumps(c); break
        self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.end_headers()
        w = self.wfile.write
        w(ev("message_start", {"message": {"id": "msg_1", "type": "message", "role": "assistant", "content": [],
            "model": req.get("model"), "stop_reason": None, "stop_sequence": None, "usage": {"input_tokens": 42, "output_tokens": 1}}}))
        if req.get("tools") and "order" in last_user.lower() and not has_result:
            w(ev("content_block_start", {"index": 0, "content_block": {"type": "tool_use", "id": "toolu_1", "name": "get_order_status", "input": {}}}))
            w(ev("content_block_delta", {"index": 0, "delta": {"type": "input_json_delta", "partial_json": '{"order_id": "A-1042"}'}}))
            w(ev("content_block_stop", {"index": 0}))
            stop = "tool_use"
        else:
            text = "Your order A-1042 shipped yesterday." if has_result else "Hi! How can I help you today?"
            w(ev("content_block_start", {"index": 0, "content_block": {"type": "text", "text": ""}}))
            for word in text.split(" "):
                w(ev("content_block_delta", {"index": 0, "delta": {"type": "text_delta", "text": word + " "}}))
            w(ev("content_block_stop", {"index": 0}))
            stop = "end_turn"
        w(ev("message_delta", {"delta": {"stop_reason": stop, "stop_sequence": None}, "usage": {"output_tokens": 9}}))
        w(ev("message_stop", {})); self.wfile.flush()
    def log_message(self, *a): pass

ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
