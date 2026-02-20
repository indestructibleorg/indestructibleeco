/**
 * Shared TypeScript types for API service.
 * URI: indestructibleeco://backend/api/src/types
 */

export interface ServiceHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  uptime_seconds: number;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export interface ErrorResponse {
  error: string;
  code: string;
  details?: Record<string, unknown>;
  request_id?: string;
}

export interface JobStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  result?: unknown;
  error?: string;
  created_at: string;
  updated_at?: string;
  latency_ms?: number;
}

export interface AIGenerateRequest {
  prompt: string;
  model?: string;
  max_tokens?: number;
  temperature?: number;
  stream?: boolean;
}

export interface AIGenerateResponse {
  job_id: string;
  status: string;
  model: string;
  result?: string;
}

export interface YAMLGenerateRequest {
  name: string;
  namespace?: string;
  kind?: string;
  image?: string;
  replicas?: number;
  ports?: number[];
}

export interface YAMLValidateRequest {
  content: string;
  strict?: boolean;
}

export interface YAMLValidateResponse {
  valid: boolean;
  errors: Array<{
    path: string;
    message: string;
    severity: 'error' | 'warning';
  }>;
}
