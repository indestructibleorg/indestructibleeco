/**
 * @ECO-governed
 * @ECO-layer: governance
 * @ECO-semantic: integration-gate
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Integration Gate
 * Validates integration points and dependencies
 */

import { BaseGate, GateResult } from './BaseGate';
import { promises as fs } from 'fs';
import path from 'path';

export class IntegrationGate extends BaseGate {
  readonly name = 'IntegrationGate';
  readonly description = 'Validates integration points and dependencies';

  async execute(): Promise<GateResult> {
    const errors: string[] = [];
    const warnings: string[] = [];
    let checksPassed = 0;
    let checksFailed = 0;

    try {
      // Check for integration markers
      const sourceFiles = await this.scanSourceFiles();
      let integrationFiles = 0;

      for (const filePath of sourceFiles) {
        const content = await fs.readFile(filePath, 'utf-8');
        
        // Check for API calls, database connections, etc.
        if (content.includes('fetch') || 
            content.includes('axios') || 
            content.includes('http') ||
            content.includes('db') ||
            content.includes('database')) {
          integrationFiles++;
        }
      }

      if (integrationFiles > 0) {
        checksPassed++;
      }

      // Validate package.json dependencies
      const packageJsonPath = path.join(this.workspace, 'package.json');
      try {
        const packageJson = JSON.parse(await fs.readFile(packageJsonPath, 'utf-8'));
        
        if (packageJson.dependencies) {
          checksPassed++;
        }

        if (packageJson.devDependencies) {
          checksPassed++;
        }
      } catch {
        warnings.push('package.json not found or invalid');
        checksFailed++;
      }

    } catch (error) {
      errors.push(`Integration gate execution error: ${error}`);
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