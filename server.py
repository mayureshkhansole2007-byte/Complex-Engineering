import http.server
import socketserver
import json
import urllib.parse
import os
import sys
from parking_engine import SmartParkingEngine

PORT = 8000
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
engine = SmartParkingEngine()

class SmartParkingHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def _send_json(self, data, status_code=200):
        response_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/status":
            return self._send_json(engine.get_parking_status())

        elif path == "/api/report":
            return self._send_json(engine.daily_report())

        elif path == "/api/records":
            return self._send_json(engine.all_records())

        elif path == "/api/search":
            q = query.get("q", [""])[0]
            return self._send_json(engine.search_vehicle(q))

        # Static files fallback
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        if path == "/api/entry":
            reg = payload.get("registration", "")
            vtype = payload.get("type", "4")
            res = engine.vehicle_entry(reg, vtype)
            status_code = 200 if res.get("success") else 400
            return self._send_json(res, status_code=status_code)

        elif path == "/api/exit":
            reg = payload.get("registration", "")
            res = engine.vehicle_exit(reg)
            status_code = 200 if res.get("success") else 400
            return self._send_json(res, status_code=status_code)

        elif path == "/api/cancel":
            reg = payload.get("registration", "")
            res = engine.cancel_entry(reg)
            status_code = 200 if res.get("success") else 400
            return self._send_json(res, status_code=status_code)

        elif path == "/api/capacity":
            cap = int(payload.get("capacity", 20))
            res = engine.set_capacity(cap)
            status_code = 200 if res.get("success") else 400
            return self._send_json(res, status_code=status_code)

        else:
            return self._send_json({"error": "Endpoint not found"}, status_code=404)

def run_server(port=PORT):
    # Ensure web directory exists
    if not os.path.exists(WEB_DIR):
        os.makedirs(WEB_DIR, exist_ok=True)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), SmartParkingHandler) as httpd:
        print(f"==================================================")
        print(f" SMART PARKING SYSTEM - WEB SERVER RUNNING")
        print(f" Local Web UI: http://localhost:{port}")
        print(f" Linked to C++ parking data: {engine.file_path}")
        print(f" Press Ctrl+C to stop the server")
        print(f"==================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == "__main__":
    port = PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
