export function createApiClient(options: { baseUrl: string; getToken?: () => Promise<string | null> }) {
  const { baseUrl, getToken } = options;
  async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const token = await getToken?.();
    const res = await fetch(`${baseUrl}${path}`, {
      method,
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
    return res.json() as Promise<T>;
  }
  return {
    auth: { login: (body: { email: string; password: string }) => request("POST", "/auth/login", body), me: () => request("GET", "/auth/me"), logout: () => request("POST", "/auth/logout") },
    yaml: { generate: (moduleJson: unknown) => request("POST", "/api/v1/yaml/generate", moduleJson), validate: (content: string) => request("POST", "/api/v1/yaml/validate", { content }) },
    ai: { generate: (prompt: string, modelId?: string) => request("POST", "/api/v1/ai/generate", { prompt, model_id: modelId }), getJob: (jobId: string) => request("GET", `/api/v1/ai/jobs/${jobId}`) },
  };
}
