const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:3000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = JSON.parse(localStorage.getItem("eco-auth") || "{}")?.state?.token;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string> || {}),
  };
  const resp = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: resp.statusText }));
    throw new Error(err.error || err.message || `HTTP ${resp.status}`);
  }
  return resp.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),

  // Auth
  login: (email: string, password: string) =>
    api.post<{ access_token: string; refresh_token: string; user: unknown }>("/auth/login", { email, password }),
  signup: (email: string, password: string) =>
    api.post<{ access_token: string; refresh_token: string; user: unknown }>("/auth/signup", { email, password }),
  refresh: (refreshToken: string) =>
    api.post<{ access_token: string }>("/auth/refresh", { refresh_token: refreshToken }),
  me: () => api.get<{ user: unknown }>("/auth/me"),

  // AI
  generate: (prompt: string, modelId = "default", maxTokens = 2048) =>
    api.post<{ request_id: string; content: string; engine: string; usage: unknown; latency_ms: number }>(
      "/api/v1/ai/generate", { prompt, model_id: modelId, max_tokens: maxTokens }
    ),
  models: () => api.get<unknown[]>("/api/v1/ai/models"),

  // Health
  health: () => api.get<{ status: string; engines?: string[] }>("/health"),

  // Platforms
  platforms: () => api.get<{ platforms: unknown[] }>("/api/v1/platforms"),
};
