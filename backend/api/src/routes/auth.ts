import { Router } from "express";
import { requireAuth } from "../middleware/auth";

export const authRouter = Router();

authRouter.post("/signup",  async (req, res) => { res.status(501).json({ todo: "implement signup" }); });
authRouter.post("/login",   async (req, res) => { res.status(501).json({ todo: "implement login" }); });
authRouter.post("/refresh", async (req, res) => { res.status(501).json({ todo: "implement refresh" }); });
authRouter.post("/logout",  requireAuth, async (req, res) => { res.json({ ok: true }); });
authRouter.get("/me",       requireAuth, async (req, res) => { res.json((req as any).user); });