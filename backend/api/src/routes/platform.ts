import { Router } from "express";
import { requireAuth } from "../middleware/auth";

export const platformRouter = Router();
platformRouter.use(requireAuth);

platformRouter.get("/",     async (_req, res) => res.json({ platforms: [] }));
platformRouter.post("/",    async (req, res)  => res.status(201).json({ id: "new", ...req.body }));
platformRouter.get("/:id",  async (req, res)  => res.json({ id: req.params.id }));
platformRouter.patch("/:id",async (req, res)  => res.json({ id: req.params.id, ...req.body }));
platformRouter.delete("/:id",async (req, res) => res.status(204).send());