/**
 * @ECO-governed
 * @ECO-layer: governance
 * @ECO-semantic: security-gate
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Security Gate
 * Validates security compliance
 */

import { BaseGate, GateResult } from './BaseGate';
import { promises as fs } from 'fs';
import path from 'path';

export class SecurityGate extends BaseGate {
  readonly name = 'SecurityGate';
  readonly description = 'Validates security compliance';

  async execute(): Promise<GateResult> {
    const errors: string[] = [];
    const warnings: string[] = [];
    let checksPassed = 0;
    let checksFailed = 0;

    try {
      // Check for exposed secrets (simplified)
      const sensitivePatterns = [
        /password\s*[:=]\s*['"].*['"]/,
        /api[_-]?key\s*[:=]\s*['"].*['"]/,
        /secret\s*[:=]\s*['"].*['"]/
      ];

      const sourceFiles = await this.scanSourceFiles();
      
      for (const filePath of sourceFiles) {
        const content = await fs.readFile(filePath, 'utf-8');
        
        for (const pattern of sensitivePatterns) {
          if (pattern.test(content)) {
            const relativePath = path.relative(this.workspace, filePath);
            errors.push(`Potential sensitive data in ${relativePath}`);
            checksFailed++;
            break;
          }
        }
      }

      if (errors.length === 0) {
        checksPassed++;
      }

      // Check for security headers in web config
      const webConfigPath = path.join(this.workspace, 'aep-engine-web', 'vite.config.ts');
      try {
        const webConfig = await fs.readFile(webConfigPath, 'utf-8');
        if (webConfig.includes('security') || webConfig.includes('headers')) {
          checksPassed++;
        } else {
          warnings.push('Security headers not configured in web config');
          checksPassed++;
        }
      } catch {
        warnings.push('Web config not found for security check');
        checksPassed++;
      }

    } catch (error) {
      errors.push(`Security gate execution error: ${error}`);
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
        } else if (entry.isFile() && /\.(ts|tsx|js|json)$/.test(entry.name)) {
          files.push(fullPath);
        }
      }
    };

    await scanDir(engineDir);
    return files;
  }
}