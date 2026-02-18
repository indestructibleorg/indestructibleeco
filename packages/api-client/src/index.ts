/**
 * @indestructibleeco/api-client
 *
 * Auto-generated typed HTTP + WebSocket client SDK.
 * Transport: fetch (HTTP) + socket.io-client (WS)
 * Auth: JWT Bearer token injected via interceptor; auto-refresh on 401.
 */

import { io, Socket } from "socket.io-client";
import type {
  AuthResponse,
  LoginRequest,
  SignupRequest,
  AuthTokens,
  Platform,
  CreatePlatformRequest,
  UpdatePlatformRequest,
  GenerateRequest,
  GenerateResponse,
  AIJob,
  ModelInfo,
  VectorAlignRequest,
  VectorAlignResponse,
  GenerateQYAMLRequest,
  ValidateQYAMLRequest,
  ValidateQYAMLResponse,
  ServiceRegistration,
  HealthResponse,
  QYAMLGovernanceBlock,
  PlatformStatusEvent,
  AIJobProgressEvent,
  AIJobCompleteEvent,
  YAMLGeneratedEvent,
  IMMessageEvent,
} from "@indestructibleeco/shared-types";

export interface ClientConfig {
  baseUrl: string;
  wsPath?: string;
  onTokenRefresh?: (tokens: AuthTokens) => void;
  onUnauthorized?: () => void;
}

export class IndestructibleEcoClient {
  private baseUrl: string;
  private accessToken: string = "";
  private refreshToken: string = "";
  private socket: Socket | null = null;
  private config: ClientConfig;

  constructor(config: ClientConfig) {
    this.config = config;
    this.baseUrl = config.baseUrl.replace(/\/$/, "");
  }

  // ─── Token Management ───

  setTokens(access: string, refresh: string): void {
    this.accessToken = access;
    this.refreshToken = refresh;
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    retry = true
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`;
    }

    const res = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (res.status === 401 && retry && this.refreshToken) {
      const refreshed = await this.authRefresh(this.refreshToken);
      if (refreshed) {
        return this.request<T>(method, path, body, false);
      }
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: "unknown", message: res.statusText }));
      throw new ApiError(res.status, err.error, err.message);
    }

    return res.json();
  }

  // ─── Auth ───

  async authSignup(req: SignupRequest): Promise<AuthResponse> {
    const data = await this.request<AuthResponse>("POST", "/auth/signup", req);
    this.setTokens(data.accessToken, data.refreshToken);
    return data;
  }

  async authLogin(req: LoginRequest): Promise<AuthResponse> {
    const data = await this.request<AuthResponse>("POST", "/auth/login", req);
    this.setTokens(data.accessToken, data.refreshToken);
    return data;
  }

  async authRefresh(token: string): Promise<AuthTokens | null> {
    try {
      const data = await this.request<AuthTokens>("POST", "/auth/refresh", { refreshToken: token }, false);
      this.setTokens(data.accessToken, data.refreshToken);
      this.config.onTokenRefresh?.(data);
      return data;
    } catch {
      this.config.onUnauthorized?.();
      return null;
    }
  }

  async authLogout(): Promise<void> {
    await this.request<void>("POST", "/auth/logout");
    this.accessToken = "";
    this.refreshToken = "";
  }

  async authMe(): Promise<{ user: AuthResponse["user"] }> {
    return this.request("GET", "/auth/me");
  }

  // ─── Platforms ───

  async listPlatforms(): Promise<{ platforms: Platform[]; total: number }> {
    return this.request("GET", "/api/v1/platforms");
  }

  async createPlatform(req: CreatePlatformRequest): Promise<{ platform: Platform }> {
    return this.request("POST", "/api/v1/platforms", req);
  }

  async getPlatform(id: string): Promise<{ platform: Platform }> {
    return this.request("GET", `/api/v1/platforms/${id}`);
  }

  async updatePlatform(id: string, req: UpdatePlatformRequest): Promise<{ platform: Platform }> {
    return this.request("PATCH", `/api/v1/platforms/${id}`, req);
  }

  async deletePlatform(id: string): Promise<{ message: string; id: string; urn: string }> {
    return this.request("DELETE", `/api/v1/platforms/${id}`);
  }

  // ─── YAML Governance ───

  async yamlGenerate(req: GenerateQYAMLRequest): Promise<{ qyaml_content: string; qyaml_uri: string; unique_id: string; valid: boolean; governance: QYAMLGovernanceBlock }> {
    return this.request("POST", "/api/v1/yaml/generate", req);
  }

  async yamlValidate(req: ValidateQYAMLRequest): Promise<ValidateQYAMLResponse> {
    return this.request("POST", "/api/v1/yaml/validate", req);
  }

  async yamlRegistry(): Promise<{ services: ServiceRegistration[]; total: number }> {
    return this.request("GET", "/api/v1/yaml/registry");
  }

  async yamlVector(id: string): Promise<{ serviceId: string; uri: string; urn: string; vector_alignment: unknown }> {
    return this.request("GET", `/api/v1/yaml/vector/${id}`);
  }

  // ─── AI ───

  async aiGenerate(req: GenerateRequest): Promise<{ jobId: string; status: string; uri: string; urn: string; pollUrl: string }> {
    return this.request("POST", "/api/v1/ai/generate", req);
  }

  async aiJobStatus(jobId: string): Promise<AIJob> {
    return this.request("GET", `/api/v1/ai/jobs/${jobId}`);
  }

  async aiVectorAlign(req: VectorAlignRequest): Promise<VectorAlignResponse> {
    return this.request("POST", "/api/v1/ai/vector/align", req);
  }

  async aiModels(): Promise<{ models: ModelInfo[]; total: number }> {
    return this.request("GET", "/api/v1/ai/models");
  }

  // ─── Health ───

  async health(): Promise<HealthResponse> {
    return this.request("GET", "/health");
  }

  async ready(): Promise<HealthResponse> {
    return this.request("GET", "/ready");
  }

  // ─── WebSocket ───

  connectWS(): Socket {
    if (this.socket?.connected) return this.socket;

    this.socket = io(this.baseUrl, {
      path: this.config.wsPath || "/ws",
      auth: { token: this.accessToken },
      transports: ["websocket", "polling"],
    });

    return this.socket;
  }

  disconnectWS(): void {
    this.socket?.disconnect();
    this.socket = null;
  }

  onPlatformStatus(cb: (event: PlatformStatusEvent) => void): void {
    this.socket?.on("platform:status", cb);
  }

  onAIJobProgress(cb: (event: AIJobProgressEvent) => void): void {
    this.socket?.on("ai:job:progress", cb);
  }

  onAIJobComplete(cb: (event: AIJobCompleteEvent) => void): void {
    this.socket?.on("ai:job:complete", cb);
  }

  onYAMLGenerated(cb: (event: YAMLGeneratedEvent) => void): void {
    this.socket?.on("yaml:generated", cb);
  }

  onIMMessage(cb: (event: IMMessageEvent) => void): void {
    this.socket?.on("im:message:in", cb);
  }

  emitPlatformRegister(platformId: string, capabilities: string[]): void {
    this.socket?.emit("platform:register", { platformId, capabilities });
  }
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export default IndestructibleEcoClient;