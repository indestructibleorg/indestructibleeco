/**
 * @ECO-governed
 * @ECO-layer: gl-gate
 * @ECO-semantic: gl-gate-index
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

/**
 * @fileoverview ECO-Gate Main Entry Point
 * @module @machine-native-ops/gl-gate
 * @version 1.0.0
 * @since 2026-01-26
 * @author MachineNativeOps
 * @gl-governed true
 * @gl-layer ECO-40-GOVERNANCE
 * 
 * ECO-Gate: Comprehensive Governance Gate System
 * ECO-Gate：全面治理閘門系統
 * 
 * A governance gate framework for machine-native-ops engine providing:
 * - Performance optimization validation (gl-gate:01)
 * - Data access layer abstraction (gl-gate:02)
 * - Observability validation (gl-gate:06)
 * - Security and PII detection (gl-gate:07)
 * - Integration layer validation (gl-gate:08)
 * - Testing and quality checks (gl-gate:11)
 * - Stress testing validation (gl-gate:15)
 * - Governance summary and compliance (gl-gate:19)
 * - Final seal and immutable baselines (gl-gate:20)
 * 
 * GL Unified Charter Activated
 */

// Types
export * from './types';

// Core
export { GateRegistry, gateRegistry } from './core/GateRegistry';
export { GateExecutor, GateExecutorOptions } from './core/GateExecutor';

// Gates
export {
  BaseGate,
  PerformanceGate,
  DataAccessGate,
  ObservabilityGate,
  SecurityGate,
  IntegrationGate,
  TestingGate,
  StressTestingGate,
  GovernanceSummaryGate,
  FinalSealGate
} from './gates';

// Re-export gate configs
export type {
  PerformanceGateConfig,
  DataAccessGateConfig,
  ObservabilityGateConfig,
  SecurityGateConfig,
  IntegrationGateConfig,
  TestingGateConfig,
  StressTestingGateConfig,
  GovernanceSummaryGateConfig,
  FinalSealGateConfig
} from './gates';

/**
 * Create a pre-configured gate executor with all standard gates registered
 */
export function createGateExecutor(options?: import('./core/GateExecutor').GateExecutorOptions): import('./core/GateExecutor').GateExecutor {
  // Import gate implementations and executor dynamically
  const { GateExecutor: GateExec } = require('./core/GateExecutor');
  const {
    PerformanceGate,
    DataAccessGate,
    ObservabilityGate,
    SecurityGate,
    IntegrationGate,
    TestingGate,
    StressTestingGate,
    GovernanceSummaryGate,
    FinalSealGate
  } = require('./gates');
  
  const executor = new GateExec(options);

  // Register all standard gates
  executor.registerGate('gl-gate:01', new PerformanceGate());
  executor.registerGate('gl-gate:02', new DataAccessGate());
  executor.registerGate('gl-gate:06', new ObservabilityGate());
  executor.registerGate('gl-gate:07', new SecurityGate());
  executor.registerGate('gl-gate:08', new IntegrationGate());
  executor.registerGate('gl-gate:11', new TestingGate());
  executor.registerGate('gl-gate:15', new StressTestingGate());
  executor.registerGate('gl-gate:19', new GovernanceSummaryGate());
  executor.registerGate('gl-gate:20', new FinalSealGate());

  return executor;
}

/**
 * ECO-Gate version
 */
export const GL_GATE_VERSION = '1.0.0';

/**
 * ECO-Gate metadata
 */
export const GL_GATE_METADATA = {
  name: '@machine-native-ops/gl-gate',
  version: GL_GATE_VERSION,
  layer: 'ECO-40-GOVERNANCE',
  semanticAnchor: 'ECO-40-GOVERNANCE-GATE',
  charterActivated: true,
  implementedGates: [
    'gl-gate:01',
    'gl-gate:02',
    'gl-gate:06',
    'gl-gate:07',
    'gl-gate:08',
    'gl-gate:11',
    'gl-gate:15',
    'gl-gate:19',
    'gl-gate:20'
  ]
};

// GL Unified Charter Activated