export interface AiJob {
  id: string;
  user_id: string;
  status: "pending" | "running" | "completed" | "failed";
  prompt: string;
  model_id: string;
  engine: string | null;
  result: string | null;
  error: string | null;
  usage: AiUsage | null;
  model_params: AiModelParams;
  latency_ms: number | null;
  createdAt: string;
  completedAt: string | null;
}

export interface AiUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface AiModelParams {
  temperature: number;
  top_p: number;
  max_tokens: number;
  stream: boolean;
}

export interface AiModel {
  id: string;
  name: string;
  provider: string;
  status: "available" | "registered" | "loading" | "error";
  capabilities: string[];
  uri: string;
  urn: string;
}
