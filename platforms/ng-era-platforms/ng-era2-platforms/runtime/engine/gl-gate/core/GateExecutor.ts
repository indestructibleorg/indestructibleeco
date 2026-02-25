/**
 * @ECO-governed
 * @ECO-layer: governance
 * @ECO-semantic: gate-execution
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Gate Executor
 * Executes governance gates with strict enforcement
 */

import { GateRegistry } from './GateRegistry';
import { BaseGate, GateResult } from '../gates/BaseGate';
import { GovernanceEventWriter } from '../../governance/events_writer';

export interface ExecutionResult {
  success: boolean;
  gateResults: Map<string, GateResult>;
  overallStatus: 'passed' | 'failed' | 'partial';
  blockedBy?: string[];
}

export class GateExecutor {
  private gateRegistry: GateRegistry;
  private eventWriter: GovernanceEventWriter;

  constructor(private workspace: string = process.cwd()) {
    this.gateRegistry = new GateRegistry(workspace);
    this.eventWriter = new GovernanceEventWriter(workspace);
  }

  async executeAll(): Promise<ExecutionResult> {
    const result: ExecutionResult = {
      success: true,
      gateResults: new Map(),
      overallStatus: 'passed',
      blockedBy: []
    };

    const gates = this.gateRegistry.getAllGates();

    for (const gate of gates) {
      const gateResult = await gate.execute();
      result.gateResults.set(gate.name, gateResult);

      if (!gateResult.passed) {
        result.success = false;
        result.blockedBy?.push(gate.name);
      }

      // Write governance event
      await this.eventWriter.writeEvent({
        id: `gate-${gate.name}-${Date.now()}`,
        type: 'enforcement',
        timestamp: new Date().toISOString(),
        source: 'gl-gate/core/GateExecutor.ts',
        data: {
          gate: gate.name,
          result: gateResult
        }
      });
    }

    if (result.blockedBy && result.blockedBy.length > 0) {
      result.overallStatus = result.blockedBy.length === gates.length ? 'failed' : 'partial';
    }

    return result;
  }

  async executeGate(gateName: string): Promise<GateResult> {
    const gate = this.gateRegistry.getGate(gateName);
    
    if (!gate) {
      throw new Error(`Gate not found: ${gateName}`);
    }

    const result = await gate.execute();

    await this.eventWriter.writeEvent({
      id: `gate-${gateName}-${Date.now()}`,
      type: 'enforcement',
      timestamp: new Date().toISOString(),
      source: 'gl-gate/core/GateExecutor.ts',
      data: {
        gate: gateName,
        result
      }
    });

    return result;
  }

  async executeUntilFailure(): Promise<ExecutionResult> {
    const result: ExecutionResult = {
      success: true,
      gateResults: new Map(),
      overallStatus: 'passed',
      blockedBy: []
    };

    const gates = this.gateRegistry.getAllGates();

    for (const gate of gates) {
      const gateResult = await gate.execute();
      result.gateResults.set(gate.name, gateResult);

      if (!gateResult.passed) {
        result.success = false;
        result.overallStatus = 'failed';
        result.blockedBy?.push(gate.name);
        break; // Stop on first failure
      }
    }

    return result;
  }
}