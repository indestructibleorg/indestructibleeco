import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";
import { config } from "../config";

export interface AuthenticatedRequest extends Request {
  user?: {
    id: string;
    email: string;
    role: string;
    urn: string;
  };
}

export function authMiddleware(
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): void {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    res.status(401).json({
      error: "unauthorized",
      message: "Missing or invalid Authorization header",
    });
    return;
  }

  const token = authHeader.slice(7);

  try {
    const payload = jwt.verify(token, config.jwtSecret) as {
      sub: string;
      email: string;
      role: string;
    };

    req.user = {
      id: payload.sub,
      email: payload.email,
      role: payload.role,
      urn: `urn:indestructibleeco:iam:user:${payload.email}:${payload.sub}`,
    };

    next();
  } catch (err) {
    res.status(401).json({
      error: "unauthorized",
      message: "Invalid or expired token",
    });
  }
}

export function adminOnly(
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): void {
  if (!req.user || req.user.role !== "admin") {
    res.status(403).json({
      error: "forbidden",
      message: "Admin access required",
    });
    return;
  }
  next();
}