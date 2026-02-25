/**
 * @ECO-governed
 * @ECO-layer: executor
 * @ECO-semantic: executor-local_executor
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

/**
 * @module local_executor
 * @description Local artifact execution with command and file operations
 * @gl-governed
 * GL Unified Charter Activated
 * @gl-layer ECO-30-EXECUTION
 * @gl-module engine/executor
 * @gl-semantic-anchor ECO-30-EXEC-TS
 * @gl-evidence-required true
 * @version 1.0.0
 * @since 2026-01-24
 * @author MachineNativeOps Team
 */

import { exec, spawn, ChildProcess } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs';
import * as path from 'path';
import { ExecutorInterface, ExecutionResult, EvidenceRecord } from '../interfaces.d';
import type { ExecutableArtifact } from '../types';

interface ExecutionLog {
  timestamp: string;
  level: 'info' | 'error' | 'warning';
  message: string;
}

interface LocalExecutionResult extends ExecutionResult {
  artifactId: string;
  exitCode?: number;
  logs: ExecutionLog[];
}

/**
 * Local Executor
 * 
 * GL30-49: Execution Layer - Executor Stage
 * 
 * Executes artifacts on the local system with full
 * command execution, file operations, and logging.
 */
export class LocalExecutor implements ExecutorInterface {
  private evidence: EvidenceRecord[] = [];
  private readonly workingDir: string;
  private readonly dryRun: boolean;

  constructor(options?: {
    workingDir?: string;
    dryRun?: boolean;
  }) {
    this.workingDir = options?.workingDir || './artifacts';
    this.dryRun = options?.dryRun ?? false;
  }

  /**
   * Execute artifact
   */
  async execute(
    artifact: ExecutableArtifact,
    env: string = 'dev'
  ): Promise<ExecutionResult> {
    const startTime = Date.now();

    try {
      if (this.dryRun) {
        return this.dryRunExecute(artifact, env);
      }

      const result = await this.realExecute(artifact, env);

      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'executor',
        component: 'local_executor',
        action: 'execute',
        status: result.status === 'success' ? 'success' : 'error',
        input: { artifactId: artifact.id, type: artifact.type, env },
        output: {
          success: result.status === 'success',
          outputLength: result.output?.length || 0
        },
        metrics: { duration: Date.now() - startTime }
      });

      return result;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);

      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'executor',
        component: 'local_executor',
        action: 'execute',
        status: 'error',
        input: { artifactId: artifact.id, env },
        output: { error: errorMsg },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'error',
        output: '',
        errors: [errorMsg],
        duration: Date.now() - startTime,
        evidence: this.evidence
      };
    }
  }

  /**
   * Real execution
   */
  private async realExecute(artifact: ExecutableArtifact, env: string): Promise<ExecutionResult> {
    const startTime = Date.now();
    
    switch (artifact.type) {
      case 'command':
        return this.executeCommand(artifact.command || '', artifact.args || [], artifact.workingDir);
      
      case 'script':
        return this.executeScript(artifact.script || '', artifact.workingDir);
      
      case 'copy':
        return this.copyFile(
          (artifact as ExecutableArtifact & { source: string }).source,
          (artifact as ExecutableArtifact & { destination: string }).destination
        );
      
      case 'mkdir':
        return this.makeDirectory(
          (artifact as ExecutableArtifact & { path: string }).path
        );
      
      case 'delete':
        return this.deleteFile(
          (artifact as ExecutableArtifact & { path: string }).path
        );
      
      case 'service':
        return this.manageService(
          (artifact as ExecutableArtifact & { service: string }).service,
          (artifact as ExecutableArtifact & { action: string }).action
        );
      
      default:
        return {
          status: 'error',
          output: '',
          errors: [`Unknown artifact type: ${artifact.type}`],
          duration: Date.now() - startTime,
          evidence: this.evidence
        };
    }
  }

  /**
   * Dry run execution
   */
  private dryRunExecute(artifact: ExecutableArtifact, env: string): ExecutionResult {
    return {
      status: 'success',
      output: `[DRY RUN] Would execute: ${JSON.stringify(artifact)}`,
      errors: [],
      duration: 0,
      evidence: this.evidence
    };
  }

  /**
   * Allowed commands whitelist for security
   * Only these commands can be executed to prevent command injection
   */
  private static readonly ALLOWED_COMMANDS = new Set([
    'node', 'npm', 'npx', 'yarn', 'pnpm',
    'python', 'python3', 'pip', 'pip3',
    'git', 'make', 'cmake',
    'ls', 'cat', 'echo', 'cp', 'mv', 'mkdir', 'rm',
    'tar', 'gzip', 'gunzip', 'zip', 'unzip'
  ]);

  /**
   * Validate command against whitelist
   */
  private validateCommand(command: string): boolean {
    // Extract base command name (handle paths like /usr/bin/node)
    const baseCommand = path.basename(command);
    return LocalExecutor.ALLOWED_COMMANDS.has(baseCommand);
  }

  /**
   * Execute command
   * @security Command is validated against whitelist to prevent injection
   */
  private async executeCommand(
    command: string,
    args: string[],
    workingDir?: string
  ): Promise<ExecutionResult> {
    // Security: Validate command against whitelist
    if (!this.validateCommand(command)) {
      return {
        status: 'error',
        output: '',
        errors: [`Command not allowed: ${command}. Only whitelisted commands can be executed.`],
        duration: 0,
        evidence: this.evidence
      };
    }

    const cwd = workingDir || this.workingDir;
    const resolvedCwd = path.resolve(cwd);
    const startTime = Date.now();

    return new Promise<ExecutionResult>((resolve) => {
      // Security: Command is validated against whitelist above (validateCommand)
      // Security: shell is disabled to prevent shell injection
      // nosemgrep: javascript.lang.security.detect-child-process.detect-child-process
      const child: ChildProcess = spawn(command, args, {
        cwd: resolvedCwd,
        shell: false
      });

      let stdout = '';
      let stderr = '';
      let finished = false;

      const timeoutMs = 30000;
      const timeout = setTimeout(() => {
        if (finished) return;
        finished = true;
        child.kill('SIGTERM');
        resolve({
          status: 'error',
          output: stdout,
          errors: [`Command timed out after ${timeoutMs}ms`],
          duration: Date.now() - startTime,
          evidence: this.evidence
        });
      }, timeoutMs);

      child.stdout?.on('data', (data: Buffer | string) => {
        stdout += data.toString();
      });

      child.stderr?.on('data', (data: Buffer | string) => {
        stderr += data.toString();
      });

      child.on('error', (error: Error) => {
        if (finished) return;
        finished = true;
        clearTimeout(timeout);
        resolve({
          status: 'error',
          output: stdout,
          errors: [stderr || error.message],
          duration: Date.now() - startTime,
          evidence: this.evidence
        });
      });

      child.on('close', (code: number | null) => {
        if (finished) return;
        finished = true;
        clearTimeout(timeout);

        const exitCode = code === null ? 1 : code;
        const success = exitCode === 0;

        resolve({
          status: success ? 'success' : 'error',
          output: stdout,
          errors: success ? [] : [stderr || `Exit code: ${exitCode}`],
          duration: Date.now() - startTime,
          evidence: this.evidence
        });
      });
    });
  }

  /**
   * Execute script
   */
  private async executeScript(script: string, workingDir?: string): Promise<ExecutionResult> {
    const cwd = workingDir || this.workingDir;
    const scriptPath = path.resolve(cwd, script);
    const startTime = Date.now();

    if (!fs.existsSync(scriptPath)) {
      return {
        status: 'error',
        output: '',
        errors: [`Script not found: ${scriptPath}`],
        duration: Date.now() - startTime,
        evidence: this.evidence
      };
    }

    return this.executeCommand(scriptPath, [], cwd);
  }

  /**
   * Copy file
   */
  private async copyFile(source: string, destination: string): Promise<ExecutionResult> {
    const sourcePath = path.resolve(this.workingDir, source);
    const destPath = path.resolve(this.workingDir, destination);
    const startTime = Date.now();

    if (!fs.existsSync(sourcePath)) {
      return {
        status: 'error',
        output: '',
        errors: [`Source file not found: ${sourcePath}`],
        duration: Date.now() - startTime,
        evidence: this.evidence
      };
    }

    fs.copyFileSync(sourcePath, destPath);

    return {
      status: 'success',
      output: `Copied ${sourcePath} to ${destPath}`,
      errors: [],
      duration: Date.now() - startTime,
      evidence: this.evidence
    };
  }

  /**
   * Make directory
   */
  private async makeDirectory(dirPath: string): Promise<ExecutionResult> {
    const resolvedPath = path.resolve(this.workingDir, dirPath);
    const startTime = Date.now();

    if (!fs.existsSync(resolvedPath)) {
      fs.mkdirSync(resolvedPath, { recursive: true });
    }

    return {
      status: 'success',
      output: `Created directory: ${resolvedPath}`,
      errors: [],
      duration: Date.now() - startTime,
      evidence: this.evidence
    };
  }

  /**
   * Delete file
   */
  private async deleteFile(filePath: string): Promise<ExecutionResult> {
    const resolvedPath = path.resolve(this.workingDir, filePath);
    const startTime = Date.now();

    if (fs.existsSync(resolvedPath)) {
      fs.unlinkSync(resolvedPath);
    }

    return {
      status: 'success',
      output: `Deleted: ${resolvedPath}`,
      errors: [],
      duration: Date.now() - startTime,
      evidence: this.evidence
    };
  }

  /**
   * Manage service
   */
  private async manageService(service: string, action: string): Promise<ExecutionResult> {
    const command = 'systemctl';
    const args = [action, service];

    return this.executeCommand(command, args);
  }

  /**
   * Execute multiple artifacts
   */
  async executeBatch(
    artifacts: ExecutableArtifact[],
    env: string = 'dev'
  ): Promise<{
    results: ExecutionResult[];
    successes: number;
    failures: number;
  }> {
    const results: ExecutionResult[] = [];
    let successes = 0;
    let failures = 0;

    for (const artifact of artifacts) {
      const result = await this.execute(artifact, env);
      results.push(result);

      if (result.status === 'success') {
        successes++;
      } else {
        failures++;
      }
    }

    return { results, successes, failures };
  }

  /**
   * Get evidence records
   */
  getEvidence(): EvidenceRecord[] {
    return this.evidence;
  }
}