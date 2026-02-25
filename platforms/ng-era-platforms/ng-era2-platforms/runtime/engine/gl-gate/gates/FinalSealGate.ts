/**
 * @ECO-governed
 * @ECO-layer: governance
 * @ECO-semantic: final-seal-gate
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Final Seal Gate
 * Final validation before deployment
 */

import { BaseGate, GateResult } from './BaseGate';
import { promises as fs } from 'fs';
import path from 'path';

export class FinalSealGate extends BaseGate {
  readonly name = 'FinalSealGate';
  readonly description = 'Final validation before deployment';

  async execute(): Promise<GateResult> {
    const errors: string[] = [];
    const warnings: string[] = [];
    let checksPassed = 0;
    let checksFailed = 0;

    try {
      // Check for deployment readiness
      const requiredFiles = [
        'package.json',
        'README.md',
        '.governance/GL_SEMANTIC_ANCHOR.json'
      ];

      for (const requiredFile of requiredFiles) {
        const filePath = path.join(this.workspace, requiredFile);
        try {
          await fs.access(filePath);
          checksPassed++;
        } catch {
          errors.push(`Required file missing: ${requiredFile}`);
          checksFailed++;
        }
      }

      // Validate semantic anchor
      const anchorPath = path.join(this.workspace, '.governance', 'GL_SEMANTIC_ANCHOR.json');
      try {
        const anchorContent = await fs.readFile(anchorPath, 'utf-8');
        const anchor = JSON.parse(anchorContent);
        
        if (!anchor.governance || !anchor.governance.charter) {
          errors.push('Invalid semantic anchor: missing governance section');
          checksFailed++;
        } else {
          checksPassed++;
        }
      } catch {
        errors.push('Cannot read or parse semantic anchor');
        checksFailed++;
      }

    } catch (error) {
      errors.push(`Final seal gate execution error: ${error}`);
      checksFailed++;
    }

    const passed = errors.length === 0;
    return this.createResult(passed, errors, warnings, checksPassed, checksFailed);
  }
}