#!/usr/bin/env python3
"""
JAX Permit Search — Local Bridge Server
Runs silently in the background on port 8765.
The BRRRR Calculator HTML calls this server when you click 🔍 Fetch City Permits.
The server runs the actual permit search via Opera/VPN and returns JSON results.

Start this via:  Start Everything.bat
"""
import http.server
import json
import os
import subprocess
import sys
import urllib.parse
from pathlib import Path

PORT        = 8765
HERE        = Path(__file__).parent
SEARCH_SCRIPT = HERE / "search_permits.py"
PYTHON      = sys.executable   # same python that's running this server

# How long (seconds) to wait for the permit search before giving up
SEARCH_TIMEOUT = 90


class Handler(http.server.BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        # ── /health  ──────────────────────────────────────────────────────────
        if parsed.path == "/health":
            self.send_response(200)
            self._cors()
            self._finish_json({"status": "ok"})
            return

        # ── /search?address=...  ──────────────────────────────────────────────
        if parsed.path == "/search":
            address = params.get("address", [""])[0].strip()
            if not address:
                self.send_response(400)
                self._cors()
                self._finish_json({"error": "No address provided"})
                return

            print(f"[server] Searching permits for: {address}")

            try:
                result = subprocess.run(
                    [PYTHON, str(SEARCH_SCRIPT), address, "--json"],
                    capture_output=True,
                    text=True,
                    timeout=SEARCH_TIMEOUT,
                    cwd=str(HERE)
                )
                stdout = result.stdout.strip()
                if not stdout:
                    raise ValueError(f"Empty output from search script. stderr: {result.stderr[:500]}")

                data = json.loads(stdout)

                # If the script returned {"error": "..."} propagate it
                if isinstance(data, dict) and "error" in data:
                    print(f"[server] Search error: {data['error']}")
                    self.send_response(502)
                    self._cors()
                    self._finish_json({"error": data["error"]})
                    return

                print(f"[server] Found {len(data)} permit(s)")
                self.send_response(200)
                self._cors()
                self._finish_json({"permits": data, "address": address})

            except subprocess.TimeoutExpired:
                msg = f"Search timed out after {SEARCH_TIMEOUT}s. Is Opera running with VPN?"
                print(f"[server] {msg}")
                self.send_response(504)
                self._cors()
                self._finish_json({"error": msg})

            except json.JSONDecodeError as e:
                msg = f"Bad JSON from search script: {e}"
                print(f"[server] {msg}")
                self.send_response(500)
                self._cors()
                self._finish_json({"error": msg})

            except Exception as e:
                msg = str(e)
                print(f"[server] Unexpected error: {msg}")
                self.send_response(500)
                self._cors()
                self._finish_json({"error": msg})

            return

        self.send_response(404)
        self._cors()
        self._finish_json({"error": "Unknown path"})

    # ── helpers ───────────────────────────────────────────────────────────────

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _finish_json(self, obj):
        body = json.dumps(obj).encode()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        if int(args[1]) >= 400:
            print(f"[server] {self.address_string()} - {fmt % args}")


if __name__ == "__main__":
    print(f"[server] JAX Permit Bridge running on http://localhost:{PORT}")
    print(f"[server] Keep this window open while you use the calculator.")
    print(f"[server] Close this window to stop the server.")
    with http.server.ThreadingHTTPServer(("", PORT), Handler) as srv:
        srv.serve_forever()
