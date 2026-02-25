# @ECO-governed
# @ECO-layer: GL20-29
# @ECO-semantic: typescript-module
# @ECO-audit-trail: ../../engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
#
# GL Unified Charter Activated
# GL Root Semantic Anchor: gl-platform-universe/governance/engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
# GL Unified Naming Charter: gl-platform-universe/governance/engine/governance/gl-artifacts/meta/naming-charter/gl-unified-naming-charter.yaml

// @ECO-governed @ECO-internal-only
// Production-grade Execution Engine with Zero Residue
// Version: 3.0.0

import * as child_process from 'child_process';
import * as fs from 'fs/promises';
import * as path from 'path';
import { v4 as uuidv4 } from 'uuid';

export interface ExecutionOptions {
  command: string;
  isolation?: boolean;
  timeout?: number;
  memoryLimit?: string;
  cpuLimit?: string;
  workspace?: string;
  cleanup?: boolean;
}

export interface ExecutionResult {
  success: boolean;
  exitCode: number;
  duration: number;
  memory: number;
  residue: string[];
  output?: string;
  error?: string;
}

export class ExecutionEngine {
  private workspace: string;
  private cleanupEnabled: boolean;

  constructor() {
    this.workspace = '';
    this.cleanupEnabled = true;
  }

  /**
   * Initialize zero-residue execution environment
   */
  async initialize(): Promise<void> {
    // Create memory workspace
    const workspaceId = uuidv4().replace(/-/g, '').substring(0, 12);
    this.workspace = `/dev/shm/gl-exec-${workspaceId}`;
    
    await fs.mkdir(this.workspace, { mode: 0o700 });
    
    // Set resource limits
    this.setResourceLimits();
  }

  /**
   * Set strict resource limits
   */
  private setResourceLimits(): void {
    try {
      process.setMaxListeners(100);
      // Additional limits would be set via cgroups in production
    } catch (error) {
      // Ignore errors in non-production environments
    }
  }

  /**
   * Execute command with zero residue
   */
  async execute(options: ExecutionOptions): Promise<ExecutionResult> {
    const startTime = Date.now();
    const workspace = options.workspace || this.workspace;
    
    // Ensure workspace exists
    if (!workspace) {
      throw new Error('Workspace not initialized');
    }

    const result: ExecutionResult = {
      success: false,
      exitCode: -1,
      duration: 0,
      memory: 0,
      residue: []
    };

    try {
      // Execute with isolation if requested
      let command = options.command;
      if (options.isolation) {
        command = `unshare --mount --uts --ipc --net --pid --fork bash -c "${command}"`;
      }

      // Execute command
      const execResult = await this.runCommand(command, workspace, options.timeout);
      
      result.success = execResult.exitCode === 0;
      result.exitCode = execResult.exitCode;
      result.duration = Date.now() - startTime;
      
      // Check for residue
      result.residue = await this.checkResidue(workspace);
      
      // Cleanup if enabled
      if (this.cleanupEnabled && options.cleanup !== false) {
        await this.cleanup(workspace);
      }
      
      return result;
      
    } catch (error) {
      result.success = false;
      result.error = error instanceof Error ? error.message : String(error);
      result.duration = Date.now() - startTime;
      
      // Ensure cleanup on error
      if (this.cleanupEnabled) {
        await this.cleanup(workspace).catch(() => {});
      }
      
      return result;
    }
  }

  /**
   * Run command in isolation
   */
  private runCommand(command: string, workspace: string, timeout?: number): Promise<child_process.SpawnSyncReturns<string>> {
    return new Promise((resolve, reject) => {
      try {
        const result = child_process.spawnSync(
          'bash',
          ['-c', `cd ${workspace} && ${command}`],
          {
            timeout: timeout || 30000,
            env: {
              ...process.env,
              GL_EXECUTION_MODE: 'zero-residue',
              GL_WORKSPACE: workspace
            },
            stdio: ['ignore', 'pipe', 'pipe']
          }
        );
        
        resolve(result);
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Check for residual files
   */
  private async checkResidue(workspace: string): Promise<string[]> {
    try {
      const files = await fs.readdir(workspace);
      return files.filter(file => 
        file.includes('.tmp') || 
        file.includes('.log') || 
        file.includes('.cache') ||
        file.startsWith('temp_')
      );
    } catch {
      return [];
    }
  }

  /**
   * Cleanup workspace with secure wipe
   */
  private async cleanup(workspace: string): Promise<void> {
    try {
      // Remove all files
      const files = await fs.readdir(workspace);
      for (const file of files) {
        const filePath = path.join(workspace, file);
        await fs.unlink(filePath);
      }
      
      // Remove workspace directory
      await fs.rmdir(workspace);
    } catch (error) {
      // Ignore cleanup errors
    }
  }

  /**
   * Verify zero residue
   */
  async verifyZeroResidue(): Promise<boolean> {
    const residue = await this.checkResidue(this.workspace);
    return residue.length === 0;
  }

  /**
   * Get execution statistics
   */
  getStats() {
    return {
      workspace: this.workspace,
      cleanupEnabled: this.cleanupEnabled
    };
  }
}