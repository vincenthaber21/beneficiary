"""
Local HTTP bridge for fingerprint scanners.

Backends (auto):
  1. Hikvision FPModule_SDK.dll  — DS-K1F820-F
  2. Neurotechnology Nffv        — Futronic, SecuGen, ZKTeco, …

Run:

    cd fingerprint_bridge
    pip install -r requirements.txt
    python app.py

For Hikvision (recommended for DS-K1F820-F):
    copy FPModule_SDK.dll into fingerprint_bridge/lib/
    If the DLL is 32-bit, use 32-bit Python:  py -3-32 app.py

Browser / Django form calls:
    GET  http://127.0.0.1:8765/status
    GET  http://127.0.0.1:8765/capture
    POST http://127.0.0.1:8765/match
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import fp_device as fp

HOST = "127.0.0.1"
PORT = 8765


def _json_bytes(payload: dict) -> bytes:
    return json.dumps(payload).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "Fingerprint-Bridge/2.0"

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")

    def _send(self, code: int, payload: dict):
        body = _json_bytes(payload)
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):  # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"
        qs = parse_qs(urlparse(self.path).query)

        if path in ("/", "/status"):
            status = fp.sdk_status()
            self._send(200 if status.get("ok") else 503, status)
            return

        if path == "/capture":
            timeout = 25.0
            if "timeout" in qs:
                try:
                    timeout = float(qs["timeout"][0])
                except (TypeError, ValueError):
                    pass
            result = fp.capture_fingerprint(timeout_sec=timeout)
            code = result.get("code") or (200 if result.get("ok") else 500)
            self._send(int(code), result)
            return

        self._send(404, {"ok": False, "error": "Not found. Use /status or /capture"})

    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send(400, {"ok": False, "error": "Invalid JSON"})
            return

        if path == "/match":
            samples = data.get("fp_samples") or data.get("samples") or []
            threshold = int(data.get("threshold", 10))
            result = fp.capture_fingerprint(timeout_sec=float(data.get("timeout", 25)))
            if not result.get("ok"):
                self._send(result.get("code", 500), result)
                return
            live = result["fp_hash"]
            best = None
            best_dist = 999
            for sample in samples:
                dist = fp.hamming_hex(live, str(sample))
                if dist < best_dist:
                    best_dist = dist
                    best = sample
            matched = best is not None and best_dist <= threshold
            self._send(
                200 if matched else 404,
                {
                    "ok": True,
                    "is_match": matched,
                    "fp_hash": live,
                    "matched_sample": best if matched else None,
                    "distance": best_dist,
                    "threshold": threshold,
                    "image_data": result.get("image_data"),
                    "device_name": result.get("device_name"),
                    "backend": result.get("backend"),
                },
            )
            return

        self._send(404, {"ok": False, "error": "Not found. Use POST /match"})

    def log_message(self, fmt, *args):
        print(f"[fp-bridge] {self.address_string()} - {fmt % args}")


def main():
    print("=" * 64)
    print(" Fingerprint Bridge (Hikvision FPModule / Nffv)")
    print(f" Listening on http://{HOST}:{PORT}")
    print(" Endpoints: GET /status  GET /capture  POST /match")
    print("=" * 64)
    status = fp.sdk_status()
    backend = status.get("backend") or ("hikvision" if fp._hik_dll_path() else "nffv")
    print(f" Backend: {backend}")
    if status.get("ok"):
        print(" SDK OK")
        scanners = status.get("available_scanners") or []
        print(f" Scanners: {', '.join(scanners) or '(none detected)'}")
        if status.get("device_info"):
            print(f" Device: {status['device_info']}")
    else:
        print(f" SDK NOT READY: {status.get('error')}")
        scanners = status.get("available_scanners") or []
        if scanners:
            print(f" Available modules: {', '.join(scanners)}")
        if status.get("note"):
            print(f" Note: {status['note']}")
        if not fp._hik_dll_path():
            print(" Tip: For DS-K1F820-F, copy FPModule_SDK.dll into fingerprint_bridge/lib/")
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
