"""
MineGuard Web Application & REST API Server (Python Backend)
============================================================
Serves the MineGuard interface design files and provides REST API
endpoints powered by the core Python quantum risk engine (engine.py).

Zero external dependencies required (uses Python standard library).

Usage:
    python app.py
    python app.py --port 8080
"""

import os
import sys
import json
import argparse
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, SimpleHTTPRequestHandler

import engine


class MineGuardRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler combining static file serving with REST API endpoints."""

    def __init__(self, *args, **kwargs):
        # Serve static assets from the current directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(*args, directory=base_dir, **kwargs)

    def _send_cors_headers(self):
        """Attaches universal CORS headers for frontend consumption."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _send_json_response(self, data: dict, status_code: int = 200):
        """Serializes and sends JSON response with proper headers."""
        response_body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(response_body)

    def do_OPTIONS(self):
        """Handles pre-flight CORS requests."""
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Handles GET requests: REST API endpoints or static interface files."""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # -------------------------------------------------------------
        # REST API ROUTING
        # -------------------------------------------------------------
        if path == "/api/health":
            self._send_json_response({
                "status": "healthy",
                "service": "MineGuard Quantum Risk Engine",
                "version": "2.4.0",
                "platform": sys.platform
            })
            return

        if path == "/api/threat-model":
            self._send_json_response(engine.QUANTUM_THREAT_MODEL)
            return

        if path == "/api/graph":
            graph = engine.build_mining_graph()
            self._send_json_response(graph)
            return

        if path == "/api/scan":
            scan_path = query.get("path", ["/path/to/mining-project"])[0]
            findings = engine.scan_project(scan_path)
            risk = engine.calculate_crypto_risk(findings)
            self._send_json_response({
                "path": scan_path,
                "findings": findings,
                "risk": risk
            })
            return

        if path == "/api/cascade":
            year_val = query.get("year", ["2029"])[0]
            try:
                year = int(year_val)
            except ValueError:
                year = 2029
            results = engine.run_cascade(q_day=year)
            self._send_json_response(results)
            return

        if path == "/api/priority":
            priorities = engine.calculate_migration_priority()
            self._send_json_response({"priorities": priorities})
            return

        if path == "/api/roadmap":
            roadmap = engine.generate_roadmap()
            self._send_json_response(roadmap)
            return

        if path == "/api/cbom":
            cbom = engine.generate_cbom()
            self._send_json_response(cbom)
            return

        # -------------------------------------------------------------
        # STATIC INTERFACE DESIGN FILES (HTML, CSS, JS)
        # -------------------------------------------------------------
        # If user visits root '/', redirect to index.html (Unified Single Website)
        if path == "/":
            self.send_response(302)
            self.send_header("Location", "/index.html")
            self.end_headers()
            return

        # Otherwise serve static frontend file via SimpleHTTPRequestHandler
        super().do_GET()

    def do_POST(self):
        """Handles POST requests to REST API endpoints."""
        parsed = urlparse(self.path)
        path = parsed.path

        # Read JSON body if present
        content_length = int(self.headers.get("Content-Length", 0))
        body_data = {}
        if content_length > 0:
            try:
                raw_body = self.rfile.read(content_length).decode("utf-8")
                body_data = json.loads(raw_body)
            except Exception:
                body_data = {}

        if path == "/api/scan":
            scan_path = body_data.get("path", "/path/to/mining-project")
            findings = engine.scan_project(scan_path)
            risk = engine.calculate_crypto_risk(findings)
            self._send_json_response({
                "path": scan_path,
                "findings": findings,
                "risk": risk
            })
            return

        if path == "/api/cascade":
            year = int(body_data.get("year", 2029))
            migrated = body_data.get("migrated", [])
            results = engine.run_cascade(q_day=year, migrated_nodes=migrated)
            self._send_json_response(results)
            return

        self._send_json_response({"error": "Endpoint not found"}, status_code=404)

    def log_message(self, format, *args):
        """Clean log formatting for incoming requests."""
        sys.stderr.write(f"[MineGuard Backend] {self.address_string()} - {format % args}\n")


def run_server(port: int = 8080, bind_addr: str = "127.0.0.1"):
    """Starts the MineGuard Python backend HTTP server."""
    server_address = (bind_addr, port)
    httpd = HTTPServer(server_address, MineGuardRequestHandler)
    print(f"======================================================")
    print(f"  MINEGUARD PYTHON BACKEND & INTERFACE SERVER ACTIVE   ")
    print(f"======================================================")
    print(f"  Host: http://{bind_addr}:{port}/")
    print(f"  Interface Entry: http://{bind_addr}:{port}/page1.html")
    print(f"  Test Runner:     http://{bind_addr}:{port}/test.html")
    print(f"  REST API Base:   http://{bind_addr}:{port}/api/health")
    print(f"======================================================")
    print(f"Press Ctrl+C to terminate.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down MineGuard server.")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MineGuard Python Backend & Interface Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    parser.add_argument("--bind", type=str, default="127.0.0.1", help="Address to bind (default: 127.0.0.1)")
    args = parser.parse_args()

    run_server(port=args.port, bind_addr=args.bind)
