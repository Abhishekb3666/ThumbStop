"""Vercel Python function: POST post details -> full crowd simulation report (text-based formats).
Capped sizes keep it cheap; files (video/audio/images) are handled by the CLI."""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ.setdefault("THUMBSTOP_HOME", "/tmp/thumbstop")

from thumbstop import content as C, crowd  # noqa: E402
from thumbstop.demographics import PLATFORMS  # noqa: E402

MAX_CHARS, MAX_N = 6000, 3000


def run(b: dict):
    text = str(b.get("text", "")).strip()
    caption = str(b.get("caption", "")).strip()
    if not text and not caption:
        return 400, {"error": "Paste your post first."}
    if len(text) + len(caption) > MAX_CHARS:
        return 400, {"error": f"Keep it under {MAX_CHARS} characters."}
    kind = str(b.get("kind") or "reel")
    niche = str(b.get("niche") or "general")[:40]
    platform = str(b.get("platform") or "instagram")
    if platform not in PLATFORMS:
        return 400, {"error": "Unknown platform."}
    try:
        topics = [t.strip() for t in str(b.get("topics", "")).split(",") if t.strip()][:5]
        c = C.from_text(kind, text, caption, None, None, topics, niche)
        followers = max(0.0, min(1.0, float(b.get("followers", 0.25))))
        n = max(200, min(MAX_N, int(b.get("n", 1500))))
    except (ValueError, TypeError) as e:
        return 400, {"error": str(e)}
    r = crowd.run(c, platform=platform, n=n, followers=followers, niche=niche)
    return 200, r.__dict__


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            n = min(int(self.headers.get("content-length", 0)), 30000)
            code, out = run(json.loads(self.rfile.read(n) or b"{}"))
        except (ValueError, TypeError):
            code, out = 400, {"error": "Bad request."}
        data = json.dumps(out).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
