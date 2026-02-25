/**
 * @ECO-governed
 * @ECO-layer: aep-engine-web
 * @ECO-semantic: data-mock
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

export const mockAuditSummary = {
  totalDetections: 24,
  passedChecks: 16,
  failedChecks: 8,
  passRate: 67,
  timestamp: new Date().toISOString(),
};

export const mockRecentEvents = [
  {
    id: '1',
    type: 'Execution',
    time: '2 min ago',
    status: 'success' as const,
  },
  {
    id: '2',
    type: 'Detection',
    time: '5 min ago',
    status: 'warning' as const,
  },
  {
    id: '3',
    type: 'Rollback',
    time: '10 min ago',
    status: 'info' as const,
  },
];

export const mockProblems = [
  {
    id: '1',
    type: 'Schema Mismatch',
    severity: 'critical' as const,
    description: "Field 'timestamp' type mismatch: expected datetime, got string",
    location: 'etl_pipeline.py:45',
    suggestion: 'Convert timestamp field to ISO 8601 format',
  },
  {
    id: '2',
    type: 'Metadata Missing',
    severity: 'high' as const,
    description: 'Missing required metadata: owner, created_at',
    location: 'schema_validator.py:12',
    suggestion: 'Add missing metadata fields to schema definition',
  },
  {
    id: '3',
    type: 'Naming Inconsistency',
    severity: 'medium' as const,
    description: 'File naming does not follow snake_case convention',
    location: 'naming_validator.py:8',
    suggestion: 'Rename file to follow naming convention',
  },
  {
    id: '4',
    type: 'Directory Structure',
    severity: 'medium' as const,
    description: 'Directory structure does not match best practices',
    location: './workspace',
    suggestion: 'Reorganize directory structure according to template',
  },
  {
    id: '5',
    type: 'GL Marker Missing',
    severity: 'low' as const,
    description: 'Missing GL Root Semantic Anchor tag',
    location: 'metadata_checker.py:20',
    suggestion: 'Add GL layer marker to file header',
  },
];

export const mockSeverityDistribution = [
  { severity: 'Critical', count: 1, percentage: 12.5 },
  { severity: 'High', count: 2, percentage: 25 },
  { severity: 'Medium', count: 3, percentage: 37.5 },
  { severity: 'Low', count: 2, percentage: 25 },
];

export const mockProblemTypes = [
  { type: 'Schema Mismatch', count: 3 },
  { type: 'Metadata Missing', count: 2 },
  { type: 'Naming Inconsistency', count: 1 },
  { type: 'Directory Structure', count: 1 },
  { type: 'GL Marker Missing', count: 1 },
];

export const mockRecommendations = [
  {
    id: '1',
    title: 'Fix Schema Validation',
    description: 'Update timestamp field to ISO 8601 format across all ETL scripts',
    impact: 'High',
  },
  {
    id: '2',
    title: 'Add Missing Metadata',
    description: 'Add owner and created_at fields to all schema definitions',
    impact: 'High',
  },
  {
    id: '3',
    title: 'Standardize Naming',
    description: 'Rename files to follow snake_case convention',
    impact: 'Medium',
  },
  {
    id: '4',
    title: 'Reorganize Directory',
    description: 'Migrate to recommended directory structure with etl/, es/, schemas/ folders',
    impact: 'Medium',
  },
];

export const mockETLStages = [
  { name: 'Extract', progress: 100, status: 'completed' as const },
  { name: 'Transform', progress: 65, status: 'running' as const },
  { name: 'Load', progress: 0, status: 'pending' as const },
];

export const mockFiles = [
  { id: '1', name: 'etl_pipeline.py', status: 'completed' as const, time: '2.3s' },
  { id: '2', name: 'schema_validator.py', status: 'running' as const, time: '1.2s' },
  { id: '3', name: 'metadata_checker.py', status: 'pending' as const, time: '-' },
  { id: '4', name: 'naming_validator.py', status: 'pending' as const, time: '-' },
];

export const mockLogs = [
  '[INFO] Starting ETL Pipeline execution',
  '[INFO] Initializing sandbox: sandbox-2026-01-26-001',
  '[INFO] Extracting data from source...',
  '[SUCCESS] Data extraction completed (1,234 records)',
  '[INFO] Starting transformation phase...',
  '[INFO] Applying schema validation...',
  '[WARNING] Found 2 schema mismatches in field "timestamp"',
];
