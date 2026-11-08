"""Vercel Python function: POST {"script","niche"} -> Report JSON.
LLM mode is off on the public web unless THUMBSTOP_WEB_LLM=1, so strangers can't spend your API credits."""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ.setdefault("THUMBSTOP_HOME", "/tmp/thumbstop")

from thumbstop import personas  # noqa: E402
from thumbstop.simulate import simulate  # noqa: E402

MAX_CHARS = 4000


def run(body: dict):
    script = str(body.get("script", "")).strip()
    if not script:
        return 400, {"error": "Paste a script first."}
    if len(script) > MAX_CHARS:
        return 400, {"error": f"Keep it under {MAX_CHARS} characters."}
    niche = str(body.get("niche") or "general")[:40]
    llm = None if os.environ.get("THUMBSTOP_WEB_LLM") == "1" else False
    r = simulate(script, niche, use_llm=llm)
    return 200, {**r.__dict__, "signals": r.signals(), "packs": personas.available()}


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            n = min(int(self.headers.get("content-length", 0)), 20000)
            code, out = run(json.loads(self.rfile.read(n) or b"{}"))
        except (ValueError, TypeError):
            code, out = 400, {"error": "Bad request."}
        data = json.dumps(out).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
