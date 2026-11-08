"""Tiny health endpoint.

Telegram polling needs no port, but some hosts (Render, Koyeb, Fly) insist on a
service that answers HTTP, otherwise they mark the deploy unhealthy. When the
``PORT`` variable exists we serve ``/`` with ``ok`` on a background thread.
"""
from __future__ import annotations

import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

log = logging.getLogger(__name__)


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        body = b"anime filter bot is running\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args) -> None:  # silence per-request logging
        return


def start_if_needed() -> threading.Thread | None:
    port = os.getenv("PORT", "").strip()
    if not port.isdigit():
        return None

    def serve() -> None:
        server = ThreadingHTTPServer(("0.0.0.0", int(port)), _Handler)
        log.info("health endpoint on 0.0.0.0:%s", port)
        server.serve_forever()

    thread = threading.Thread(target=serve, daemon=True, name="health")
    thread.start()
    return thread
