/**
 * @ECO-governed
 * @ECO-layer: governance
 * @ECO-semantic: base-gate
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Base Gate
 * Base class for all governance gates
 */

export interface GateResult {
  passed: boolean;
  errors: string[];
  warnings: string[];
  metrics: {
    checksPerformed: number;
    checksPassed: number;
    checksFailed: number;
  };
}

export interface GateConfig {
  enabled: boolean;
  blocking: boolean;
  severity: 'critical' | 'high' | 'medium' | 'low';
}

export abstract class BaseGate {
  public abstract readonly name: string;
  public abstract readonly description: string;

  protected config: GateConfig;

  constructor(
    protected workspace: string,
    config?: Partial<GateConfig>
  ) {
    this.config = {
      enabled: true,
      blocking: true,
      severity: 'high',
      ...config
    };
  }

  abstract execute(): Promise<GateResult>;

  protected createResult(
    passed: boolean,
    errors: string[] = [],
    warnings: string[] = [],
    checksPassed: number = 0,
    checksFailed: number = 0
  ): GateResult {
    return {
      passed,
      errors,
      warnings,
      metrics: {
        checksPerformed: checksPassed + checksFailed,
        checksPassed,
        checksFailed
      }
    };
  }

  isEnabled(): boolean {
    return this.config.enabled;
  }

  isBlocking(): boolean {
    return this.config.blocking;
  }

  getSeverity(): string {
    return this.config.severity;
  }

  async executeIfEnabled(): Promise<GateResult> {
    if (!this.isEnabled()) {
      return this.createResult(
        true,
        [],
        [`Gate ${this.name} is disabled, skipping`],
        0,
        0
      );
    }

    return this.execute();
  }
}