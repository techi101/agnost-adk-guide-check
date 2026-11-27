"""Stand-in for Agnost's capture API (api.agnost.ai). Records every POST to received.json.
FAIL_MODE file present -> answers 500 (to test failed exports)."""
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
HERE = Path(__file__).parent; OUT = HERE / "received.json"; GOT = []
class R(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        fail = (HERE / "FAIL_MODE").exists()
        try: data = json.loads(body)
        except Exception: data = {"raw": body[:200].decode("utf-8", "ignore")}
        GOT.append({"path": self.path, "org": self.headers.get("X-Org-Id"), "failed": fail, "body": data})
        OUT.write_text(json.dumps(GOT, indent=1), encoding="utf-8")
        self.send_response(500 if fail else 200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(b'{"error":"test"}' if fail else b'{"ok":true}')
    def log_message(self, *a): pass
if __name__ == "__main__":
    OUT.write_text("[]", encoding="utf-8")
    ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), R).serve_forever()
