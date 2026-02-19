import type { User } from "../entities/user";
import type { Platform } from "../entities/platform";
import type { AiJob, AiModel, AiUsage } from "../entities/ai";

export interface LoginResponse { access_token: string; refresh_token: string; expires_in: number; user: User }
export interface SignupResponse { access_token: string; refresh_token: string; user: User }
export interface RefreshResponse { access_token: string; expires_in: number }
export interface YamlGenResponse { qyaml_content: string; valid: boolean; warnings: string[] }
export interface YamlValidateResponse { valid: boolean; missing_blocks: string[] }
export interface AiGenResponse { request_id: string; content: string; model_id: string; engine: string; usage: AiUsage; finish_reason: string; latency_ms: number }
export interface ChatCompletionResponse { id: string; object: string; model: string; choices: { index: number; message: { role: string; content: string }; finish_reason: string }[]; usage: AiUsage }
export interface ModelsResponse { models: AiModel[] }
export interface HealthResponse { status: string; service: string; version: string; engines?: string[]; uptime_seconds: number }
export interface PlatformListResponse { platforms: Platform[] }
export interface PlatformResponse { platform: Platform }
export interface VectorAlignResponse { coherence_vector: number[]; dimension: number; alignment_model: string; alignment_score: number; function_keywords: string[] }
