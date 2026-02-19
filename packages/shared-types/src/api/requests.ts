import type { ModuleDescriptor } from "../entities/yaml";

export interface LoginRequest { email: string; password: string }
export interface SignupRequest { email: string; password: string; name?: string }
export interface RefreshRequest { refresh_token: string }
export interface YamlGenRequest { module: ModuleDescriptor; target: "k8s" | "docker" | "helm" | "nomad" }
export interface YamlValidateRequest { content: string }
export interface AiGenRequest { prompt: string; model_id?: string; max_tokens?: number; temperature?: number; top_p?: number }
export interface ChatCompletionRequest { model?: string; messages: { role: string; content: string }[]; temperature?: number; max_tokens?: number; stream?: boolean }
export interface PlatformCreateRequest { name: string; type: "web" | "desktop" | "im" | "extension" | "custom"; config?: Record<string, unknown> }
export interface PlatformUpdateRequest { name?: string; status?: string; config?: Record<string, unknown> }
export interface VectorAlignRequest { tokens: string[]; target_dim?: number; alignment_model?: string; tolerance?: number }
