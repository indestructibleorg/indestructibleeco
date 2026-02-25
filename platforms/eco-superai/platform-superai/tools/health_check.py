"""System health check tool - checks all platform dependencies."""
from __future__ import annotations

import asyncio
import json
import sys
import time
from typing import Any

import httpx


class HealthChecker:
    """Comprehensive health checker for all platform services."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: dict[str, Any] = {}

    async def check_all(self) -> dict[str, Any]:
        start = time.perf_counter()
        checks = await asyncio.gather(
            self._check_api(),
            self._check_database(),
            self._check_redis(),
            self._check_rabbitmq(),
            self._check_elasticsearch(),
            self._check_prometheus(),
            self._check_chromadb(),
            return_exceptions=True,
        )

        services = ["api", "database", "redis", "rabbitmq", "elasticsearch", "prometheus", "chromadb"]
        for name, result in zip(services, checks):
            if isinstance(result, Exception):
                self.results[name] = {"status": "error", "error": str(result)}
            else:
                self.results[name] = result

        healthy = sum(1 for r in self.results.values() if r.get("status") == "healthy")
        total = len(self.results)
        elapsed = (time.perf_counter() - start) * 1000

        return {
            "overall_status": "healthy" if healthy == total else "degraded" if healthy > 0 else "unhealthy",
            "healthy_services": f"{healthy}/{total}",
            "services": self.results,
            "check_duration_ms": round(elapsed, 2),
        }

    async def _check_api(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/api/v1/health")
                data = resp.json()
                return {"status": "healthy" if resp.status_code == 200 else "unhealthy", "response_time_ms": resp.elapsed.total_seconds() * 1000, "version": data.get("version", "unknown")}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def _check_database(self) -> dict[str, Any]:
        try:
            import asyncpg
            conn = await asyncio.wait_for(asyncpg.connect("postgresql://superai:superai_secret@localhost:5432/superai_db"), timeout=5)
            version = await conn.fetchval("SELECT version()")
            await conn.close()
            return {"status": "healthy", "version": version[:50]}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def _check_redis(self) -> dict[str, Any]:
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url("redis://localhost:6379/0", socket_timeout=5)
            await r.ping()
            info = await r.info("server")
            await r.close()
            return {"status": "healthy", "version": info.get("redis_version", "unknown")}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def _check_rabbitmq(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get("http://localhost:15672/api/overview", auth=("superai", "superai_secret"))
                if resp.status_code == 200:
                    data = resp.json()
                    return {"status": "healthy", "version": data.get("rabbitmq_version", "unknown"), "node": data.get("node", "")}
            return {"status": "unhealthy", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def _check_elasticsearch(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get("http://localhost:9200/_cluster/health")
                if resp.status_code == 200:
                    data = resp.json()
                    return {"status": "healthy" if data["status"] in ("green", "yellow") else "degraded", "cluster_status": data["status"], "nodes": data.get("number_of_nodes", 0)}
            return {"status": "unhealthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def _check_prometheus(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get("http://localhost:9090/-/healthy")
                return {"status": "healthy" if resp.status_code == 200 else "unhealthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def _check_chromadb(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get("http://localhost:8100/api/v1/heartbeat")
                return {"status": "healthy" if resp.status_code == 200 else "unhealthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="SuperAI Platform Health Check")
    parser.add_argument("--url", default="http://localhost:8000", help="Base API URL")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--watch", type=int, default=0, help="Watch interval in seconds (0=once)")
    args = parser.parse_args()

    async def run() -> None:
        checker = HealthChecker(base_url=args.url)
        while True:
            result = await checker.check_all()
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                status_icon = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}
                print(f"\n{'='*60}")
                print(f"  SuperAI Platform Health: {status_icon.get(result['overall_status'], '?')} {result['overall_status'].upper()}")
                print(f"  Services: {result['healthy_services']} healthy")
                print(f"  Duration: {result['check_duration_ms']:.1f}ms")
                print(f"{'='*60}")
                for name, info in result["services"].items():
                    icon = status_icon.get(info.get("status", ""), "?")
                    extra = info.get("version", info.get("error", ""))[:40]
                    print(f"  {icon} {name:20s} {info.get('status', 'unknown'):12s} {extra}")
                print()

            if args.watch <= 0:
                break
            await asyncio.sleep(args.watch)

    asyncio.run(run())


if __name__ == "__main__":
    main()