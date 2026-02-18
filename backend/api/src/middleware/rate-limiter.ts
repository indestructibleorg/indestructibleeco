import { Request, Response, NextFunction } from "express";
import Redis from "ioredis";
import { config } from "../config";
import { AuthenticatedRequest } from "./auth";

let redis: Redis | null = null;

try {
  redis = new Redis(config.redisUrl, {
    maxRetriesPerRequest: 3,
    lazyConnect: true,
    enableOfflineQueue: false,
  });
} catch {
  redis = null;
}

interface RateLimitEntry {
  count: number;
  resetAt: number;
}

const memoryStore = new Map<string, RateLimitEntry>();

function getKey(req: AuthenticatedRequest): string {
  const user = req.user;
  if (user) return `rl:user:${user.id}`;
  const ip = req.ip || req.socket.remoteAddress || "unknown";
  return `rl:ip:${ip}`;
}

function getLimit(req: AuthenticatedRequest): number {
  return req.user
    ? config.rateLimitAuthenticated
    : config.rateLimitPublic;
}

async function checkRedis(key: string, limit: number, windowMs: number): Promise<{ allowed: boolean; remaining: number; resetAt: number }> {
  if (!redis) throw new Error("no redis");

  const now = Date.now();
  const windowKey = `${key}:${Math.floor(now / windowMs)}`;

  const count = await redis.incr(windowKey);
  if (count === 1) {
    await redis.pexpire(windowKey, windowMs);
  }

  const ttl = await redis.pttl(windowKey);
  const resetAt = now + (ttl > 0 ? ttl : windowMs);

  return {
    allowed: count <= limit,
    remaining: Math.max(0, limit - count),
    resetAt,
  };
}

function checkMemory(key: string, limit: number, windowMs: number): { allowed: boolean; remaining: number; resetAt: number } {
  const now = Date.now();
  let entry = memoryStore.get(key);

  if (!entry || now >= entry.resetAt) {
    entry = { count: 0, resetAt: now + windowMs };
    memoryStore.set(key, entry);
  }

  entry.count++;

  return {
    allowed: entry.count <= limit,
    remaining: Math.max(0, limit - entry.count),
    resetAt: entry.resetAt,
  };
}

export async function rateLimiter(
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): Promise<void> {
  const key = getKey(req);
  const limit = getLimit(req);
  const windowMs = config.rateLimitWindowMs;

  let result: { allowed: boolean; remaining: number; resetAt: number };

  try {
    result = await checkRedis(key, limit, windowMs);
  } catch {
    result = checkMemory(key, limit, windowMs);
  }

  res.setHeader("X-RateLimit-Limit", limit);
  res.setHeader("X-RateLimit-Remaining", result.remaining);
  res.setHeader("X-RateLimit-Reset", Math.ceil(result.resetAt / 1000));

  if (!result.allowed) {
    res.status(429).json({
      error: "too_many_requests",
      message: `Rate limit exceeded. Limit: ${limit} requests per ${windowMs / 1000}s`,
      retryAfter: Math.ceil((result.resetAt - Date.now()) / 1000),
    });
    return;
  }

  next();
}