import { Router, Request, Response, NextFunction } from "express";
import { requireAuth, AuthenticatedRequest } from "../middleware/auth";
import { config } from "../config";
import { v1 as uuidv1 } from "uuid";

export const aiRouter = Router();
aiRouter.use(requireAuth);

// POST /api/v1/ai/generate — Proxy to backend/ai /api/v1/generate
aiRouter.post("/generate", async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const { prompt, model_id, params, max_tokens, temperature, top_p } = req.body;

    if (!prompt) {
      res.status(400).json({ error: "validation_error", message: "prompt is required" });
      return;
    }

    const aiPayload = {
      prompt: prompt,
      model_id: model_id || "default",
      params: params || {},
      max_tokens: max_tokens || 2048,
      temperature: temperature ?? 0.7,
      top_p: top_p ?? 0.9,
    };

    const upstream = await fetch(`${config.aiServiceHttp}/api/v1/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(aiPayload),
      signal: AbortSignal.timeout(30000),
    });

    const data = await upstream.json();

    if (!upstream.ok) {
      res.status(upstream.status).json(data);
      return;
    }

    res.status(200).json(data);
  } catch (err) {
    if (err instanceof Error && err.name === "TimeoutError") {
      res.status(504).json({ error: "gateway_timeout", message: "AI service did not respond in time" });
      return;
    }
    next(err);
  }
});

// POST /api/v1/ai/chat/completions — Proxy to backend/ai /v1/chat/completions
aiRouter.post("/chat/completions", async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const upstream = await fetch(`${config.aiServiceHttp}/v1/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": req.headers.authorization || "",
      },
      body: JSON.stringify(req.body),
      signal: AbortSignal.timeout(60000),
    });

    const data = await upstream.json();

    if (!upstream.ok) {
      res.status(upstream.status).json(data);
      return;
    }

    res.status(200).json(data);
  } catch (err) {
    if (err instanceof Error && err.name === "TimeoutError") {
      res.status(504).json({ error: "gateway_timeout", message: "AI service did not respond in time" });
      return;
    }
    next(err);
  }
});

// POST /api/v1/ai/vector/align — Proxy to backend/ai /api/v1/vector/align
aiRouter.post("/vector/align", async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const upstream = await fetch(`${config.aiServiceHttp}/api/v1/vector/align`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req.body),
      signal: AbortSignal.timeout(15000),
    });

    const data = await upstream.json();

    if (!upstream.ok) {
      res.status(upstream.status).json(data);
      return;
    }

    res.status(200).json(data);
  } catch (err) {
    if (err instanceof Error && err.name === "TimeoutError") {
      res.status(504).json({ error: "gateway_timeout", message: "AI service did not respond in time" });
      return;
    }
    next(err);
  }
});

// GET /api/v1/ai/models — Proxy to backend/ai /api/v1/models
aiRouter.get("/models", async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const upstream = await fetch(`${config.aiServiceHttp}/api/v1/models`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      signal: AbortSignal.timeout(10000),
    });

    const data = await upstream.json();

    if (!upstream.ok) {
      res.status(upstream.status).json(data);
      return;
    }

    res.status(200).json(data);
  } catch (err) {
    if (err instanceof Error && err.name === "TimeoutError") {
      res.status(504).json({ error: "gateway_timeout", message: "AI service did not respond in time" });
      return;
    }
    next(err);
  }
});

// GET /api/v1/ai/jobs/:jobId — Get job status
aiRouter.get("/jobs/:jobId", async (req: AuthenticatedRequest, res: Response): Promise<void> => {
  const jobId = req.params.jobId;
  res.status(200).json({
    id: jobId,
    status: "pending",
    result: null,
    uri: `indestructibleeco://ai/job/${jobId}`,
    urn: `urn:indestructibleeco:ai:job:${jobId}:${uuidv1()}`,
  });
});
