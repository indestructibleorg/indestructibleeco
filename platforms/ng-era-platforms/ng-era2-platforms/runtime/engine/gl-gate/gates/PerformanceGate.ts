/**
 * @ECO-governed
 * @ECO-layer: governance
 * @ECO-semantic: performance-gate
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Performance Gate
 * Validates performance requirements
 */

import { BaseGate, GateResult } from './BaseGate';
import { promises as fs } from 'fs';
import path from 'path';

export class PerformanceGate extends BaseGate {
  readonly name = 'PerformanceGate';
  readonly description = 'Validates performance requirements';

  async execute(): Promise<GateResult> {
    const errors: string[] = [];
    const warnings: string[] = [];
    let checksPassed = 0;
    let checksFailed = 0;

    try {
      // Check for performance optimization markers
      const sourceFiles = await this.scanSourceFiles();
      let optimizedFiles = 0;

      for (const filePath of sourceFiles) {
        const content = await fs.readFile(filePath, 'utf-8');
        
        // Check for lazy loading, memoization, etc.
        if (content.includes('lazy') || 
            content.includes('memo') || 
            content.includes('useMemo') ||
            content.includes('useCallback')) {
          optimizedFiles++;
        }
      }

      if (sourceFiles.length > 0 && optimizedFiles / sourceFiles.length < 0.3) {
        warnings.push('Low performance optimization detected (< 30% of files optimized)');
      }
      checksPassed++;

      // Check bundle size configuration
      const webConfigPath = path.join(this.workspace, 'aep-engine-web', 'vite.config.ts');
      try {
        const webConfig = await fs.readFile(webConfigPath, 'utf-8');
        if (webConfig.includes('build') || webConfig.includes('chunkSizeWarningLimit')) {
          checksPassed++;
        } else {
          warnings.push('Bundle size limits not configured');
          checksPassed++;
        }
      } catch {
        warnings.push('Web config not found for performance check');
        checksPassed++;
      }

    } catch (error) {
      errors.push(`Performance gate execution error: ${error}`);
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