/**
 * @ECO-governed
 * @ECO-layer: gl-gate
 * @ECO-semantic: types-index
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

/**
 * @fileoverview ECO-Gate Type Definitions
 * @module @machine-native-ops/gl-gate/types
 * @version 1.0.0
 * @since 2026-01-26
 * @author MachineNativeOps
 * @gl-governed true
 * @gl-layer ECO-40-GOVERNANCE
 * 
 * GL Unified Charter Activated
 */

/**
 * Gate execution status
 */
export type GateStatus = 'pending' | 'running' | 'passed' | 'failed' | 'skipped' | 'warning';

/**
 * Gate severity level
 */
export type GateSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';

/**
 * Gate category classification
 */
export type GateCategory = 
  | 'performance'      // gl-gate:01
  | 'data-access'      // gl-gate:02
  | 'observability'    // gl-gate:06
  | 'security'         // gl-gate:07
  | 'integration'      // gl-gate:08
  | 'testing'          // gl-gate:11
  | 'stress-testing'   // gl-gate:15
  | 'governance'       // gl-gate:19
  | 'sealing';         // gl-gate:20

/**
 * Gate identifier following gl-gate:NN format
 */
export type GateId = 
  | 'gl-gate:01' | 'gl-gate:02' | 'gl-gate:06' | 'gl-gate:07' 
  | 'gl-gate:08' | 'gl-gate:11' | 'gl-gate:15' | 'gl-gate:19' | 'gl-gate:20';

/**
 * Gate definition interface
 * 治理閘門定義介面
 */
export interface GateDefinition {
  /** Gate identifier (gl-gate:NN format) */
  id: GateId;
  
  /** English name */
  nameEN: string;
  
  /** Chinese name */
  nameZH: string;
  
  /** Gate category */
  category: GateCategory;
  
  /** Description in English */
  descriptionEN: string;
  
  /** Description in Chinese */
  descriptionZH: string;
  
  /** Semantic boundary definition */
  semanticBoundary: string;
  
  /** Verification standards */
  verificationStandards: string[];
  
  /** Default severity */
  defaultSeverity: GateSeverity;
  
  /** Whether gate is enabled by default */
  enabledByDefault: boolean;
  
  /** Gate dependencies (other gate IDs) */
  dependencies?: GateId[];
  
  /** Gate version */
  version: string;
}

/**
 * Gate execution context
 * 閘門執行上下文
 */
export interface GateContext {
  /** Execution ID */
  executionId: string;
  
  /** Timestamp */
  timestamp: Date;
  
  /** Environment (dev/staging/production) */
  environment: 'development' | 'staging' | 'production';
  
  /** Target module or component */
  target: string;
  
  /** Additional metadata */
  metadata: Record<string, unknown>;
  
  /** Parent context (for nested gates) */
  parentContext?: GateContext;
}

/**
 * Gate execution result
 * 閘門執行結果
 */
export interface GateResult {
  /** Gate ID */
  gateId: GateId;
  
  /** Execution status */
  status: GateStatus;
  
  /** Execution duration in milliseconds */
  durationMs: number;
  
  /** Result message */
  message: string;
  
  /** Detailed findings */
  findings: GateFinding[];
  
  /** Metrics collected */
  metrics: GateMetric[];
  
  /** Evidence generated */
  evidence: GateEvidence[];
  
  /** Timestamp */
  timestamp: Date;
  
  /** Context used */
  context: GateContext;
}

/**
 * Gate finding (issue or observation)
 * 閘門發現（問題或觀察）
 */
export interface GateFinding {
  /** Finding ID */
  id: string;
  
  /** Finding type */
  type: 'violation' | 'warning' | 'info' | 'recommendation';
  
  /** Severity */
  severity: GateSeverity;
  
  /** Title */
  title: string;
  
  /** Description */
  description: string;
  
  /** Location (file, line, etc.) */
  location?: string;
  
  /** Remediation suggestion */
  remediation?: string;
  
  /** Related evidence */
  evidenceIds?: string[];
}

/**
 * Gate metric
 * 閘門指標
 */
export interface GateMetric {
  /** Metric name */
  name: string;
  
  /** Metric value */
  value: number;
  
  /** Unit of measurement */
  unit: string;
  
  /** Threshold (if applicable) */
  threshold?: number;
  
  /** Whether threshold was exceeded */
  thresholdExceeded?: boolean;
  
  /** Labels for metric categorization */
  labels: Record<string, string>;
}

/**
 * Gate evidence
 * 閘門證據
 */
export interface GateEvidence {
  /** Evidence ID */
  id: string;
  
  /** Evidence type */
  type: 'log' | 'artifact' | 'snapshot' | 'report' | 'signature';
  
  /** Evidence content or reference */
  content: string | Buffer;
  
  /** Content hash for integrity */
  hash: string;
  
  /** Timestamp */
  timestamp: Date;
  
  /** Whether evidence is immutable (sealed) */
  sealed: boolean;
  
  /** Signature (if sealed) */
  signature?: string;
}

/**
 * Gate configuration
 * 閘門配置
 */
export interface GateConfig {
  /** Gate ID */
  gateId: GateId;
  
  /** Whether gate is enabled */
  enabled: boolean;
  
  /** Severity override */
  severity?: GateSeverity;
  
  /** Custom thresholds */
  thresholds?: Record<string, number>;
  
  /** Custom rules */
  rules?: GateRule[];
  
  /** Timeout in milliseconds */
  timeoutMs?: number;
  
  /** Retry configuration */
  retry?: {
    maxAttempts: number;
    delayMs: number;
    backoffMultiplier: number;
  };
}

/**
 * Gate rule
 * 閘門規則
 */
export interface GateRule {
  /** Rule ID */
  id: string;
  
  /** Rule name */
  name: string;
  
  /** Rule condition (expression) */
  condition: string;
  
  /** Action on match */
  action: 'fail' | 'warn' | 'info' | 'skip';
  
  /** Message template */
  messageTemplate: string;
  
  /** Whether rule is enabled */
  enabled: boolean;
}

/**
 * Gate orchestration configuration
 * 閘門編排配置
 */
export interface GateOrchestration {
  /** Orchestration ID */
  id: string;
  
  /** Name */
  name: string;
  
  /** Gates to execute in order */
  gates: GateId[];
  
  /** Execution mode */
  mode: 'sequential' | 'parallel' | 'dag';
  
  /** Stop on first failure */
  stopOnFailure: boolean;
  
  /** Global timeout */
  timeoutMs: number;
  
  /** Notification configuration */
  notifications?: {
    onSuccess?: string[];
    onFailure?: string[];
    onWarning?: string[];
  };
}

/**
 * Gate execution summary
 * 閘門執行摘要
 */
export interface GateExecutionSummary {
  /** Orchestration ID */
  orchestrationId: string;
  
  /** Total gates executed */
  totalGates: number;
  
  /** Passed gates */
  passedGates: number;
  
  /** Failed gates */
  failedGates: number;
  
  /** Skipped gates */
  skippedGates: number;
  
  /** Warning gates */
  warningGates: number;
  
  /** Overall status */
  overallStatus: GateStatus;
  
  /** Total duration */
  totalDurationMs: number;
  
  /** Individual results */
  results: GateResult[];
  
  /** Start timestamp */
  startTime: Date;
  
  /** End timestamp */
  endTime: Date;
  
  /** Evidence chain hash */
  evidenceChainHash: string;
}

/**
 * Gate event for event streaming
 * 閘門事件（用於事件流）
 */
export interface GateEvent {
  /** Event ID */
  eventId: string;
  
  /** Event type */
  eventType: 'gate.started' | 'gate.completed' | 'gate.failed' | 'gate.skipped' | 'finding.created' | 'evidence.sealed';
  
  /** Gate ID */
  gateId: GateId;
  
  /** Timestamp */
  timestamp: Date;
  
  /** Event payload */
  payload: Record<string, unknown>;
  
  /** Correlation ID for tracing */
  correlationId: string;
}

// GL Unified Charter Activated