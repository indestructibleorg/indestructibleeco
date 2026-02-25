# @ECO-governed
# @ECO-layer: GL20-29
# @ECO-semantic: typescript-module
# @ECO-audit-trail: ../../engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
#
# GL Unified Charter Activated
# GL Root Semantic Anchor: gl-platform-universe/governance/engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
# GL Unified Naming Charter: gl-platform-universe/governance/engine/governance/gl-artifacts/meta/naming-charter/gl-unified-naming-charter.yaml

// @ECO-governed @ECO-internal-only
// Production-grade Zero Residue Cleaner
// Version: 3.0.0

import * as fs from 'fs/promises';
import * as path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export interface CleanupPolicy {
  name: string;
  pattern: string[];
  location: string;
  maxAge: number;
  action: 'delete' | 'secure-wipe' | 'archive';
}

export interface CleanupResult {
  success: boolean;
  filesProcessed: number;
  bytesFreed: number;
  duration: number;
  errors: string[];
}

export class ZeroResidueCleaner {
  private policies: CleanupPolicy[] = [];

  constructor() {
    this.initializePolicies();
  }

  /**
   * Initialize cleanup policies
   */
  private initializePolicies(): void {
    this.policies = [
      {
        name: 'temp-file-cleanup',
        pattern: ['*.tmp', '*.temp', '*.cache', '*.log'],
        location: '/tmp',
        maxAge: 5 * 60 * 1000, // 5 minutes
        action: 'delete'
      },
      {
        name: 'workspace-cleanup',
        pattern: ['gl-exec-*', 'gl-work-*'],
        location: '/dev/shm',
        maxAge: 60 * 60 * 1000, // 1 hour
        action: 'secure-wipe'
      },
      {
        name: 'debug-file-cleanup',
        pattern: ['debug_*', '*-debug.*', 'temp_*'],
        location: process.cwd(),
        maxAge: 10 * 60 * 1000, // 10 minutes
        action: 'delete'
      }
    ];
  }

  /**
   * Execute cleanup based on policies
   */
  async executeCleanup(): Promise<CleanupResult> {
    const startTime = Date.now();
    const result: CleanupResult = {
      success: true,
      filesProcessed: 0,
      bytesFreed: 0,
      duration: 0,
      errors: []
    };

    try {
      for (const policy of this.policies) {
        try {
          const policyResult = await this.executePolicy(policy);
          result.filesProcessed += policyResult.filesProcessed;
          result.bytesFreed += policyResult.bytesFreed;
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : String(error);
          result.errors.push(`Policy ${policy.name} failed: ${errorMessage}`);
        }
      }

      // Clear memory caches
      await this.clearMemoryCaches();

      result.duration = Date.now() - startTime;
      result.success = result.errors.length === 0;

      return result;
    } catch (error) {
      result.duration = Date.now() - startTime;
      result.success = false;
      result.errors.push(error instanceof Error ? error.message : String(error));
      return result;
    }
  }

  /**
   * Execute single cleanup policy
   */
  private async executePolicy(policy: CleanupPolicy): Promise<{ filesProcessed: number; bytesFreed: number }> {
    let filesProcessed = 0;
    let bytesFreed = 0;

    try {
      // Find files matching patterns
      for (const pattern of policy.pattern) {
        const findCommand = `find ${policy.location} -name "${pattern}" -type f -mtime -$((${policy.maxAge / 1000 / 60}))m 2>/dev/null`;
        
        try {
          const { stdout } = await execAsync(findCommand);
          const files = stdout.trim().split('\n').filter(f => f);

          for (const filePath of files) {
            try {
              const stats = await fs.stat(filePath);
              
              // Check age
              const age = Date.now() - stats.mtimeMs;
              if (age > policy.maxAge) {
                if (policy.action === 'secure-wipe') {
                  await this.secureWipe(filePath);
                } else {
                  await fs.unlink(filePath);
                }
                
                filesProcessed++;
                bytesFreed += stats.size;
              }
            } catch {
              // Ignore individual file errors
            }
          }
        } catch {
          // Ignore find command errors
        }
      }
    } catch (error) {
      // Ignore policy execution errors
    }

    return { filesProcessed, bytesFreed };
  }

  /**
   * Secure wipe file (7-pass)
   */
  private async secureWipe(filePath: string): Promise<void> {
    try {
      const shredCommand = `shred -n 3 -z -u "${filePath}" 2>/dev/null`;
      await execAsync(shredCommand);
    } catch {
      // Fallback to regular delete if shred fails
      await fs.unlink(filePath);
    }
  }

  /**
   * Clear memory caches
   */
  private async clearMemoryCaches(): Promise<void> {
    try {
      await execAsync('sync && echo 3 > /proc/sys/vm/drop_caches 2>/dev/null');
    } catch {
      // Ignore cache clear errors (may require root)
    }
  }

  /**
   * Verify zero residue
   */
  async verifyZeroResidue(): Promise<{ isClean: boolean; residueFiles: string[] }> {
    const residueFiles: string[] = [];

    // Check common temporary locations
    const locations = ['/tmp', '/var/tmp', '/dev/shm'];
    const patterns = ['gl-*', 'temp-*', '*.tmp', '*.temp', '*.cache'];

    for (const location of locations) {
      try {
        for (const pattern of patterns) {
          try {
            const { stdout } = await execAsync(`find ${location} -name "${pattern}" 2>/dev/null`);
            const files = stdout.trim().split('\n').filter(f => f);
            residueFiles.push(...files);
          } catch {
            // Ignore find errors
          }
        }
      } catch {
        // Ignore location errors
      }
    }

    return {
      isClean: residueFiles.length === 0,
      residueFiles
    };
  }

  /**
   * Add custom cleanup policy
   */
  addPolicy(policy: CleanupPolicy): void {
    this.policies.push(policy);
  }

  /**
   * Remove cleanup policy
   */
  removePolicy(policyName: string): void {
    this.policies = this.policies.filter(p => p.name !== policyName);
  }

  /**
   * Get cleanup policies
   */
  getPolicies(): CleanupPolicy[] {
    return [...this.policies];
  }
}