/**
 * IndestructibleEco - Shared Type Definitions
 * Cross-platform type contracts for all services and platforms
 */

// ── UUID v1 Governance Types ───────────────────────────────
export interface DocumentMetadata {
  unique_id: string;
  schema_version: string;
  target_system: TargetSystem;
  cross_layer_binding: CrossLayerBinding;
  generated_by: string;
  created_at: string;
  updated_at: string;
}

export type TargetSystem = "kubernetes" | "docker-compose" | "helm" | "nomad" | "cloudflare" | "vercel";

export interface CrossLayerBinding {
  source_layer: LayerType;
  target_layer: LayerType;
  binding_type: "direct" | "event" | "query" | "stream";
  protocol: "rest" | "grpc" | "graphql" | "kafka" | "redis-stream";
}

export type LayerType = "input" | "process" | "core" | "governance" | "output" | "validate";

// ── Governance Info ────────────────────────────────────────
export interface GovernanceInfo {
  owner: string;
  approval_chain: string[];
  compliance_tags: string[];
  lifecycle_policy: LifecyclePolicy;
}

export type LifecyclePolicy = "active" | "deprecated" | "sunset" | "archived";

// ── Registry Binding ───────────────────────────────────────
export interface RegistryBinding {
  service_endpoint: string;
  discovery_protocol: "consul" | "eureka" | "etcd" | "kubernetes";
  health_check_path: string;
  registry_ttl: number;
  contextual_binding: Record<string, string>;
}

// ── Vector Alignment Map ───────────────────────────────────
export interface VectorAlignmentMap {
  coherence_vector: number[];
  function_keyword: string[];
  contextual_binding: Record<string, number>;
  model: string;
  dimensions: number;
  tolerance: number;
}

// ── Code Folding Engine Types ──────────────────────────────
export interface FoldingRequest {
  content: string;
  content_type: "source_code" | "document" | "config" | "log";
  language?: string;
  strategy: FoldingStrategy;
  target_dimensions?: number;
}

export type FoldingStrategy = "vector" | "graph" | "hybrid";

export interface FoldingResult {
  id: string;
  vector?: number[];
  graph?: GraphNode[];
  metadata: Record<string, unknown>;
  folding_time_ms: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, unknown>;
  edges: GraphEdge[];
}

export interface GraphEdge {
  target: string;
  relation: string;
  weight: number;
}

// ── Compute Engine Types ───────────────────────────────────
export interface SimilarityRequest {
  query_vector: number[];
  top_k: number;
  metric: "cosine" | "euclidean" | "dot_product";
  threshold?: number;
  filters?: Record<string, unknown>;
}

export interface SimilarityResult {
  id: string;
  score: number;
  metadata: Record<string, unknown>;
}

export interface ClusterRequest {
  vectors: number[][];
  algorithm: "kmeans" | "dbscan" | "hierarchical";
  params: Record<string, number>;
}

export interface ClusterResult {
  cluster_id: number;
  members: string[];
  centroid?: number[];
  density?: number;
}

export interface InferenceQuery {
  start_node: string;
  relation_path: string[];
  max_depth: number;
  reasoning_type: "deductive" | "inductive" | "abductive";
}

export interface InferenceResult {
  path: GraphNode[];
  confidence: number;
  explanation: string;
}

export interface RankingRequest {
  query: string;
  candidates: RankCandidate[];
  strategy: "bm25" | "vector" | "hybrid";
}

export interface RankCandidate {
  id: string;
  text: string;
  vector?: number[];
  metadata?: Record<string, unknown>;
}

export interface RankResult {
  id: string;
  score: number;
  rank: number;
}

// ── Index Engine Types ─────────────────────────────────────
export type IndexType = "faiss" | "neo4j" | "elasticsearch" | "hybrid";

export interface IndexEntry {
  id: string;
  vector?: number[];
  text?: string;
  graph_data?: GraphNode;
  metadata: Record<string, unknown>;
}

export interface IndexQuery {
  index_type: IndexType;
  query_vector?: number[];
  query_text?: string;
  graph_query?: string;
  top_k: number;
  filters?: Record<string, unknown>;
}

export interface IndexResult {
  entries: IndexEntry[];
  total_count: number;
  query_time_ms: number;
  index_type: IndexType;
}

// ── Service Engine Types ───────────────────────────────────
export interface ServiceHealth {
  service: string;
  status: "healthy" | "degraded" | "unhealthy";
  uptime_seconds: number;
  version: string;
  checks: HealthCheck[];
}

export interface HealthCheck {
  name: string;
  status: "pass" | "fail" | "warn";
  latency_ms: number;
  message?: string;
}

// ── Skill System Types ─────────────────────────────────────
export interface SkillDefinition {
  id: string;
  name: string;
  version: string;
  description: string;
  category: SkillCategory;
  triggers: SkillTrigger[];
  actions: SkillAction[];
  inputs: SkillParam[];
  outputs: SkillParam[];
  governance: GovernanceInfo;
  metadata: DocumentMetadata;
}

export type SkillCategory =
  | "ci-cd-repair"
  | "code-generation"
  | "code-analysis"
  | "deployment"
  | "monitoring"
  | "security"
  | "testing";

export interface SkillTrigger {
  type: "webhook" | "schedule" | "event" | "manual";
  config: Record<string, unknown>;
}

export interface SkillAction {
  id: string;
  name: string;
  type: "shell" | "api" | "transform" | "validate" | "deploy";
  config: Record<string, unknown>;
  depends_on?: string[];
  retry?: { max_attempts: number; backoff_ms: number };
}

export interface SkillParam {
  name: string;
  type: "string" | "number" | "boolean" | "object" | "array";
  required: boolean;
  default?: unknown;
  description: string;
}

// ── QYAML Template Types ───────────────────────────────────
export interface QYAMLTemplate {
  template_id: string;
  target_system: TargetSystem;
  variables: Record<string, QYAMLVariable>;
  body: string;
  schema_ref: string;
}

export interface QYAMLVariable {
  name: string;
  type: "string" | "number" | "boolean" | "list" | "map";
  default?: unknown;
  required: boolean;
  description: string;
}