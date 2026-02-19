import { type ErrorRequestHandler } from "express";
import pino from "pino";

const logger = pino();

export const errorHandler: ErrorRequestHandler = (err, _req, res, _next) => {
  logger.error(err);
  res.status(err.status ?? 500).json({ error: err.message ?? "Internal server error" });
};