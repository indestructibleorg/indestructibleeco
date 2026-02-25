/**
 * @ECO-governed
 * @ECO-layer: governance
 * @ECO-semantic: data-access-gate
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Data Access Gate
 * Validates data access patterns and security
 */

import { BaseGate, GateResult } from './BaseGate';
import { promises as fs } from 'fs';
import path from 'path';

export class DataAccessGate extends BaseGate {
  readonly name = 'DataAccessGate';
  readonly description = 'Validates data access patterns and security';

  async execute(): Promise<GateResult> {
    const errors: string[] = [];
    const warnings: string[] = [];
    let checksPassed = 0;
    let checksFailed = 0;

    try {
      // Check for data access patterns
      const sourceFiles = await this.scanSourceFiles();
      let dataAccessFiles = 0;

      for (const filePath of sourceFiles) {
        const content = await fs.readFile(filePath, 'utf-8');
        
        // Check for SQL injection risks
        if (content.includes('SELECT') && content.includes("WHERE")) {
          if (content.includes("'") || content.includes('"')) {
            warnings.push('Potential SQL injection risk detected');
            checksPassed++;
          }
        }

        // Check for data validation
        if (content.includes('validate') || 
            content.includes('sanitize') || 
            content.includes('escape')) {
          dataAccessFiles++;
        }
      }

      if (dataAccessFiles > 0) {
        checksPassed++;
      }

      // Check for environment variable usage for credentials
      const envFiles = ['.env', '.env.local', '.env.example'];
      for (const envFile of envFiles) {
        try {
          const envPath = path.join(this.workspace, envFile);
          await fs.access(envPath);
          checksPassed++;
        } catch {
          // File not found, skip
        }
      }

    } catch (error) {
      errors.push(`Data access gate execution error: ${error}`);
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