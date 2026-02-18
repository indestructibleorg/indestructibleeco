import { Router, Response, NextFunction } from "express";
import { v1 as uuidv1 } from "uuid";
import { AuthenticatedRequest } from "../middleware/auth";
import { AppError } from "../middleware/error-handler";
import { config } from "../config";

const aiRouter = Router();

// In-memory job store (production: Redis + Supabase)
const jobs = new Map<string, AIJobRecord>();

interface AIJobRecord {
  id: string;
  userId: string;
  modelId: string;
  prompt: string;
  status: "pending" | "running" | "completed" | "failed";
  uri: string;
  urn: string;
  result: string | null;
  error: string | null;
  progress: number;
  params: Record<string, unknown>;
  usage: { promptTokens: number; completionTokens: number; totalTokens: number } | null;
  createdAt: string;
  completedAt: string | null;
}

// POST /api/v1/ai/generate — Submit async generation job
aiRouter.post("/generate", async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const { prompt, model_id, params } = req.body;
    if (!prompt) {
      throw new AppError(400, "validation_error", "Prompt is required");
    }

    const jobId = uuidv1();
    const modelId = model_id || "default";

    const job: AIJobRecord = {
      id: jobId,
      userId: req.user!.id,
      modelId,
      prompt,
      status: "pending",
      uri: `indestructibleeco://ai/job/${jobId}`,
      urn: `urn:indestructibleeco:ai:job:${modelId}:${jobId}`,
      result: null,
      error: null,
      progress: 0,
      params: params || {},
      usage: null,
      createdAt: new Date().toISOString(),
      completedAt: null,
    };

    jobs.set(jobId, job);

    // Dispatch to AI service (async via Celery/Redis in production)
    dispatchToAIService(job).catch(() => {});

    res.status(202).json({
      jobId,
      status: "pending",
      uri: job.uri,
      urn: job.urn,
      pollUrl: `/api/v1/ai/jobs/${jobId}`,
    });
  } catch (err) {
    next(err);
  }
});

// GET /api/v1/ai/jobs/:jobId — Poll job status
aiRouter.get("/jobs/:jobId", async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const job = jobs.get(req.params.jobId);
    if (!job) {
      throw new AppError(404, "not_found", "Job not found");
    }

    if (job.userId !== req.user!.id && req.user!.role !== "admin") {
      throw new AppError(403, "forbidden", "Access denied to this job");
    }

    res.status(200).json({
      jobId: job.id,
      status: job.status,
      progress: job.progress,
      uri: job.uri,
      urn: job.urn,
      result: job.result,
      error: job.error,
      usage: job.usage,
      createdAt: job.createdAt,
      completedAt: job.completedAt,
    });
  } catch (err) {
    next(err);
  }
});

// POST /api/v1/ai/vector/align — Compute vector alignment
aiRouter.post("/vector/align", async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const { tokens, target_dim } = req.body;
    if (!tokens || !Array.isArray(tokens)) {
      throw new AppError(400, "validation_error", "Tokens array is required");
    }

    const dim = target_dim || 1024;
    if (dim < 1024 || dim > 4096) {
      throw new AppError(400, "validation_error", "target_dim must be between 1024 and 4096");
    }

    // Forward to AI service
    try {
      const response = await fetch(`${config.aiServiceHttp}/api/v1/vector/align`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tokens, target_dim: dim }),
        signal: AbortSignal.timeout(30000),
      });

      if (response.ok) {
        const data = await response.json();
        res.status(200).json(data);
        return;
      }
    } catch {
      // Fallback to mock response
    }

    // Mock response when AI service unavailable
    const mockVector = Array.from({ length: Math.min(dim, 10) }, () =>
      parseFloat((Math.random() * 2 - 1).toFixed(6))
    );

    res.status(200).json({
      alignment_model: "quantum-bert-xxl-v1",
      coherence_vector: mockVector,
      dimension: dim,
      function_keywords: tokens.slice(0, 5),
      alignment_score: parseFloat((0.8 + Math.random() * 0.2).toFixed(4)),
      note: "mock_response_ai_service_unavailable",
    });
  } catch (err) {
    next(err);
  }
});

// GET /api/v1/ai/models — List available models
aiRouter.get("/models", async (_req: AuthenticatedRequest, res: Response) => {
  const models = [
    {
      id: "vllm-default",
      name: "vLLM Default",
      provider: "vllm",
      status: "available",
      uri: "indestructibleeco://ai/model/vllm-default",
    },
    {
      id: "ollama-default",
      name: "Ollama Default",
      provider: "ollama",
      status: "available",
      uri: "indestructibleeco://ai/model/ollama-default",
    },
    {
      id: "tgi-default",
      name: "TGI Default",
      provider: "tgi",
      status: "available",
      uri: "indestructibleeco://ai/model/tgi-default",
    },
    {
      id: "sglang-default",
      name: "SGLang Default",
      provider: "sglang",
      status: "available",
      uri: "indestructibleeco://ai/model/sglang-default",
    },
  ];

  res.status(200).json({ models, total: models.length });
});

// ─── Internal: Dispatch to AI Service ───
async function dispatchToAIService(job: AIJobRecord): Promise<void> {
  const record = jobs.get(job.id);
  if (!record) return;

  record.status = "running";
  record.progress = 0.1;

  try {
    const response = await fetch(`${config.aiServiceHttp}/api/v1/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: job.prompt,
        model_id: job.modelId,
        params: job.params,
      }),
      signal: AbortSignal.timeout(120000),
    });

    if (response.ok) {
      const data = await response.json();
      record.status = "completed";
      record.progress = 1.0;
      record.result = data.content || data.result || JSON.stringify(data);
      record.usage = data.usage || null;
      record.completedAt = new Date().toISOString();
    } else {
      record.status = "failed";
      record.error = `AI service returned HTTP ${response.status}`;
      record.completedAt = new Date().toISOString();
    }
  } catch (err) {
    record.status = "failed";
    record.error = (err as Error).message;
    record.completedAt = new Date().toISOString();
  }
}

export { aiRouter };