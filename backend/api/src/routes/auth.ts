import { Router, Request, Response, NextFunction } from "express";
import { createClient } from "@supabase/supabase-js";
import jwt from "jsonwebtoken";
import { v1 as uuidv1 } from "uuid";
import { config } from "../config";
import { AppError } from "../middleware/error-handler";
import { AuthenticatedRequest, authMiddleware } from "../middleware/auth";

const authRouter = Router();

const supabase = createClient(
  config.supabaseUrl || "https://placeholder.supabase.co",
  config.supabaseKey || "placeholder-key"
);

function signToken(user: { id: string; email: string; role: string }): {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
} {
  const accessToken = jwt.sign(
    { sub: user.id, email: user.email, role: user.role },
    config.jwtSecret,
    { expiresIn: "1h" }
  );
  const refreshToken = jwt.sign(
    { sub: user.id, type: "refresh" },
    config.jwtSecret,
    { expiresIn: "7d" }
  );
  return { accessToken, refreshToken, expiresIn: 3600 };
}

// POST /auth/signup
authRouter.post("/signup", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { email, password } = req.body;
    if (!email || !password) {
      throw new AppError(400, "validation_error", "Email and password are required");
    }

    const { data, error } = await supabase.auth.signUp({ email, password });
    if (error) {
      throw new AppError(400, "signup_failed", error.message);
    }

    const userId = data.user?.id || uuidv1();
    const tokens = signToken({ id: userId, email, role: "member" });

    res.status(201).json({
      user: {
        id: userId,
        email,
        role: "member",
        uri: `indestructibleeco://iam/user/${email}`,
        urn: `urn:indestructibleeco:iam:user:${email}:${userId}`,
      },
      ...tokens,
    });
  } catch (err) {
    next(err);
  }
});

// POST /auth/login
authRouter.post("/login", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { email, password } = req.body;
    if (!email || !password) {
      throw new AppError(400, "validation_error", "Email and password are required");
    }

    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
      throw new AppError(401, "login_failed", "Invalid email or password");
    }

    const userId = data.user?.id || uuidv1();
    const role = data.user?.user_metadata?.role || "member";
    const tokens = signToken({ id: userId, email, role });

    res.status(200).json({
      user: {
        id: userId,
        email,
        role,
        uri: `indestructibleeco://iam/user/${email}`,
        urn: `urn:indestructibleeco:iam:user:${email}:${userId}`,
      },
      ...tokens,
    });
  } catch (err) {
    next(err);
  }
});

// POST /auth/refresh
authRouter.post("/refresh", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { refreshToken } = req.body;
    if (!refreshToken) {
      throw new AppError(400, "validation_error", "Refresh token is required");
    }

    const payload = jwt.verify(refreshToken, config.jwtSecret) as {
      sub: string;
      type: string;
    };

    if (payload.type !== "refresh") {
      throw new AppError(401, "invalid_token", "Not a refresh token");
    }

    const tokens = signToken({
      id: payload.sub,
      email: "",
      role: "member",
    });

    res.status(200).json(tokens);
  } catch (err) {
    if (err instanceof jwt.JsonWebTokenError) {
      next(new AppError(401, "invalid_token", "Invalid or expired refresh token"));
    } else {
      next(err);
    }
  }
});

// POST /auth/logout
authRouter.post("/logout", authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  // In production: invalidate token in Redis blacklist
  res.status(200).json({
    message: "Logged out successfully",
    userId: req.user?.id,
  });
});

// GET /auth/me
authRouter.get("/me", authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  res.status(200).json({
    user: {
      id: req.user!.id,
      email: req.user!.email,
      role: req.user!.role,
      uri: `indestructibleeco://iam/user/${req.user!.email}`,
      urn: req.user!.urn,
    },
  });
});

export { authRouter };