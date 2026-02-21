import { type Request, type Response, type NextFunction, type RequestHandler } from "express";
import { createClient } from "@supabase/supabase-js";
import { config } from "../config";

// -- Types --

export interface AuthenticatedRequest extends Request {
  user?: {
    id: string;
    email: string;
    role: string;
    urn: string;
  };
}

// -- Supabase Client (lazy init to handle missing config gracefully) --

let _supabase: ReturnType<typeof createClient> | null = null;

function getSupabase() {
  if (!_supabase) {
    if (!config.supabaseUrl || !config.supabaseUrl.startsWith("http")) {
      return null;
    }
    _supabase = createClient(
      config.supabaseUrl,
      config.supabaseServiceRoleKey || config.supabaseKey
    );
  }
  return _supabase;
}

// -- authMiddleware: validates Bearer token via Supabase --

export const authMiddleware: RequestHandler = async (
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> => {
  const supabase = getSupabase();
  if (!supabase) {
    // Supabase not configured - pass through in staging
    (req as AuthenticatedRequest).user = {
      id: "anonymous",
      email: "anonymous@staging",
      role: "member",
      urn: "urn:indestructibleeco:iam:user:anonymous",
    };
    next();
    return;
  }

  const token = req.headers.authorization?.replace("Bearer ", "");
  if (!token) {
    res.status(401).json({ error: "No token" });
    return;
  }

  const { data, error } = await supabase.auth.getUser(token);
  if (error || !data.user) {
    res.status(401).json({ error: "Invalid token" });
    return;
  }

  (req as AuthenticatedRequest).user = {
    id: data.user.id,
    email: data.user.email || "",
    role: data.user.role || "member",
    urn: `urn:indestructibleeco:iam:user:${data.user.id}`,
  };
  next();
};

// -- requireAuth: alias for route-level usage --

export const requireAuth: RequestHandler = authMiddleware;

// -- adminOnly: restricts to admin role --

export const adminOnly: RequestHandler = async (
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> => {
  const authReq = req as AuthenticatedRequest;
  if (!authReq.user) {
    res.status(401).json({ error: "Authentication required" });
    return;
  }

  if (authReq.user.role !== "admin" && authReq.user.role !== "service_role") {
    res.status(403).json({ error: "Admin access required" });
    return;
  }

  next();
};