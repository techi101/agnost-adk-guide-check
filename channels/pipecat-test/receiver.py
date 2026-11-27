"""Local stand-in for otel.agnost.ai: records OTLP/HTTP protobuf trace posts to received.json. Run: python receiver.py 4321"""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.collector.trace.v1 import trace_service_pb2

OUT = Path(__file__).parent / "received.json"
GOT = []


class R(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.headers.get("Transfer-Encoding", "").lower() == "chunked":
            body = b""
            while True:
                size = int(self.rfile.readline().strip() or b"0", 16)
                if size == 0:
                    self.rfile.readline()
                    break
                body += self.rfile.read(size)
                self.rfile.readline()
        else:
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.headers.get("Content-Encoding", "").lower() == "gzip":
            import gzip
            body = gzip.decompress(body)
        entry = {"path": self.path, "org": self.headers.get("X-Agnost-Org-ID"),
                 "content_type": self.headers.get("Content-Type"), "bytes": len(body), "headers": dict(self.headers)}
        try:
            req = trace_service_pb2.ExportTraceServiceRequest()
            req.ParseFromString(body)
            entry["body"] = MessageToDict(req)
        except Exception as e:  # e.g. JSON instead of protobuf
            entry["parse_error"] = str(e)[:200]
            entry["raw_prefix"] = body[:200].decode("utf-8", "ignore")
        GOT.append(entry)
        OUT.write_text(json.dumps(GOT, indent=1), encoding="utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/x-protobuf")
        self.end_headers()
        self.wfile.write(trace_service_pb2.ExportTraceServiceResponse().SerializeToString())

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    OUT.write_text("[]", encoding="utf-8")
    HTTPServer(("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 4321), R).serve_forever()
