#!/usr/bin/env python3
"""
Mock server for testing ptvgym_monitor.py locally.

It serves the "no products" page first, then after SWITCH_AFTER_SECONDS
automatically switches to the "products available" page — simulating
the real site going live.

Usage:
    python mock_server.py

Then in ptvgym_monitor.py temporarily change TARGET_URL to:
    TARGET_URL = "http://localhost:8765/"
And set CHECK_INTERVAL_SECONDS = 10 for fast feedback.
"""

import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

PORT = 8765
SWITCH_AFTER_SECONDS = 30  # how long to serve the empty page before "going live"

EMPTY_PAGE = Path("./empty.html").read_text()
PRODUCTS_PAGE = Path("./products.html").read_text()

state = {"products_live": False}


def flip_switch():
    time.sleep(SWITCH_AFTER_SECONDS)
    state["products_live"] = True
    print(f"\n🟢 Mock server: switched to PRODUCTS page (simulating site going live!)\n")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        page = PRODUCTS_PAGE if state["products_live"] else EMPTY_PAGE
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode())

    def log_message(self, format, *args):
        status = "PRODUCTS" if state["products_live"] else "empty"
        print(f"  [{status}] {self.address_string()} - {format % args}")


if __name__ == "__main__":
    threading.Thread(target=flip_switch, daemon=True).start()
    print(f"Mock server running at http://localhost:{PORT}/")
    print(f"Serving EMPTY page for {SWITCH_AFTER_SECONDS}s, then switching to PRODUCTS.")
    print(f"Point your bot at: TARGET_URL = 'http://localhost:{PORT}/'")
    print(f"Tip: set CHECK_INTERVAL_SECONDS = 10 in the bot for fast testing.\n")
    HTTPServer(("", PORT), Handler).serve_forever()
