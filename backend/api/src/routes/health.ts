import { Router, Request, Response } from "express";
import Redis from "ioredis";
import { config } from "../config";
import { v1 as uuidv1 } from "uuid";

const healthRouter = Router();

interface ComponentHealth {
  status: "healthy" | "degraded" | "unhealthy";
  latencyMs?: number;
  message?: string;
}

async function checkRedis(): Promise<ComponentHealth> {
  try {
    const start = Date.now();
    const redis = new Redis(config.redisUrl, {
      connectTimeout: 2000,
      maxRetriesPerRequest: 1,
      lazyConnect: true,
    });
    await redis.ping();
    await redis.quit();
    return { status: "healthy", latencyMs: Date.now() - start };
  } catch (err) {
    return { status: "unhealthy", message: (err as Error).message };
  }
}

async function checkAIService(): Promise<ComponentHealth> {
  try {
    const start = Date.now();
    const res = await fetch(`${config.aiServiceHttp}/health`, {
      signal: AbortSignal.timeout(3000),
    });
    if (res.ok) {
      return { status: "healthy", latencyMs: Date.now() - start };
    }
    return { status: "degraded", message: `HTTP ${res.status}` };
  } catch (err) {
    return { status: "unhealthy", message: (err as Error).message };
  }
}

// GET /health — Liveness probe
healthRouter.get("/", (_req: Request, res: Response) => {
  res.status(200).json({
    status: "healthy",
    service: "api",
    version: "1.0.0",
    uri: "indestructibleeco://backend/api/health",
    urn: `urn:indestructibleeco:backend:api:health:${uuidv1()}`,
    timestamp: new Date().toISOString(),
  });
});

// GET /ready — Readiness probe (checks dependencies)
healthRouter.get("/ready", async (_req: Request, res: Response) => {
  const [redis, ai] = await Promise.all([checkRedis(), checkAIService()]);

  const components: Record<string, ComponentHealth> = { redis, ai };
  const allHealthy = Object.values(components).every(
    (c) => c.status === "healthy"
  );
  const anyUnhealthy = Object.values(components).some(
    (c) => c.status === "unhealthy"
  );

  const overallStatus = allHealthy
    ? "healthy"
    : anyUnhealthy
    ? "unhealthy"
    : "degraded";

  const statusCode = overallStatus === "unhealthy" ? 503 : 200;

  res.status(statusCode).json({
    status: overallStatus,
    service: "api",
    version: "1.0.0",
    uri: "indestructibleeco://backend/api/ready",
    components,
    timestamp: new Date().toISOString(),
  });
});

// GET /metrics — Prometheus-compatible metrics
healthRouter.get("/metrics", (_req: Request, res: Response) => {
  const uptime = process.uptime();
  const mem = process.memoryUsage();

  const metrics = [
    `# HELP api_uptime_seconds API service uptime in seconds`,
    `# TYPE api_uptime_seconds gauge`,
    `api_uptime_seconds ${uptime.toFixed(2)}`,
    `# HELP api_memory_heap_used_bytes Heap memory used`,
    `# TYPE api_memory_heap_used_bytes gauge`,
    `api_memory_heap_used_bytes ${mem.heapUsed}`,
    `# HELP api_memory_heap_total_bytes Total heap memory`,
    `# TYPE api_memory_heap_total_bytes gauge`,
    `api_memory_heap_total_bytes ${mem.heapTotal}`,
    `# HELP api_memory_rss_bytes Resident set size`,
    `# TYPE api_memory_rss_bytes gauge`,
    `api_memory_rss_bytes ${mem.rss}`,
  ].join("\n");

  res.setHeader("Content-Type", "text/plain; version=0.0.4");
  res.status(200).send(metrics + "\n");
});

export { healthRouter };