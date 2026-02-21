import { Router, Request, Response, NextFunction } from "express";
import { getSupabase } from "../services/supabase";
import { requireAuth, AuthenticatedRequest } from "../middleware/auth";
import { v1 as uuidv1 } from "uuid";

export const authRouter = Router();

// Supabase client accessed via getSupabase() - lazy init

// POST /auth/signup — Create account via Supabase Auth
authRouter.post("/signup", async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const { email, password, display_name } = req.body;

    if (!email || !password) {
      res.status(400).json({ error: "validation_error", message: "Email and password are required" });
      return;
    }

    const { data, error } = await getSupabase()?.auth?.signUp({
      email,
      password,
      options: {
        data: { display_name: display_name || "" },
      },
    });

    if (error) {
      const status = error.message.includes("already registered") ? 409 : 400;
      res.status(status).json({ error: "auth_error", message: error.message });
      return;
    }

    res.status(201).json({
      user: {
        id: data.user?.id,
        email: data.user?.email,
        urn: `urn:indestructibleeco:iam:user:${data.user?.id}`,
      },
      session: data.session
        ? {
            access_token: data.session.access_token,
            refresh_token: data.session.refresh_token,
            expires_at: data.session.expires_at,
          }
        : null,
    });
  } catch (err) {
    next(err);
  }
});

// POST /auth/login — Sign in via Supabase Auth
authRouter.post("/login", async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      res.status(400).json({ error: "validation_error", message: "Email and password are required" });
      return;
    }

    const { data, error } = await getSupabase()?.auth?.signInWithPassword({
      email,
      password,
    });

    if (error) {
      res.status(401).json({ error: "auth_error", message: error.message });
      return;
    }

    res.status(200).json({
      user: {
        id: data.user.id,
        email: data.user.email,
        role: data.user.role || "member",
        urn: `urn:indestructibleeco:iam:user:${data.user.id}`,
      },
      session: {
        access_token: data.session.access_token,
        refresh_token: data.session.refresh_token,
        expires_at: data.session.expires_at,
      },
    });
  } catch (err) {
    next(err);
  }
});

// POST /auth/refresh — Refresh session token
authRouter.post("/refresh", async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const { refresh_token } = req.body;

    if (!refresh_token) {
      res.status(400).json({ error: "validation_error", message: "refresh_token is required" });
      return;
    }

    const { data, error } = await getSupabase()?.auth?.refreshSession({
      refresh_token,
    });

    if (error) {
      res.status(401).json({ error: "auth_error", message: error.message });
      return;
    }

    if (!data.session) {
      res.status(401).json({ error: "auth_error", message: "Session expired" });
      return;
    }

    res.status(200).json({
      session: {
        access_token: data.session.access_token,
        refresh_token: data.session.refresh_token,
        expires_at: data.session.expires_at,
      },
    });
  } catch (err) {
    next(err);
  }
});

// POST /auth/logout — Sign out (requires auth)
authRouter.post("/logout", requireAuth, async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const token = req.headers.authorization?.replace("Bearer ", "");
    if (token) {
      await getSupabase()?.auth?.admin.signOut(token);
    }
    res.status(200).json({ ok: true });
  } catch (err) {
    next(err);
  }
});

// GET /auth/me — Get current user profile (requires auth)
authRouter.get("/me", requireAuth, async (req: Request, res: Response): Promise<void> => {
  const authReq = req as AuthenticatedRequest;
  res.status(200).json({
    user: authReq.user,
    uri: "indestructibleeco://backend/api/auth/me",
  });
});
