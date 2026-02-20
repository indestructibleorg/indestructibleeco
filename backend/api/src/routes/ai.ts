/**
 * IndestructibleEco — AI Routes
 * URI: indestructibleeco://backend/api/routes/ai
 *
 * Proxies to backend/ai via ai-proxy service.
 * Persists jobs to Supabase for tracking and WebSocket push.
 */

import { Router, Response, NextFunction } from "express";
import { requireAuth, AuthenticatedRequest } from "../middleware/auth";
import { v1 as uuidv1 } from "uuid";
import * as aiProxy from "../services/ai-proxy";
import * as db from "../services/supabase";

export const aiRouter = Router();
aiRouter.use(requireAuth);

// POST /api/v1/ai/generate — Proxy to backend/ai, persist job
aiRouter.post("/generate", async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const { prompt, model_id, max_tokens, temperature, top_p } = req.body;

    if (!prompt) {
      res.status(400).json({ error: "validation_error", message: "prompt is required" });
      return;
    }

    const jobId = uuidv1();

    // Persist job to Supabase
    await db.createAiJob({
      user_id: req.user!.id,
      prompt,
      model_id: model_id || "default",
      model_params: {
        temperature: temperature ?? 0.7,
        top_p: top_p ?? 0.9,
        max_tokens: max_tokens ?? 2048,
        stream: false,
      },
      uri: `indestructibleeco://ai/job/${jobId}`,
      urn: `urn:indestructibleeco:ai:job:${jobId}`,
    });

    // Proxy to AI service
    let data: aiProxy.AiGenerateResponse;
    try {
      data = await aiProxy.generate({
        prompt,
        model_id: model_id || "default",
        max_tokens: max_tokens ?? 2048,
        temperature: temperature ?? 0.7,
        top_p: top_p ?? 0.9,
      });
    } catch (err: unknown) {
      if (isProxyErr(err) && err.upstream) {
        res.status(err.status).json({ error: err.error, message: err.message });
        return;
      }
      throw err;
    }

    res.status(200).json(data);
  } catch (err) {
    next(err);
  }
});

// POST /api/v1/ai/chat/completions — OpenAI-compatible proxy
aiRouter.post("/chat/completions", async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    let data: aiProxy.AiChatResponse;
    try {
      data = await aiProxy.chatCompletions(req.body, req.headers.authorization);
    } catch (err: unknown) {
      if (isProxyErr(err) && err.upstream) {
        res.status(err.status).json({ error: err.error, message: err.message });
        return;
      }
      throw err;
    }

    res.status(200).json(data);
  } catch (err) {
    next(err);
  }
});

// POST /api/v1/ai/vector/align — Vector alignment proxy
aiRouter.post("/vector/align", async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    let data: aiProxy.AiVectorAlignResponse;
    try {
      data = await aiProxy.vectorAlign(req.body);
    } catch (err: unknown) {
      if (isProxyErr(err) && err.upstream) {
        res.status(err.status).json({ error: err.error, message: err.message });
        return;
      }
      throw err;
    }

    res.status(200).json(data);
  } catch (err) {
    next(err);
  }
});

// GET /api/v1/ai/models — List available models
aiRouter.get("/models", async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    let models: aiProxy.AiModelInfo[];
    try {
      models = await aiProxy.listModels();
    } catch (err: unknown) {
      if (isProxyErr(err) && err.upstream) {
        res.status(err.status).json({ error: err.error, message: err.message });
        return;
      }
      throw err;
    }

    res.status(200).json({ models });
  } catch (err) {
    next(err);
  }
});

// GET /api/v1/ai/jobs/:jobId — Get job status from Supabase
aiRouter.get("/jobs/:jobId", async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const job = await db.getAiJob(req.params.jobId as string);
    if (!job) {
      res.status(404).json({ error: "not_found", message: "Job not found" });
      return;
    }

    // Verify ownership (non-admin can only see own jobs)
    if (req.user!.role !== "admin" && req.user!.role !== "service_role" && job.user_id !== req.user!.id) {
      res.status(403).json({ error: "forbidden", message: "Access denied" });
      return;
    }

    res.status(200).json({
      id: job.id,
      status: job.status,
      prompt: job.prompt,
      model_id: job.model_id,
      engine: job.engine,
      result: job.result,
      error: job.error,
      usage: job.usage,
      latency_ms: job.latency_ms,
      uri: job.uri || `indestructibleeco://ai/job/${job.id}`,
      urn: job.urn || `urn:indestructibleeco:ai:job:${job.id}`,
      created_at: job.created_at,
      completed_at: job.completed_at,
    });
  } catch (err) {
    next(err);
  }
});

// GET /api/v1/ai/jobs — List user's jobs
aiRouter.get("/jobs", async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const limit = Math.min(parseInt(String(req.query.limit || "50"), 10), 200);
    const jobs = await db.listAiJobsByUser(req.user!.id, limit);
    res.status(200).json({ jobs, total: jobs.length });
  } catch (err) {
    next(err);
  }
});

// ── Helpers ──────────────────────────────────────────────────────────────────

function isProxyErr(err: unknown): err is aiProxy.AiProxyError {
  return typeof err === "object" && err !== null && "upstream" in err && "status" in err;
}