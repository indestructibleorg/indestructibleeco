import { type RequestHandler } from "express";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export const requireAuth: RequestHandler = async (req, res, next) => {
  const token = req.headers.authorization?.replace("Bearer ", "");
  if (!token) { res.status(401).json({ error: "No token" }); return; }

  const { data, error } = await supabase.auth.getUser(token);
  if (error || !data.user) { res.status(401).json({ error: "Invalid token" }); return; }

  (req as any).user = data.user;
  next();
};