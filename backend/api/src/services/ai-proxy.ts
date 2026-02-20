/**
 * IndestructibleEco — AI Service Proxy
 * URI: indestructibleeco://backend/api/services/ai-proxy
 *
 * HTTP proxy to backend/ai FastAPI service with:
 * - Configurable timeout per endpoint
 * - Automatic retry with exponential backoff (max 2 retries)
 * - Structured error mapping
 * - Request/response logging hooks
 */

import { config } from "../config";

// ── Types ────────────────────────────────────────────────────────────────────

export interface AiGenerateRequest {
  prompt: string;
  model_id?: string;
  params?: Record<string, unknown>;
  max_tokens?: number;
  temperature?: number;
  top_p?: number;
}

export interface AiGenerateResponse {
  request_id: string;
  content: string;
  model_id: string;
  engine: string;
  usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
  finish_reason: string;
  latency_ms: number;
}

export interface AiChatRequest {
  model?: string;
  messages: { role: string; content: string }[];
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

export interface AiChatResponse {
  id: string;
  object: string;
  model: string;
  choices: { index: number; message: { role: string; content: string }; finish_reason: string }[];
  usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
}

export interface AiModelInfo {
  id: string;
  name: string;
  provider: string;
  status: string;
  capabilities: string[];
  uri: string;
  urn: string;
}

export interface AiVectorAlignRequest {
  tokens: string[];
  target_dim?: number;
  alignment_model?: string;
  tolerance?: number;
}

export interface AiVectorAlignResponse {
  coherence_vector: number[];
  dimension: number;
  alignment_model: string;
  alignment_score: number;
  function_keywords: string[];
}

export interface AiProxyError {
  error: string;
  message: string;
  status: number;
  upstream: boolean;
}

// ── Configuration ────────────────────────────────────────────────────────────

const TIMEOUTS: Record<string, number> = {
  generate: 30_000,
  chat: 60_000,
  vector: 15_000,
  models: 10_000,
  health: 5_000,
};

const MAX_RETRIES = 2;
const RETRY_BASE_MS = 500;

// ── Internal Helpers ─────────────────────────────────────────────────────────

async function proxyRequest<T>(
  method: string,
  path: string,
  body?: unknown,
  timeoutKey = "generate",
  headers?: Record<string, string>
): Promise<T> {
  const baseUrl = config.aiServiceHttp;
  const url = `${baseUrl}${path}`;
  const timeout = TIMEOUTS[timeoutKey] ?? TIMEOUTS.generate;

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const reqInit: RequestInit = {
        method,
        headers: {
          "Content-Type": "application/json",
          "X-Request-Source": "eco-api-proxy",
          ...(headers ?? {}),
        },
        signal: AbortSignal.timeout(timeout),
      };

      if (body && method !== "GET") {
        reqInit.body = JSON.stringify(body);
      }

      const resp = await fetch(url, reqInit);

      if (!resp.ok) {
        const errBody = (await resp.json().catch(() => ({ error: resp.statusText }))) as Record<string, string>;
        const proxyErr: AiProxyError = {
          error: errBody.error || "upstream_error",
          message: errBody.message || errBody.detail || resp.statusText,
          status: resp.status,
          upstream: true,
        };
        throw proxyErr;
      }

      return (await resp.json()) as T;
    } catch (err: unknown) {
      if (isProxyError(err)) {
        if (err.status >= 400 && err.status < 500) {
          throw err;
        }
      }

      if (err instanceof Error && err.name === "TimeoutError") {
        lastError = err;
        if (attempt < MAX_RETRIES) {
          await sleep(RETRY_BASE_MS * Math.pow(2, attempt));
          continue;
        }
        const timeoutErr: AiProxyError = {
          error: "gateway_timeout",
          message: "AI service did not respond in time",
          status: 504,
          upstream: true,
        };
        throw timeoutErr;
      }

      lastError = err instanceof Error ? err : new Error(String(err));
      if (attempt < MAX_RETRIES) {
        await sleep(RETRY_BASE_MS * Math.pow(2, attempt));
        continue;
      }
    }
  }

  const connErr: AiProxyError = {
    error: "service_unavailable",
    message: lastError?.message || "AI service is unreachable",
    status: 503,
    upstream: true,
  };
  throw connErr;
}

function isProxyError(err: unknown): err is AiProxyError {
  return typeof err === "object" && err !== null && "upstream" in err && "status" in err;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ── Public API ───────────────────────────────────────────────────────────────

export async function generate(req: AiGenerateRequest): Promise<AiGenerateResponse> {
  return proxyRequest<AiGenerateResponse>("POST", "/api/v1/generate", {
    prompt: req.prompt,
    model_id: req.model_id || "default",
    params: req.params || {},
    max_tokens: req.max_tokens ?? 2048,
    temperature: req.temperature ?? 0.7,
    top_p: req.top_p ?? 0.9,
  }, "generate");
}

export async function chatCompletions(
  req: AiChatRequest,
  authHeader?: string
): Promise<AiChatResponse> {
  const headers: Record<string, string> = {};
  if (authHeader) headers["Authorization"] = authHeader;
  return proxyRequest<AiChatResponse>("POST", "/v1/chat/completions", req, "chat", headers);
}

export async function vectorAlign(req: AiVectorAlignRequest): Promise<AiVectorAlignResponse> {
  return proxyRequest<AiVectorAlignResponse>("POST", "/api/v1/vector/align", req, "vector");
}

export async function listModels(): Promise<AiModelInfo[]> {
  const resp = await proxyRequest<{ models: AiModelInfo[] } | AiModelInfo[]>(
    "GET", "/api/v1/models", undefined, "models"
  );
  return Array.isArray(resp) ? resp : resp.models;
}

export async function healthCheck(): Promise<{ status: string; engines?: string[] }> {
  return proxyRequest<{ status: string; engines?: string[] }>("GET", "/health", undefined, "health");
}

export async function getJobStatus(jobId: string): Promise<{
  id: string;
  status: string;
  result: string | null;
  error: string | null;
  engine: string | null;
  latency_ms: number | null;
}> {
  return proxyRequest("GET", `/api/v1/jobs/${jobId}`, undefined, "generate");
}