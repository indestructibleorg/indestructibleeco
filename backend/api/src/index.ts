import "express-async-errors";
import express from "express";
import { createServer } from "http";
import { Server as SocketServer } from "socket.io";
import pino from "pino";
import pinoHttp from "pino-http";

import { authRouter }     from "./routes/auth";
import { platformRouter } from "./routes/platform";
import { yamlRouter }     from "./routes/yaml";
import { aiRouter }       from "./routes/ai";
import { errorHandler }   from "./middleware/error";
import { rateLimiter }    from "./middleware/ratelimit";

const PORT   = parseInt(process.env.PORT ?? "3000", 10);
const logger = pino({ level: process.env.LOG_LEVEL ?? "info" });

const app  = express();
const http = createServer(app);
const io   = new SocketServer(http, { cors: { origin: process.env.CORS_ORIGIN?.split(",") ?? [] } });

app.use(pinoHttp({ logger }));
app.use(express.json({ limit: "1mb" }));
app.use(rateLimiter);

// ── Health ──────────────────────────────────────────────────────────────
app.get("/health", (_req, res) => res.json({ status: "ok", ts: new Date().toISOString() }));
app.get("/ready",  (_req, res) => res.json({ status: "ready" }));
app.get("/metrics", (_req, res) => res.type("text/plain").send("# Prometheus metrics placeholder\n"));

// ── Routes ──────────────────────────────────────────────────────────────
app.use("/auth",        authRouter);
app.use("/api/v1/platforms", platformRouter);
app.use("/api/v1/yaml",      yamlRouter);
app.use("/api/v1/ai",        aiRouter);

app.use(errorHandler);

// ── WebSocket ────────────────────────────────────────────────────────────
io.on("connection", (socket) => {
  logger.info({ socketId: socket.id }, "WS client connected");
  socket.on("platform:register", (data) => {
    logger.info({ data }, "platform registered via WS");
    socket.emit("platform:status", { platformId: data.platformId, status: "active", timestamp: Date.now() });
  });
  socket.on("disconnect", () => logger.info({ socketId: socket.id }, "WS client disconnected"));
});

http.listen(PORT, () => logger.info({ port: PORT }, "indestructibleeco API listening"));