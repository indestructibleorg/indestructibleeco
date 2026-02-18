import { Request, Response, NextFunction } from "express";
import pino from "pino";

const logger = pino({ level: process.env.LOG_LEVEL || "info" });

export class AppError extends Error {
  constructor(
    public statusCode: number,
    public code: string,
    message: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = "AppError";
  }
}

export function errorHandler(
  err: Error,
  _req: Request,
  res: Response,
  _next: NextFunction
): void {
  if (err instanceof AppError) {
    logger.warn({
      err: err.code,
      statusCode: err.statusCode,
      message: err.message,
      details: err.details,
    });

    res.status(err.statusCode).json({
      error: err.code,
      message: err.message,
      ...(err.details ? { details: err.details } : {}),
    });
    return;
  }

  logger.error({
    err: err.message,
    stack: err.stack,
    name: err.name,
  });

  res.status(500).json({
    error: "internal_server_error",
    message:
      process.env.NODE_ENV === "production"
        ? "An unexpected error occurred"
        : err.message,
  });
}