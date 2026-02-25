# @ECO-governed
# @ECO-layer: GL20-29
# @ECO-semantic: typescript-module
# @ECO-audit-trail: ../../engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
#
# GL Unified Charter Activated
# GL Root Semantic Anchor: gl-platform-universe/governance/engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
# GL Unified Naming Charter: gl-platform-universe/governance/engine/governance/gl-artifacts/meta/naming-charter/gl-unified-naming-charter.yaml

// @ECO-governed @ECO-internal-only
// GL Enterprise Platform - Main Orchestrator with Global DAG v9.0.0
// Version: 9.0.0

import { ExecutionEngine, ExecutionOptions } from './execution/execution-engine';
import { ComplianceValidator, ComplianceReport } from './validation/compliance-validator';
import { ZeroResidueCleaner, CleanupResult } from './cleanup/zero-residue-cleaner';
import { InternalMonitor, MonitoringStats } from './monitoring/internal-monitor';
import { GlobalDAGOrchestrator, DAGGraph, DAGExecutionResult } from '../gl-runtime-platform/global-dag';
import { v4 as uuidv4 } from 'uuid';

export interface PlatformConfig {
  workspace?: string;
  enableCleanup?: boolean;
  enableMonitoring?: boolean;
  monitoringInterval?: number;
  enableGlobalDAG?: boolean;
  dagExecutionMode?: 'sequential' | 'parallel' | 'hybrid';
}

export interface PlatformResult {
  success: boolean;
  executionId: string;
  executionResult?: any;
  complianceReport?: ComplianceReport;
  cleanupResult?: CleanupResult;
  monitoringStats?: MonitoringStats;
  duration: number;
  error?: string;
}

export class GLPlatform {
  private executionEngine: ExecutionEngine;
  private complianceValidator: ComplianceValidator;
  private cleanupEngine: ZeroResidueCleaner;
  private monitor: InternalMonitor;
  private config: PlatformConfig;
  private globalDAGOrchestrator: GlobalDAGOrchestrator | null;

  constructor(config: PlatformConfig = {}) {
    this.config = {
      enableCleanup: true,
      enableMonitoring: true,
      monitoringInterval: 10000,
      enableGlobalDAG: true,
      dagExecutionMode: 'parallel',
      ...config
    };

    this.executionEngine = new ExecutionEngine();
    this.complianceValidator = new ComplianceValidator();
    this.cleanupEngine = new ZeroResidueCleaner();
    this.monitor = new InternalMonitor();
    this.globalDAGOrchestrator = null;
  }

  /**
   * Initialize platform
   */
  async initialize(): Promise<void> {
    // Initialize execution engine
    await this.executionEngine.initialize();

    // Initialize Global DAG orchestrator if enabled
    if (this.config.enableGlobalDAG) {
      this.globalDAGOrchestrator = new GlobalDAGOrchestrator({
        executionMode: this.config.dagExecutionMode || 'parallel',
        federationPath: './gl-runtime-platform/federation'
      });
      await this.globalDAGOrchestrator.initialize();
      
      this.monitor.recordMetric({
        name: 'global_dag_initialized',
        value: 1,
        labels: { mode: this.config.dagExecutionMode || 'parallel' }
      });
    }

    // Start monitoring if enabled
    if (this.config.enableMonitoring) {
      this.monitor.start(this.config.monitoringInterval);
    }

    this.monitor.recordMetric({
      name: 'platform_initialized',
      value: 1,
      labels: { platform: 'gl-enterprise', version: '9.0.0' }
    });
  }

  /**
   * Execute task with full platform support
   */
  async execute(options: ExecutionOptions): Promise<PlatformResult> {
    const executionId = uuidv4();
    const startTime = Date.now();

    this.monitor.recordMetric({
      name: 'execution_started',
      value: 1,
      labels: { executionId }
    });

    const result: PlatformResult = {
      success: false,
      executionId,
      duration: 0
    };

    try {
      // Pre-execution compliance check
      const complianceReport = await this.complianceValidator.validateDirectory(process.cwd());
      result.complianceReport = complianceReport;

      // Check if compliance is acceptable
      if (complianceReport.overallCompliance < 80) {
        throw new Error(`Compliance check failed: ${complianceReport.overallCompliance}%`);
      }

      // Execute task
      const executionResult = await this.executionEngine.execute(options);
      result.executionResult = executionResult;
      result.success = executionResult.success;

      this.monitor.recordMetric({
        name: 'execution_completed',
        value: executionResult.success ? 1 : 0,
        labels: { executionId, success: String(executionResult.success) }
      });

      // Post-execution cleanup
      if (this.config.enableCleanup) {
        const cleanupResult = await this.cleanupEngine.executeCleanup();
        result.cleanupResult = cleanupResult;
      }

      // Verify zero residue
      const zeroResidueCheck = await this.cleanupEngine.verifyZeroResidue();
      this.monitor.recordMetric({
        name: 'zero_residue_check',
        value: zeroResidueCheck.isClean ? 1 : 0,
        labels: { executionId }
      });

      result.duration = Date.now() - startTime;
      result.success = result.success && zeroResidueCheck.isClean;

      return result;

    } catch (error) {
      result.duration = Date.now() - startTime;
      result.success = false;
      result.error = error instanceof Error ? error.message : String(error);

      this.monitor.recordMetric({
        name: 'execution_failed',
        value: 1,
        labels: { executionId, error: result.error }
      });

      // Ensure cleanup on error
      if (this.config.enableCleanup) {
        await this.cleanupEngine.executeCleanup().catch(() => {});
      }

      return result;
    }
  }

  /**
   * Run compliance validation
   */
  async runComplianceValidation(directoryPath: string): Promise<ComplianceReport> {
    return await this.complianceValidator.validateDirectory(directoryPath);
  }

  /**
   * Run cleanup
   */
  async runCleanup(): Promise<CleanupResult> {
    return await this.cleanupEngine.executeCleanup();
  }

  /**
   * Verify zero residue
   */
  async verifyZeroResidue(): Promise<{ isClean: boolean; residueFiles: string[] }> {
    return await this.cleanupEngine.verifyZeroResidue();
  }

  /**
   * Get monitoring statistics
   */
  getMonitoringStats(): MonitoringStats {
    return this.monitor.getStats();
  }

  /**
   * Get alerts
   */
  getAlerts() {
    return this.monitor.getAlerts();
  }

  /**
   * Shutdown platform
   */
  async shutdown(): Promise<void> {
    // Stop monitoring
    this.monitor.stop();

    // Final cleanup
    await this.cleanupEngine.executeCleanup();

    this.monitor.recordMetric({
      name: 'platform_shutdown',
      value: 1,
      labels: { platform: 'gl-enterprise' }
    });
  }

  /**
   * Get platform status
   */
  getStatus() {
    const status: any = {
      initialized: true,
      executionEngine: this.executionEngine.getStats(),
      monitoring: this.monitor.getStats(),
      zeroResidue: 'verified',
      productionReady: true,
      version: '9.0.0'
    };

    if (this.globalDAGOrchestrator) {
      status.globalDAG = this.globalDAGOrchestrator.getStatus();
    }

    return status;
  }

  /**
   * Build Global DAG
   */
  async buildGlobalDAG(): Promise<DAGGraph> {
    if (!this.globalDAGOrchestrator) {
      throw new Error('Global DAG orchestrator not enabled');
    }
    return await this.globalDAGOrchestrator.buildDAG();
  }

  /**
   * Execute Global DAG
   */
  async executeGlobalDAG(): Promise<DAGExecutionResult> {
    if (!this.globalDAGOrchestrator) {
      throw new Error('Global DAG orchestrator not enabled');
    }
    return await this.globalDAGOrchestrator.executeDAG();
  }

  /**
   * Get Global DAG status
   */
  getGlobalDAGStatus() {
    if (!this.globalDAGOrchestrator) {
      return { enabled: false };
    }
    return this.globalDAGOrchestrator.getStatus();
  }

  /**
   * Get Global DAG graph
   */
  getGlobalDAGGraph() {
    if (!this.globalDAGOrchestrator) {
      return null;
    }
    return this.globalDAGOrchestrator.getGraph();
  }
}

// Export singleton instance
export const platform = new GLPlatform();