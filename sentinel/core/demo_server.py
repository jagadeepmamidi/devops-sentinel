"""Finite local HTTP app used by `sentinel demo`."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread


class _DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/ok"):
            body = b'{"status":"ok","service":"demo"}'
            self.send_response(200)
        else:
            body = b'{"status":"error","service":"demo"}'
            self.send_response(503)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


class DemoServer:
    def __init__(self, host: str = "127.0.0.1"):
        self.server = ThreadingHTTPServer((host, 0), _DemoHandler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)

    @property
    def ok_url(self) -> str:
        host, port = self.server.server_address[:2]
        return f"http://{host}:{port}/ok"

    @property
    def fail_url(self) -> str:
        host, port = self.server.server_address[:2]
        return f"http://{host}:{port}/fail"

    def start(self) -> "DemoServer":
        self.thread.start()
        return self

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def __enter__(self) -> "DemoServer":
        return self.start()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()
