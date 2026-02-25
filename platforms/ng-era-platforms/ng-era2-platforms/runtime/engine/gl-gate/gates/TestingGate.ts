/**
 * @ECO-governed
 * @ECO-layer: governance
 * @ECO-semantic: testing-gate
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Testing Gate
 * Validates test coverage and quality
 */

import { BaseGate, GateResult } from './BaseGate';
import { promises as fs } from 'fs';
import path from 'path';

export class TestingGate extends BaseGate {
  readonly name = 'TestingGate';
  readonly description = 'Validates test coverage and quality';

  async execute(): Promise<GateResult> {
    const errors: string[] = [];
    const warnings: string[] = [];
    let checksPassed = 0;
    let checksFailed = 0;

    try {
      const testDir = path.join(this.workspace, 'tests');
      
      // Check if tests directory exists
      try {
        await fs.access(testDir);
        checksPassed++;
      } catch {
        errors.push('Tests directory not found');
        checksFailed++;
        return this.createResult(false, errors, warnings, checksPassed, checksFailed);
      }

      // Scan for test files
      const testFiles = await this.scanTestFiles(testDir);
      
      if (testFiles.length === 0) {
        errors.push('No test files found');
        checksFailed++;
      } else {
        checksPassed++;
        warnings.push(`Found ${testFiles.length} test files`);
      }

      // Check for test coverage (simplified)
      const coverage = await this.estimateCoverage(testFiles);
      if (coverage < 50) {
        errors.push(`Test coverage below 50%: ${coverage.toFixed(1)}%`);
        checksFailed++;
      } else {
        checksPassed++;
      }

    } catch (error) {
      errors.push(`Testing gate execution error: ${error}`);
      checksFailed++;
    }

    const passed = errors.length === 0;
    return this.createResult(passed, errors, warnings, checksPassed, checksFailed);
  }

  private async scanTestFiles(dir: string): Promise<string[]> {
    const files: string[] = [];
    const entries = await fs.readdir(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      
      if (entry.isDirectory()) {
        files.push(...await this.scanTestFiles(fullPath));
      } else if (entry.isFile() && /\.(test|spec)\.(ts|tsx|js)$/.test(entry.name)) {
        files.push(fullPath);
      }
    }

    return files;
  }

  private async estimateCoverage(testFiles: string[]): Promise<number> {
    // Simplified coverage estimation
    // In production, use actual coverage tools
    return Math.min(testFiles.length * 10, 100);
  }
}