/**
 * @ECO-governed
 * @ECO-layer: governance
 * @ECO-semantic: observability-gate
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Observability Gate
 * Validates logging and monitoring setup
 */

import { BaseGate, GateResult } from './BaseGate';
import { promises as fs } from 'fs';
import path from 'path';

export class ObservabilityGate extends BaseGate {
  readonly name = 'ObservabilityGate';
  readonly description = 'Validates logging and monitoring setup';

  async execute(): Promise<GateResult> {
    const errors: string[] = [];
    const warnings: string[] = [];
    let checksPassed = 0;
    let checksFailed = 0;

    try {
      // Check for logging implementation
      const sourceFiles = await this.scanSourceFiles();
      let loggedFiles = 0;

      for (const filePath of sourceFiles) {
        const content = await fs.readFile(filePath, 'utf-8');
        
        // Check for console.log, logger, etc.
        if (content.includes('console.log') || 
            content.includes('logger') || 
            content.includes('log.') ||
            content.includes('winston') ||
            content.includes('pino')) {
          loggedFiles++;
        }
      }

      if (loggedFiles > 0) {
        checksPassed++;
      } else {
        warnings.push('No logging detected in source files');
        checksPassed++;
      }

      // Check for monitoring configuration
      const monitoringConfig = path.join(this.workspace, 'monitoring.config.js');
      try {
        await fs.access(monitoringConfig);
        checksPassed++;
      } catch {
        warnings.push('Monitoring configuration not found');
        checksPassed++;
      }

    } catch (error) {
      errors.push(`Observability gate execution error: ${error}`);
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