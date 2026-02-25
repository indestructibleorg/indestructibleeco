"""GovOps Platform API — FastAPI application entry point.

@GL-governed
@GL-layer: GL50-69
@GL-semantic: api-main
"""
from __future__ import annotations

import structlog
from fastapi import FastAPI

from presentation.api.routers import health, modules, scans, workflows

logger = structlog.get_logger("govops.api")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title="GovOps Platform API",
        version="1.0.0",
        description="Governance Operations Platform — autonomous closed-loop governance.",
    )

    app.include_router(health.router)
    app.include_router(modules.router)
    app.include_router(scans.router)
    app.include_router(workflows.router)

    return app


app = create_app()


def run() -> None:
    """Entry point for the ``govops`` console script."""
    import uvicorn

    uvicorn.run(
        "presentation.api.main:app",
        host="0.0.0.0",
        port=8091,
        log_level="info",
    )


if __name__ == "__main__":
    run()
