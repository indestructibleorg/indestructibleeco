/**
 * @ECO-governed
 * @ECO-layer: governance
 * @ECO-semantic: governance-summary-gate
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Governance Summary Gate
 * Generates final governance summary report
 */

import { BaseGate, GateResult } from './BaseGate';
import { promises as fs } from 'fs';
import path from 'path';

export class GovernanceSummaryGate extends BaseGate {
  readonly name = 'GovernanceSummaryGate';
  readonly description = 'Generates final governance summary report';

  async execute(): Promise<GateResult> {
    const errors: string[] = [];
    const warnings: string[] = [];
    let checksPassed = 0;
    let checksFailed = 0;

    try {
      // Generate governance summary
      const summary = {
        timestamp: new Date().toISOString(),
        charter: 'GL Unified Charter',
        version: '1.0.0',
        activation: 'active',
        totalFiles: 0,
        governedFiles: 0,
        complianceRate: 0
      };

      // Count governed files
      const sourceFiles = await this.scanSourceFiles();
      summary.totalFiles = sourceFiles.length;

      for (const filePath of sourceFiles) {
        const content = await fs.readFile(filePath, 'utf-8');
        if (content.includes('@ECO-governed')) {
          summary.governedFiles++;
        }
      }

      summary.complianceRate = summary.totalFiles > 0 
        ? (summary.governedFiles / summary.totalFiles) * 100 
        : 0;

      // Write summary to file
      const summaryPath = path.join(this.workspace, '.governance', 'summary.json');
      await fs.mkdir(path.dirname(summaryPath), { recursive: true });
      await fs.writeFile(summaryPath, JSON.stringify(summary, null, 2), 'utf-8');

      checksPassed++;

      if (summary.complianceRate < 100) {
        warnings.push(`Governance compliance at ${summary.complianceRate.toFixed(1)}%`);
      }

    } catch (error) {
      errors.push(`Governance summary gate execution error: ${error}`);
      checksFailed++;
    }

    const passed = errors.length === 0;
    return this.createResult(passed, errors, warnings, checksPassed, checksFailed);
  }

  private async scanSourceFiles(): Promise<string[]> {
    const files: string[] = [];
    const engineDir = path.join(this.workspace, 'engine');

    const scanDir = async (dir: string): Promise<void> => {
      const entries = await fs.readdir(dir, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        
        if (entry.isDirectory() && 
!['node_modules', '__pycache__', 'dist', 'build'].includes(entry.name)
) {
          await scanDir(fullPath);
        } else if (entry.isFile() && /\.(ts|tsx|js)$/.test(entry.name)) {
          files.push(fullPath);
        }
      }
    };

    await scanDir(engineDir);
    return files;
  }
}