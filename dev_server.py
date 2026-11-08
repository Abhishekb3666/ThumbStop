"""Local preview of the web UI (what Vercel does in production): python dev_server.py -> http://localhost:8000"""
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler

from api.analyze import handler as analyze
from api.crowd import handler as crowd_api


class Dev(SimpleHTTPRequestHandler):
    def do_POST(self):
        (crowd_api if self.path.startswith('/api/crowd') else analyze).do_POST(self)


if __name__ == "__main__":
    print("http://localhost:8000")
    HTTPServer(("", 8000), partial(Dev, directory="public")).serve_forever()
