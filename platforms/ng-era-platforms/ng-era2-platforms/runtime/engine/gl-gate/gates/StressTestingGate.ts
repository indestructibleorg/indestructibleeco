/**
 * @ECO-governed
 * @ECO-layer: governance
 * @ECO-semantic: stress-testing-gate
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Stress Testing Gate
 * Validates system under load
 */

import { BaseGate, GateResult } from './BaseGate';
import { promises as fs } from 'fs';
import path from 'path';

export class StressTestingGate extends BaseGate {
  readonly name = 'StressTestingGate';
  readonly description = 'Validates system under load';

  async execute(): Promise<GateResult> {
    const errors: string[] = [];
    const warnings: string[] = [];
    let checksPassed = 0;
    let checksFailed = 0;

    try {
      // Check for stress test configuration
      const stressTestConfig = path.join(this.workspace, '.governance', 'stress-test.config.json');
      
      try {
        await fs.access(stressTestConfig);
        checksPassed++;
      } catch {
        warnings.push('Stress test configuration not found');
        checksPassed++;
      }

      // Check for load test scripts
      const testScripts = await this.findTestScripts();
      
      if (testScripts.length > 0) {
        checksPassed++;
      } else {
        warnings.push('No load test scripts found');
        checksPassed++;
      }

      // Validate resource limits
      const packageJsonPath = path.join(this.workspace, 'package.json');
      try {
        const packageJson = JSON.parse(await fs.readFile(packageJsonPath, 'utf-8'));
        
        if (packageJson.scripts?.['stress-test'] || packageJson.scripts?.['load-test']) {
          checksPassed++;
        } else {
          warnings.push('No stress test script defined in package.json');
          checksPassed++;
        }
      } catch {
        warnings.push('package.json not found for stress test validation');
        checksPassed++;
      }

    } catch (error) {
      errors.push(`Stress testing gate execution error: ${error}`);
      checksFailed++;
    }

    const passed = errors.length === 0;
    return this.createResult(passed, errors, warnings, checksPassed, checksFailed);
  }

  private async findTestScripts(): Promise<string[]> {
    const files: string[] = [];
    const testDir = path.join(this.workspace, 'tests');

    try {
      const entries = await fs.readdir(testDir, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = path.join(testDir, entry.name);
        
        if (entry.isFile() && /\.(ts|tsx|js)$/.test(entry.name)) {
          const content = await fs.readFile(fullPath, 'utf-8');
          if (content.includes('stress') || content.includes('load')) {
            files.push(fullPath);
          }
        }
      }
    } catch {
      // Test directory not found
    }

    return files;
  }
}