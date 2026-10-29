from __future__ import annotations

import json
import mimetypes
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from intermarket_analysis.config import WEB_DIR
from intermarket_analysis.analysis.run import run_analysis
from intermarket_analysis.storage import init_db, list_series_meta, query_series


class DashboardHandler(BaseHTTPRequestHandler):
    web_dir: Path = WEB_DIR

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        if not path.is_file():
            self.send_error(404)
            return
        content = path.read_bytes()
        mime, _ = mimetypes.guess_type(str(path))
        self.send_response(200)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            return self._send_file(self.web_dir / "index.html")
        if parsed.path.startswith("/static/"):
            rel = parsed.path.removeprefix("/static/")
            static_root = (self.web_dir / "static").resolve()
            target = (static_root / rel).resolve()
            if not str(target).startswith(str(static_root)):
                self.send_error(403)
                return
            return self._send_file(target)

        if parsed.path == "/api/series":
            init_db()
            series = [
                {
                    "id": s.series_id,
                    "name": s.name,
                    "unit": s.unit,
                    "source_url": s.source_url,
                    "asset_class": s.asset_class,
                    "compare_group": s.compare_group,
                    "spot_series_id": s.spot_series_id,
                }
                for s in list_series_meta()
                if s.enabled
            ]
            return self._send_json({"series": series})

        if parsed.path == "/api/analysis/summary":
            qs = parse_qs(parsed.query)
            start = qs.get("from", [None])[0]
            end = qs.get("to", [None])[0]
            start_date = date.fromisoformat(start) if start else None
            end_date = date.fromisoformat(end) if end else None
            init_db()
            payload = run_analysis(start_date, end_date)
            return self._send_json(payload)

        if parsed.path == "/api/data":
            qs = parse_qs(parsed.query)
            ids = qs.get("series", [])
            if not ids:
                return self._send_json({"error": "series query parameter required"}, 400)
            start = qs.get("from", [None])[0]
            end = qs.get("to", [None])[0]
            start_date = date.fromisoformat(start) if start else None
            end_date = date.fromisoformat(end) if end else None
            init_db()
            data = query_series(ids, start_date, end_date)
            return self._send_json({"data": data})

        self.send_error(404)


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    init_db()
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"Dashboard: http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
