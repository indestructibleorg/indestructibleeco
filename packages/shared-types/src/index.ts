/**
 * @indestructibleeco/shared-types
 *
 * Single source of truth for TypeScript interfaces and enums.
 * Type-only (no runtime code) — zero bundle cost.
 * UUID v1 policy: all identifiers are time-based UUIDs.
 * URI/URN policy: all resources carry dual identification.
 */

// ─── Core Identifiers ───

export interface ResourceIdentifier {
  id: string;          // UUID v1
  uri: string;         // indestructibleeco://{domain}/{kind}/{name}
  urn: string;         // urn:indestructibleeco:{domain}:{kind}:{name}:{uuid}
}

// ─── Auth ───

export type UserRole = "admin" | "member" | "viewer";

export interface User extends ResourceIdentifier {
  email: string;
  role: UserRole;
  createdAt: string;
  updatedAt: string;
  metadata: Record<string, unknown>;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

// ─── Platform ───

export type PlatformStatus = "active" | "inactive" | "deploying" | "error" | "maintenance";

export interface Platform extends ResourceIdentifier {
  name: string;
  slug: string;
  status: PlatformStatus;
  config: Record<string, unknown>;
  capabilities: string[];
  k8sNamespace: string;
  deployTarget: string;
  ownerId: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreatePlatformRequest {
  name: string;
  slug: string;
  config?: Record<string, unknown>;
  capabilities?: string[];
  deployTarget?: string;
}

export interface UpdatePlatformRequest {
  name?: string;
  status?: PlatformStatus;
  config?: Record<string, unknown>;
  capabilities?: string[];
  deployTarget?: string;
}

// ─── AI ───

export type JobStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

export interface AIJob extends ResourceIdentifier {
  userId: string;
  modelId: string;
  prompt: string;
  status: JobStatus;
  result: string | null;
  error: string | null;
  progress: number;
  params: Record<string, unknown>;
  usage: TokenUsage | null;
  createdAt: string;
  completedAt: string | null;
}

export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}

export interface GenerateRequest {
  prompt: string;
  model_id?: string;
  params?: Record<string, unknown>;
  max_tokens?: number;
  temperature?: number;
  top_p?: number;
}

export interface GenerateResponse {
  requestId: string;
  content: string;
  modelId: string;
  uri: string;
  urn: string;
  usage: TokenUsage;
  finishReason: string;
  createdAt: string;
}

export interface ModelInfo extends ResourceIdentifier {
  name: string;
  provider: string;
  status: string;
  capabilities: string[];
}

// ─── Vector Alignment ───

export interface VectorAlignRequest {
  tokens: string[];
  target_dim?: number;
  alignment_model?: string;
  tolerance?: number;
}

export interface VectorAlignResponse {
  coherenceVector: number[];
  dimension: number;
  alignmentModel: string;
  alignmentScore: number;
  functionKeywords: string[];
  uri: string;
  urn: string;
}

// ─── YAML Governance ───

export interface QYAMLDocumentMetadata {
  unique_id: string;
  uri: string;
  urn: string;
  target_system: string;
  cross_layer_binding: string[];
  schema_version: string;
  generated_by: string;
  created_at: string;
}

export interface QYAMLGovernanceInfo {
  owner: string;
  approval_chain: string[];
  compliance_tags: string[];
  lifecycle_policy: "active" | "deprecated" | "archived";
}

export interface QYAMLRegistryBinding {
  service_endpoint: string;
  discovery_protocol: "consul" | "etcd" | "k8s-dns";
  health_check_path: string;
  registry_ttl: number;
}

export interface QYAMLVectorAlignment {
  alignment_model: string;
  coherence_vector_dim: number;
  function_keyword: string[];
  contextual_binding: string;
}

export interface QYAMLGovernanceBlock {
  document_metadata: QYAMLDocumentMetadata;
  governance_info: QYAMLGovernanceInfo;
  registry_binding: QYAMLRegistryBinding;
  vector_alignment_map: QYAMLVectorAlignment;
}

export interface GenerateQYAMLRequest {
  name: string;
  image?: string;
  replicas?: number;
  ports?: number[];
  depends_on?: string[];
  target_system?: string;
  kind?: string;
}

export interface ValidateQYAMLRequest {
  qyaml_content: string;
}

export interface ValidateQYAMLResponse {
  valid: boolean;
  errors: Array<{ path: string; message: string; severity: string }>;
}

// ─── Service Registry ───

export type ServiceHealth = "healthy" | "degraded" | "unhealthy" | "unknown";

export interface ServiceRegistration extends ResourceIdentifier {
  serviceName: string;
  endpoint: string;
  discoveryProtocol: string;
  healthCheckPath: string;
  health: ServiceHealth;
  registryTtl: number;
  registeredAt: string;
  lastHeartbeat: string | null;
}

// ─── WebSocket Events ───

export interface PlatformStatusEvent {
  platformId: string;
  status: string;
  timestamp: string;
}

export interface AIJobProgressEvent {
  jobId: string;
  progress: number;
  partial_result: string | null;
}

export interface AIJobCompleteEvent {
  jobId: string;
  result: string;
  qyaml_uri: string | null;
}

export interface YAMLGeneratedEvent {
  serviceId: string;
  qyaml_content: string;
  valid: boolean;
}

export interface IMMessageEvent {
  channel: string;
  userId: string;
  text: string;
  intent: string;
}

export interface PlatformRegisterEvent {
  platformId: string;
  capabilities: string[];
}

// ─── Health ───

export interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  service: string;
  version: string;
  uri: string;
  timestamp: string;
  components?: Record<string, { status: string; latencyMs?: number; message?: string }>;
}