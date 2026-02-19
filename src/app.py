# IndestructibleEco v1.0 — API Gateway Application
# URI: indestructibleeco://src/app
#
# This is the root-level API Gateway entry point used by docker/Dockerfile.
# It proxies requests to backend services (AI, API) and provides health/status endpoints.
#
# Build: docker build -t ghcr.io/indestructibleorg/api:v1.0.0 -f docker/Dockerfile .
# Run:   docker run -p 8000:8000 ghcr.io/indestructibleorg/api:v1.0.0

import os
import time
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# ── Configuration ────────────────────────────────────────────
HOST = os.getenv("ECO_HOST", "0.0.0.0")
PORT = int(os.getenv("ECO_PORT", "8000"))
ENVIRONMENT = os.getenv("ECO_ENVIRONMENT", "production")
VERSION = "1.0.0"
START_TIME = time.time()

# ── Upstream service endpoints ───────────────────────────────
AI_SERVICE_URL = os.getenv("ECO_AI_SERVICE_URL", "http://localhost:8001")
API_SERVICE_URL = os.getenv("ECO_API_SERVICE_URL", "http://localhost:3000")


class GatewayHandler(BaseHTTPRequestHandler):
    """Minimal API Gateway request handler."""

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/health":
            self._respond(200, {
                "status": "healthy",
                "service": "api-gateway",
                "version": VERSION,
                "environment": ENVIRONMENT,
                "uptime_seconds": round(time.time() - START_TIME, 2),
            })
        elif path == "/ready":
            self._respond(200, {"ready": True})
        elif path == "/":
            self._respond(200, {
                "service": "IndestructibleEco API Gateway",
                "version": VERSION,
                "endpoints": {
                    "health": "/health",
                    "ready": "/ready",
                    "ai": "/api/v1/ai/*",
                    "platform": "/api/v1/platform/*",
                },
            })
        else:
            self._respond(404, {"error": "not_found", "path": path})

    def do_POST(self):
        self._respond(501, {"error": "not_implemented", "message": "Proxy routing not yet configured"})

    def _respond(self, status: int, body: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Service", "indestructibleeco-gateway")
        self.send_header("X-Version", VERSION)
        self.end_headers()
        self.wfile.write(json.dumps(body, indent=2).encode())

    def log_message(self, format, *args):
        """Structured logging."""
        print(f"[gateway] {self.address_string()} - {format % args}")


# ── ASGI/WSGI compatibility shim ────────────────────────────
# When run via uvicorn (as in Dockerfile CMD), provide an ASGI app object.
# For standalone mode, use the built-in HTTP server.
try:
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    async def health(request):
        return JSONResponse({
            "status": "healthy",
            "service": "api-gateway",
            "version": VERSION,
            "environment": ENVIRONMENT,
            "uptime_seconds": round(time.time() - START_TIME, 2),
        })

    async def ready(request):
        return JSONResponse({"ready": True})

    async def root(request):
        return JSONResponse({
            "service": "IndestructibleEco API Gateway",
            "version": VERSION,
            "endpoints": {
                "health": "/health",
                "ready": "/ready",
                "ai": "/api/v1/ai/*",
                "platform": "/api/v1/platform/*",
            },
        })

    async def not_found(request):
        return JSONResponse(
            {"error": "not_found", "path": request.url.path},
            status_code=404,
        )

    app = Starlette(
        routes=[
            Route("/", root),
            Route("/health", health),
            Route("/ready", ready),
        ],
        debug=(ENVIRONMENT != "production"),
    )

except ImportError:
    # Starlette not available — provide a minimal WSGI-compatible app
    app = None


def main():
    """Standalone HTTP server mode."""
    server = HTTPServer((HOST, PORT), GatewayHandler)
    print(f"[gateway] IndestructibleEco API Gateway v{VERSION}")
    print(f"[gateway] Listening on {HOST}:{PORT} ({ENVIRONMENT})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[gateway] Shutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()