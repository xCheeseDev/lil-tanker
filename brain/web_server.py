"""Tiny dashboard server (stdlib only). Runs in a thread next to the brain.

Serves web/dashboard.html and a small JSON API:
  GET  /api/status   -> {connected, dist_cm, batt_v, said:[...]}
  POST /api/drive    {ms, speed}   manual nudge
  POST /api/stop     {}
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_link = None
_said = None


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/status":
            try:
                s = _link.sensors() if _link.connected else {}
            except Exception:
                s = {}
            return self._json({
                "connected": _link.connected,
                "dist_cm": s.get("dist_cm"),
                "batt_v": s.get("batt_v"),
                "said": list(_said)[-20:],
            })
        if self.path in ("/", "/index.html"):
            try:
                with open("../web/dashboard.html", "rb") as f:
                    body = f.read()
            except FileNotFoundError:
                with open("web/dashboard.html", "rb") as f:
                    body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            data = {}
        if self.path == "/api/drive":
            ms = max(0, min(int(data.get("ms", 500)), 2000))
            speed = max(0, min(int(data.get("speed", 40)), 60))
            cmd = {"forward": "DRIVE", "back": "BACK",
                   "left": "TURNL", "right": "TURNR"}.get(data.get("dir", "forward"), "DRIVE")
            try:
                _link._cmd(f"{cmd} {ms} {speed}")
                return self._json({"ok": True})
            except Exception as e:
                return self._json({"ok": False, "error": str(e)}, 500)
        if self.path == "/api/stop":
            try:
                _link.stop()
            except Exception:
                pass
            return self._json({"ok": True})
        self.send_response(404)
        self.end_headers()

    def log_message(self, *a):
        pass  # quiet


def start_dashboard(link, said_log, port=8080):
    global _link, _said
    _link, _said = link, said_log
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server
