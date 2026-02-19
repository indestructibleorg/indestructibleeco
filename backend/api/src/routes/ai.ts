import { Router } from "express";
import { requireAuth } from "../middleware/auth";
import { v4 as uuidv4 } from "uuid";

export const aiRouter = Router();
aiRouter.use(requireAuth);

aiRouter.post("/generate", async (req, res) => {
  const jobId = uuidv4();
  // TODO: enqueue to Redis/Celery AI worker
  res.status(202).json({ job_id: jobId, status: "queued" });
});

aiRouter.get("/jobs/:jobId", async (req, res) => {
  res.json({ id: req.params.jobId, status: "pending", result: null });
});

aiRouter.get("/models", async (_req, res) => {
  res.json({ models: [{ id: "quantum-bert-xxl-v1", dim_range: [1024, 4096], status: "available" }] });
});