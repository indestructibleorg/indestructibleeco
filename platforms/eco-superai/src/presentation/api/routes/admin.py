"""Administration API routes - System management, CI/CD status, K8s health."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter()


class SystemStatusResponse(BaseModel):
    platform: str = "SuperAI Platform"
    version: str = "1.0.0"
    environment: str
    services: dict[str, Any]
    resources: dict[str, Any]


class DeploymentStatusResponse(BaseModel):
    deployment_id: str
    status: str
    namespace: str
    replicas: dict[str, int]
    last_updated: str


class K8sHealthRequest(BaseModel):
    namespace: str = Field(default="default")
    resource_type: str = Field(default="all", pattern=r"^(all|pods|services|deployments|ingress)$")


@router.get("/system/status")
async def system_status() -> dict[str, Any]:
    """Get comprehensive system status."""
    import platform
    import psutil
    from datetime import datetime, timezone

    cpu_percent = psutil.cpu_percent(interval=0.1) if hasattr(psutil, 'cpu_percent') else 0
    memory = psutil.virtual_memory() if hasattr(psutil, 'virtual_memory') else None

    services = {}
    # Database
    try:
        from src.infrastructure.persistence.database import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            row = result.fetchone()
            services["database"] = {"status": "healthy", "version": str(row[0]) if row else "unknown"}
    except Exception as e:
        services["database"] = {"status": "unhealthy", "error": str(e)}

    # Redis
    try:
        from src.infrastructure.cache.redis_client import get_redis
        redis = await get_redis()
        info = await redis.info("server")
        services["redis"] = {"status": "healthy", "version": info.get("redis_version", "unknown")}
    except Exception as e:
        services["redis"] = {"status": "unhealthy", "error": str(e)}

    return {
        "platform": "SuperAI Platform",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": "production",
        "services": services,
        "resources": {
            "cpu_percent": cpu_percent,
            "memory_total_gb": round(memory.total / (1024**3), 2) if memory else 0,
            "memory_used_gb": round(memory.used / (1024**3), 2) if memory else 0,
            "memory_percent": memory.percent if memory else 0,
            "python_version": platform.python_version(),
        },
    }


@router.get("/deployments")
async def list_deployments(namespace: str = Query("default")) -> list[dict[str, Any]]:
    """List Kubernetes deployments status."""
    try:
        from src.infrastructure.external.k8s_client import K8sClient
        client = K8sClient()
        return await client.list_deployments(namespace=namespace)
    except ImportError:
        return [{"status": "k8s_client_not_configured", "message": "Kubernetes client not available in this environment"}]


@router.post("/deployments/{name}/scale")
async def scale_deployment(name: str, replicas: int = Query(..., ge=0, le=50), namespace: str = Query("default")) -> dict[str, Any]:
    """Scale a Kubernetes deployment."""
    try:
        from src.infrastructure.external.k8s_client import K8sClient
        client = K8sClient()
        return await client.scale_deployment(name=name, replicas=replicas, namespace=namespace)
    except ImportError:
        return {"status": "error", "message": "Kubernetes client not available"}


@router.post("/k8s/health")
async def k8s_health_check(request: K8sHealthRequest) -> dict[str, Any]:
    """Check Kubernetes cluster health."""
    try:
        from src.infrastructure.external.k8s_client import K8sClient
        client = K8sClient()
        return await client.health_check(namespace=request.namespace, resource_type=request.resource_type)
    except ImportError:
        return {"status": "standalone", "message": "Running outside Kubernetes cluster"}


@router.get("/config/export")
async def export_config(format: str = Query("json", pattern=r"^(json|yaml)$")) -> dict[str, Any]:
    """Export current configuration (sanitized)."""
    from src.infrastructure.config import get_settings
    settings = get_settings()
    config = {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "app_env": settings.app_env.value,
        "database_pool_size": settings.database.pool_size,
        "redis_max_connections": settings.redis.max_connections,
        "celery_timezone": settings.celery.timezone,
        "quantum_backend": settings.quantum.backend,
        "quantum_shots": settings.quantum.shots,
        "ai_model": settings.ai.openai_model,
        "monitoring_enabled": settings.monitoring.prometheus_enabled,
    }
    if format == "yaml":
        import yaml
        return {"format": "yaml", "content": yaml.dump(config, default_flow_style=False, allow_unicode=True)}
    return {"format": "json", "content": config}


@router.post("/tools/yaml-to-json")
async def yaml_to_json_admin(yaml_content: str) -> dict[str, Any]:
    """Convert YAML to JSON (admin utility)."""
    import yaml
    import json
    try:
        parsed = yaml.safe_load(yaml_content)
        return {"status": "success", "result": parsed}
    except yaml.YAMLError as e:
        return {"status": "error", "message": str(e)}


@router.post("/cache/flush")
async def flush_cache(pattern: str = Query("*", max_length=200)) -> dict[str, Any]:
    """Flush cache entries matching pattern."""
    try:
        from src.infrastructure.cache.redis_client import get_redis
        redis = await get_redis()
        if pattern == "*":
            await redis.flushdb()
            return {"status": "success", "message": "All cache entries flushed"}
        else:
            keys = []
            async for key in redis.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await redis.delete(*keys)
            return {"status": "success", "flushed_keys": len(keys)}
    except Exception as e:
        return {"status": "error", "message": str(e)}