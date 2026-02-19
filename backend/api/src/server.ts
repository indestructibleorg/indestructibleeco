import "express-async-errors";
import express from "express";
import cors from "cors";
import helmet from "helmet";
import { createServer } from "http";
import { Server as SocketIOServer } from "socket.io";
import pino from "pino";
import pinoHttp from "pino-http";

import { authRouter } from "./routes/auth";
import { platformRouter } from "./routes/platforms";
import { yamlRouter } from "./routes/yaml";
import { aiRouter } from "./routes/ai";
import { healthRouter } from "./routes/health";
import { errorHandler } from "./middleware/error-handler";
import { rateLimiter } from "./middleware/rate-limiter";
import { authMiddleware } from "./middleware/auth";
import { setupWebSocket } from "./ws/handler";
import { config } from "./config";

const logger = pino({
  level: config.logLevel,
  ...(config.logFormat === "json" ? {} : { transport: { target: "pino-pretty" } }),
});

const app = express();
const httpServer = createServer(app);

// ─── Socket.IO ───
const io = new SocketIOServer(httpServer, {
  cors: { origin: config.corsOrigins, credentials: true },
  path: "/ws",
});

// ─── Global Middleware ───
app.use(helmet());
app.use(cors({ origin: config.corsOrigins, credentials: true }));
app.use(express.json({ limit: "10mb" }));
app.use(pinoHttp({ logger }));

// ─── Public Routes (no auth) ───
app.use("/health", healthRouter);
app.use("/ready", healthRouter);
app.use("/auth", authRouter);

// ─── Rate Limiter ───
app.use("/api", rateLimiter);

// ─── Protected Routes ───
app.use("/api/v1/platforms", authMiddleware, platformRouter);
app.use("/api/v1/yaml", authMiddleware, yamlRouter);
app.use("/api/v1/ai", authMiddleware, aiRouter);

// ─── Error Handler ───
app.use(errorHandler);

// ─── WebSocket ───
setupWebSocket(io, logger);

// ─── Start ───
httpServer.listen(config.port, () => {
  logger.info({
    msg: "IndestructibleEco API started",
    port: config.port,
    env: config.nodeEnv,
    uri: `indestructibleeco://backend/api/server`,
  });
});

export { app, io, logger };