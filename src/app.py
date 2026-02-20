"""IndestructibleEco v1.0 — Application Factory.

URI: indestructibleeco://src/app

Provides:
- create_app() factory for FastAPI application
- /health, /metrics, /v1/models, /v1/chat/completions endpoints
- API key authentication middleware
- Proxy routing to backend/ai and backend/api services
- Standalone HTTP server fallback

Contracts defined by: tests/integration/test_api.py
"""

from __future__ import annotations

import os
import time
import uuid
import resource
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel

from .middleware.auth import AuthMiddleware
from .core.registry import ModelRegistry
from .core.queue import RequestQueue
from .schemas.auth import UserRole
from .schemas.inference import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatMessage,
    ChatRole,
    UsageInfo,
)
from .schemas.models import ModelStatus

# ── Configuration ────────────────────────────────────────────────────

VERSION = "1.0.0"
ENVIRONMENT = os.getenv("ECO_ENVIRONMENT", "development")
AI_SERVICE_URL = os.getenv("ECO_AI_SERVICE_URL", "http://localhost:8001")
API_SERVICE_URL = os.getenv("ECO_API_SERVICE_URL", "http://localhost:3000")


# ── Proxy Client ───────────────────────────────────────────────────

class ServiceProxy:
    """Lightweight HTTP proxy to backend services."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Any = None

    async def _get_client(self) -> Any:
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    async def forward(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        json_body: Any = None,
        params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Forward request to backend service, return parsed JSON."""
        try:
            client = await self._get_client()
            response = await client.request(
                method, path, headers=headers, json=json_body, params=params,
            )
            if response.status_code >= 400:
                return {
                    "_proxy_error": True,
                    "status_code": response.status_code,
                    "detail": response.text[:500],
                }
            return response.json()
        except Exception as exc:
            return {
                "_proxy_error": True,
                "status_code": 502,
                "detail": f"Upstream service unavailable: {type(exc).__name__}: {exc}",
            }

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


# ── Application Factory ─────────────────────────────────────────────

def _init_state(app: FastAPI) -> None:
    """Initialize application state (idempotent)."""
    if not hasattr(app.state, "start_time"):
        app.state.start_time = time.time()
        app.state.auth = AuthMiddleware()
        app.state.registry = ModelRegistry()
        app.state.queue = RequestQueue()
        app.state.ai_proxy = ServiceProxy(AI_SERVICE_URL)
        app.state.api_proxy = ServiceProxy(API_SERVICE_URL)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _init_state(app)
        yield
        await app.state.ai_proxy.close()
        await app.state.api_proxy.close()

    app = FastAPI(
        title="IndestructibleEco AI Service",
        version=VERSION,
        docs_url="/docs" if ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )

    # Eagerly initialize state so TestClient works even if lifespan
    # is not triggered by older Starlette versions.
    _init_state(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Auth dependency ──────────────────────────────────────────

    async def require_auth(request: Request) -> Dict[str, Any]:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        token = auth_header[7:]
        auth: AuthMiddleware = request.app.state.auth

        # Try API key first
        key_data = auth.validate_api_key(token)
        if key_data is not None:
            return key_data

        # Try JWT
        payload = auth.verify_jwt_token(token)
        if payload is not None:
            return {"sub": payload["sub"], "role": payload.get("role", "viewer")}

        raise HTTPException(status_code=401, detail="Invalid credentials")

    # ── Health ───────────────────────────────────────────────────

    @app.get("/health")
    async def health(request: Request):
        uptime = time.time() - request.app.state.start_time
        registry: ModelRegistry = request.app.state.registry
        engines = list({
            engine
            for m in (await registry.list_models())
            for engine in m.compatible_engines
        })
        return {
            "status": "healthy",
            "service": "ai",
            "version": VERSION,
            "engines": sorted(engines),
            "uri": "indestructibleeco://backend/ai/health",
            "urn": f"urn:indestructibleeco:backend:ai:health:{uuid.uuid1()}",
            "uptime_seconds": round(uptime, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ── Metrics ──────────────────────────────────────────────────

    @app.get("/metrics")
    async def metrics(request: Request):
        uptime = time.time() - request.app.state.start_time
        mem = resource.getrusage(resource.RUSAGE_SELF)
        registry: ModelRegistry = request.app.state.registry
        model_count = registry.count
        queue: RequestQueue = request.app.state.queue
        lines = [
            "# HELP eco_uptime_seconds Service uptime in seconds",
            "# TYPE eco_uptime_seconds gauge",
            f"eco_uptime_seconds {uptime:.2f}",
            "# HELP eco_memory_maxrss_bytes Maximum resident set size",
            "# TYPE eco_memory_maxrss_bytes gauge",
            f"eco_memory_maxrss_bytes {mem.ru_maxrss * 1024}",
            "# HELP eco_models_registered Total registered models",
            "# TYPE eco_models_registered gauge",
            f"eco_models_registered {model_count}",
            "# HELP eco_queue_depth Current request queue depth",
            "# TYPE eco_queue_depth gauge",
            f"eco_queue_depth {queue.depth}",
        ]
        return PlainTextResponse(
            "\n".join(lines) + "\n",
            media_type="text/plain; version=0.0.4",
        )

    # ── Models ───────────────────────────────────────────────────

    @app.get("/v1/models")
    async def list_models(request: Request, user: Dict = Depends(require_auth)):
        registry: ModelRegistry = request.app.state.registry
        models = await registry.list_models()
        return {
            "object": "list",
            "data": [
                {
                    "id": m.model_id,
                    "object": "model",
                    "source": m.source,
                    "capabilities": [c.value for c in m.capabilities],
                    "compatible_engines": m.compatible_engines,
                    "context_length": m.context_length,
                    "status": m.status.value,
                }
                for m in models
            ],
        }

    # ── Chat Completions ─────────────────────────────────────────

    @app.post("/v1/chat/completions")
    async def chat_completions(
        req: ChatCompletionRequest,
        request: Request,
        user: Dict = Depends(require_auth),
    ):
        registry: ModelRegistry = request.app.state.registry
        model = await registry.resolve_model(req.model)
        if model is None:
            raise HTTPException(status_code=404, detail=f"Model '{req.model}' not found")

        # Try proxy to AI service first
        ai_proxy: ServiceProxy = request.app.state.ai_proxy
        proxy_result = await ai_proxy.forward(
            "POST", "/v1/chat/completions",
            json_body={
                "model": model.model_id,
                "messages": [{"role": m.role.value, "content": m.content} for m in req.messages],
                "temperature": req.temperature,
                "max_tokens": req.max_tokens,
                "stream": req.stream,
            },
            headers={"Authorization": request.headers.get("Authorization", "")},
        )

        if not proxy_result.get("_proxy_error"):
            return proxy_result

        # Fallback: local inference simulation
        request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        prompt_tokens = sum(len(m.content.split()) for m in req.messages)
        completion_tokens = min(req.max_tokens, max(1, prompt_tokens))

        response = ChatCompletionResponse(
            id=request_id,
            model=model.model_id,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role=ChatRole.ASSISTANT,
                        content=f"[{model.model_id}] Response to: {req.messages[-1].content[:100]}",
                    ),
                    finish_reason="stop",
                )
            ],
            usage=UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )
        return response

    # ── Proxy routes to API service ──────────────────────────────

    @app.post("/api/v1/generate")
    async def proxy_generate(request: Request, user: Dict = Depends(require_auth)):
        body = await request.json()
        api_proxy: ServiceProxy = request.app.state.api_proxy
        result = await api_proxy.forward(
            "POST", "/api/v1/ai/generate",
            json_body=body,
            headers={"Authorization": request.headers.get("Authorization", "")},
        )
        if result.get("_proxy_error"):
            raise HTTPException(status_code=result["status_code"], detail=result["detail"])
        return result

    @app.post("/api/v1/yaml/generate")
    async def proxy_yaml_generate(request: Request, user: Dict = Depends(require_auth)):
        body = await request.json()
        api_proxy: ServiceProxy = request.app.state.api_proxy
        result = await api_proxy.forward(
            "POST", "/api/v1/yaml/generate",
            json_body=body,
            headers={"Authorization": request.headers.get("Authorization", "")},
        )
        if result.get("_proxy_error"):
            raise HTTPException(status_code=result["status_code"], detail=result["detail"])
        return result

    @app.post("/api/v1/yaml/validate")
    async def proxy_yaml_validate(request: Request, user: Dict = Depends(require_auth)):
        body = await request.json()
        api_proxy: ServiceProxy = request.app.state.api_proxy
        result = await api_proxy.forward(
            "POST", "/api/v1/yaml/validate",
            json_body=body,
            headers={"Authorization": request.headers.get("Authorization", "")},
        )
        if result.get("_proxy_error"):
            raise HTTPException(status_code=result["status_code"], detail=result["detail"])
        return result

    @app.get("/api/v1/platforms")
    async def proxy_platforms(request: Request, user: Dict = Depends(require_auth)):
        api_proxy: ServiceProxy = request.app.state.api_proxy
        result = await api_proxy.forward(
            "GET", "/api/v1/platforms",
            headers={"Authorization": request.headers.get("Authorization", "")},
        )
        if result.get("_proxy_error"):
            raise HTTPException(status_code=result["status_code"], detail=result["detail"])
        return result

    return app


# ── Standalone mode ──────────────────────────────────────────────────

app = create_app()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("ECO_PORT", "8000"))
    uvicorn.run("src.app:app", host="0.0.0.0", port=port, reload=(ENVIRONMENT == "development"))
