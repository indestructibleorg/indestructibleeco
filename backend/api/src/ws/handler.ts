import { Server as SocketIOServer, Socket } from "socket.io";
import { Logger } from "pino";
import jwt from "jsonwebtoken";

const config = {
  jwtSecret: process.env.JWT_SECRET || "dev-secret-change-in-production",
};

interface AuthenticatedSocket extends Socket {
  user?: {
    id: string;
    email: string;
    role: string;
    urn: string;
  };
}

// ─── Event Types (AsyncAPI 2.6 compliant) ───
// Server → Client:
//   platform:status    { platformId, status, timestamp }
//   ai:job:progress    { jobId, progress, partial_result }
//   ai:job:complete    { jobId, result, qyaml_uri }
//   yaml:generated     { serviceId, qyaml_content, valid }
//   im:message:in      { channel, userId, text, intent }
//
// Client → Server:
//   platform:register  { platformId, capabilities[] }

export function setupWebSocket(io: SocketIOServer, logger: Logger): void {
  // ─── Auth Middleware ───
  io.use((socket: AuthenticatedSocket, next) => {
    const token =
      socket.handshake.auth?.token ||
      socket.handshake.headers?.authorization?.replace("Bearer ", "");

    if (!token) {
      return next(new Error("Authentication required"));
    }

    try {
      const payload = jwt.verify(token, config.jwtSecret) as {
        sub: string;
        email: string;
        role: string;
      };

      socket.user = {
        id: payload.sub,
        email: payload.email,
        role: payload.role,
        urn: `urn:indestructibleeco:iam:user:${payload.email}:${payload.sub}`,
      };

      next();
    } catch {
      next(new Error("Invalid token"));
    }
  });

  io.on("connection", (socket: AuthenticatedSocket) => {
    const user = socket.user!;
    logger.info({ userId: user.id, socketId: socket.id, msg: "WebSocket connected" });

    // Join user-specific room
    socket.join(`user:${user.id}`);

    // ─── Client → Server: platform:register ───
    socket.on("platform:register", (data: { platformId: string; capabilities: string[] }) => {
      logger.info({
        msg: "Platform registered via WebSocket",
        platformId: data.platformId,
        capabilities: data.capabilities,
        userId: user.id,
      });

      socket.join(`platform:${data.platformId}`);

      // Broadcast status to all connected clients
      io.emit("platform:status", {
        platformId: data.platformId,
        status: "registered",
        timestamp: new Date().toISOString(),
      });
    });

    // ─── Disconnect ───
    socket.on("disconnect", (reason) => {
      logger.info({ userId: user.id, socketId: socket.id, reason, msg: "WebSocket disconnected" });
    });

    // ─── Error ───
    socket.on("error", (err) => {
      logger.error({ userId: user.id, socketId: socket.id, err: err.message, msg: "WebSocket error" });
    });
  });
}

// ─── Emit Helpers (used by route handlers) ───
export function emitJobProgress(
  io: SocketIOServer,
  userId: string,
  jobId: string,
  progress: number,
  partialResult?: string
): void {
  io.to(`user:${userId}`).emit("ai:job:progress", {
    jobId,
    progress,
    partial_result: partialResult || null,
  });
}

export function emitJobComplete(
  io: SocketIOServer,
  userId: string,
  jobId: string,
  result: string,
  qyamlUri?: string
): void {
  io.to(`user:${userId}`).emit("ai:job:complete", {
    jobId,
    result,
    qyaml_uri: qyamlUri || null,
  });
}

export function emitYAMLGenerated(
  io: SocketIOServer,
  serviceId: string,
  qyamlContent: string,
  valid: boolean
): void {
  io.emit("yaml:generated", {
    serviceId,
    qyaml_content: qyamlContent,
    valid,
  });
}

export function emitIMMessage(
  io: SocketIOServer,
  channel: string,
  userId: string,
  text: string,
  intent: string
): void {
  io.emit("im:message:in", {
    channel,
    userId,
    text,
    intent,
  });
}