/**
 * @ECO-governed
 * @ECO-layer: instant
 * @ECO-semantic: data-synchronization-entry-point
 * @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
 *
 * GL Unified Charter Activated
 * Data Synchronization Service Entry Point
 * 
 * Main entry point for the data synchronization service
 * Integrates with agent-orchestration.yml and file-organizer-system
 */

export * from './data-sync-service';
export * from './data-sync-engine';

// Re-export types for convenience
export type {
  SyncConfig,
  SyncRecord,
  ChangeTracking,
  SyncStatus,
  ValidationRule,
  DataSyncService
} from './data-sync-service';

export type {
  PipelineConfig,
  Transformation,
  SyncJob,
  EngineMetrics,
  DataSyncEngine
} from './data-sync-engine';

// Version information
export const VERSION = '1.0.0';
export const BUILD_DATE = new Date().toISOString();
export const GOVERNANCE_LAYER = 'GL90-99';
export const CHARTER_VERSION = '2.0.0';