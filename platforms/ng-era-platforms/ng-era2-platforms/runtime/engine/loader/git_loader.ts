/**
 * @ECO-governed
 * @ECO-layer: loader
 * @ECO-semantic: loader-git_loader
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

/**
 * @module git_loader
 * @description Git repository configuration loader
 * @gl-governed
 * GL Unified Charter Activated
 * @gl-layer ECO-30-EXECUTION
 * @gl-module engine/loader
 * @gl-semantic-anchor ECO-30-EXEC-TS
 * @gl-evidence-required true
 * @version 1.0.0
 * @since 2026-01-24
 * @author MachineNativeOps Team
 */

import * as path from 'path';
import { execSync } from 'child_process';
import { LoaderInterface, LoadResult, EvidenceRecord } from '../interfaces.d';

/**
 * Git Loader
 * 
 * GL30-49: Execution Layer - Loader Stage
 * 
 * Loads DSL files from Git repositories, supporting
 * branches, tags, and commit references. Generates complete
 * evidence chains with git metadata.
 */
export class GitLoader implements LoaderInterface {
  private evidence: EvidenceRecord[] = [];
  private readonly repoUrl: string;
  private readonly targetDir: string;
  private readonly options: {
    branch?: string;
    tag?: string;
    commit?: string;
    depth?: number;
  };

  constructor(repoUrl: string, targetDir: string, options?: {
    branch?: string;
    tag?: string;
    commit?: string;
    depth?: number;
  }) {
    this.repoUrl = repoUrl;
    this.targetDir = path.resolve(targetDir);
    this.options = options || {};
  }

  /**
   * Clone repository and load DSL files
   */
  async load(): Promise<LoadResult> {
    const startTime = Date.now();
    const files: Map<string, any> = new Map();
    const errors: string[] = [];

    try {
      // Clone repository
      const cloneResult = await this.cloneRepository();
      
      if (cloneResult.status !== 'success') {
        throw new Error(cloneResult.errors[0] || 'Failed to clone repository');
      }

      // Load files using FS loader logic
      await this.loadDslFiles(files, errors);

      // Generate evidence record
      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'loader',
        component: 'git_loader',
        action: 'load',
        status: errors.length > 0 ? 'warning' : 'success',
        input: {
          repoUrl: this.repoUrl,
          branch: this.options.branch,
          tag: this.options.tag,
          commit: this.options.commit
        },
        output: { fileCount: files.size, errorCount: errors.length },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: errors.length > 0 ? 'warning' : 'success',
        files,
        errors,
        evidence: this.evidence
      };
    } catch (error) {
      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'loader',
        component: 'git_loader',
        action: 'load',
        status: 'error',
        input: {
          repoUrl: this.repoUrl,
          branch: this.options.branch,
          tag: this.options.tag
        },
        output: { error: error instanceof Error ? error.message : String(error) },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'error',
        files,
        errors: [error instanceof Error ? error.message : String(error)],
        evidence: this.evidence
      };
    }
  }

  /**
   * Clone Git repository
   */
  private async cloneRepository(): Promise<LoadResult> {
    const startTime = Date.now();
    const errors: string[] = [];

    try {
      // Remove target directory if exists
      const fs = require('fs');
      if (fs.existsSync(this.targetDir)) {
        fs.rmSync(this.targetDir, { recursive: true, force: true });
      }

      // Build clone command
      let cmd = `git clone ${this.repoUrl} ${this.targetDir}`;
      
      if (this.options.depth) {
        cmd += ` --depth ${this.options.depth}`;
      }

      if (this.options.branch) {
        cmd += ` --branch ${this.options.branch}`;
      }

      // Execute clone
      execSync(cmd, { stdio: 'pipe', encoding: 'utf-8' });

      // Checkout specific tag/commit if specified
      if (this.options.tag || this.options.commit) {
        const ref = this.options.tag || this.options.commit;
        execSync(`cd ${this.targetDir} && git checkout ${ref}`, { stdio: 'pipe' });
      }

      // Get git metadata
      const commitHash = execSync(
        `cd ${this.targetDir} && git rev-parse HEAD`,
        { encoding: 'utf-8' }
      ).trim();

      const commitMessage = execSync(
        `cd ${this.targetDir} && git log -1 --pretty=%B`,
        { encoding: 'utf-8' }
      ).trim();

      const commitDate = execSync(
        `cd ${this.targetDir} && git log -1 --pretty=%ci`,
        { encoding: 'utf-8' }
      ).trim();

      // Record evidence
      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'loader',
        component: 'git_loader',
        action: 'clone',
        status: 'success',
        input: {
          repoUrl: this.repoUrl,
          branch: this.options.branch,
          tag: this.options.tag,
          commit: this.options.commit
        },
        output: {
          commitHash,
          commitMessage,
          commitDate,
          targetDir: this.targetDir
        },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'success',
        files: new Map(),
        errors: [],
        evidence: this.evidence
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      errors.push(`Failed to clone repository: ${errorMsg}`);

      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'loader',
        component: 'git_loader',
        action: 'clone',
        status: 'error',
        input: {
          repoUrl: this.repoUrl,
          branch: this.options.branch
        },
        output: { error: errorMsg },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'error',
        files: new Map(),
        errors,
        evidence: this.evidence
      };
    }
  }

  /**
   * Load DSL files from cloned repository
   */
  private async loadDslFiles(
    files: Map<string, any>,
    errors: string[]
  ): Promise<void> {
    const fs = require('fs');
    const walk = (dir: string, relativePath: string = '') => {
      const entries = fs.readdirSync(dir, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        const relPath = path.join(relativePath, entry.name);

        // Skip .git directory
        if (entry.name === '.git') {
          continue;
        }

        if (entry.isDirectory()) {
          walk(fullPath, relPath);
        } else if (entry.isFile()) {
          const ext = path.extname(fullPath).toLowerCase();

          if (
!['.yaml', '.yml', '.json'].includes(ext)
) {
            return;
          }

          try {
            const content = fs.readFileSync(fullPath, 'utf-8');
            
            files.set(relPath, {
              path: relPath,
              fullPath,
              content,
              type: ext,
              size: content.length,
              hash: this.generateHash(content),
              modified: fs.statSync(fullPath).mtime.toISOString()
            });

            this.evidence.push({
              timestamp: new Date().toISOString(),
              stage: 'loader',
              component: 'git_loader',
              action: 'load_file',
              status: 'success',
              input: { path: relPath },
              output: { size: content.length, type: ext },
              metrics: {}
            });
          } catch (error) {
            errors.push(
              `Failed to load ${relPath}: ${error instanceof Error ? error.message : String(error)}`
            );
          }
        }
      }
    };

    walk(this.targetDir);
  }

  /**
   * Generate SHA256 hash
   */
  private generateHash(content: string): string {
    const crypto = require('crypto');
    return crypto.createHash('sha256').update(content).digest('hex');
  }

  /**
   * Get evidence records
   */
  getEvidence(): EvidenceRecord[] {
    return this.evidence;
  }
}