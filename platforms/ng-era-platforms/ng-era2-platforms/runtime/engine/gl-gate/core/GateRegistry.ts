/**
 * @ECO-governed
 * @ECO-layer: governance
 * @ECO-semantic: gate-registry
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Gate Registry
 * Registers and manages all governance gates
 */

import { BaseGate } from '../gates/BaseGate';
import { TestingGate } from '../gates/TestingGate';
import { SecurityGate } from '../gates/SecurityGate';
import { PerformanceGate } from '../gates/PerformanceGate';
import { IntegrationGate } from '../gates/IntegrationGate';
import { ObservabilityGate } from '../gates/ObservabilityGate';
import { DataAccessGate } from '../gates/DataAccessGate';
import { GovernanceSummaryGate } from '../gates/GovernanceSummaryGate';
import { FinalSealGate } from '../gates/FinalSealGate';
import { StressTestingGate } from '../gates/StressTestingGate';

export class GateRegistry {
  private gates: Map<string, BaseGate> = new Map();

  constructor(private workspace: string = process.cwd()) {
    this.registerDefaultGates();
  }

  private registerDefaultGates(): void {
    this.register(new TestingGate(this.workspace));
    this.register(new SecurityGate(this.workspace));
    this.register(new PerformanceGate(this.workspace));
    this.register(new IntegrationGate(this.workspace));
    this.register(new ObservabilityGate(this.workspace));
    this.register(new DataAccessGate(this.workspace));
    this.register(new GovernanceSummaryGate(this.workspace));
    this.register(new FinalSealGate(this.workspace));
    this.register(new StressTestingGate(this.workspace));
  }

  register(gate: BaseGate): void {
    this.gates.set(gate.name, gate);
  }

  unregister(gateName: string): void {
    this.gates.delete(gateName);
  }

  getGate(gateName: string): BaseGate | undefined {
    return this.gates.get(gateName);
  }

  getAllGates(): BaseGate[] {
    return Array.from(this.gates.values());
  }

  getGateNames(): string[] {
    return Array.from(this.gates.keys());
  }

  hasGate(gateName: string): boolean {
    return this.gates.has(gateName);
  }
}