import { type RequestHandler } from "express";
// TODO: wire up Redis-backed sliding window rate limiter
// e.g. express-rate-limit + rate-limit-redis
export const rateLimiter: RequestHandler = (_req, _res, next) => next();