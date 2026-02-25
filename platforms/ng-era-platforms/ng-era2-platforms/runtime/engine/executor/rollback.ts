/**
 * @ECO-governed
 * @ECO-layer: executor
 * @ECO-semantic: executor-rollback
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

/**
 * @module rollback
 * @description Rollback operations with state tracking and backup
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

import { EvidenceRecord } from '../interfaces.d';
import * as fs from 'fs';
import * as path from 'path';
import type { BackupEntry } from '../types';

interface BackupRecord {
  backupId: string;
  paths: string[];
  timestamp: string;
}

/**
 * Rollback Manager
 * 
 * GL30-49: Execution Layer - Executor Stage
 * 
 * Manages rollback operations with state tracking,
 * backup creation, and verification.
 */
export class RollbackManager {
  private evidence: EvidenceRecord[] = [];
  private readonly backupDir: string;
  private readonly executionHistory: Map<string, BackupRecord[]> = new Map();

  constructor(options?: {
    backupDir?: string;
  }) {
    this.backupDir = options?.backupDir || './backups';
    this.ensureDirectoryExists(this.backupDir);
  }

  /**
   * Create backup before execution
   */
  async createBackup(
    artifactId: string,
    paths: string[]
  ): Promise<{
    success: boolean;
    backupId: string;
    errors: string[];
  }> {
    const startTime = Date.now();
    const backupId = `${artifactId}_${Date.now()}`;
    const errors: string[] = [];

    try {
      // Create backup directory
      const backupPath = path.join(this.backupDir, backupId);
      fs.mkdirSync(backupPath, { recursive: true });

      // Backup each path
      for (const filePath of paths) {
        try {
          const resolvedPath = path.resolve(filePath);
          
          if (fs.existsSync(resolvedPath)) {
            const backupFilePath = path.join(backupPath, path.basename(filePath));
            fs.copyFileSync(resolvedPath, backupFilePath);
          }
        } catch (error) {
          errors.push(
            `Failed to backup ${filePath}: ${error instanceof Error ? error.message : String(error)}`
          );
        }
      }

      // Record backup
      this.recordBackup(artifactId, backupId, paths);

      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'executor',
        component: 'rollback',
        action: 'create_backup',
        status: errors.length > 0 ? 'warning' : 'success',
        input: { artifactId, paths },
        output: {
          backupId,
          errorCount: errors.length
        },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        success: errors.length === 0,
        backupId,
        errors
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      errors.push(errorMsg);

      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'executor',
        component: 'rollback',
        action: 'create_backup',
        status: 'error',
        input: { artifactId },
        output: { error: errorMsg },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        success: false,
        backupId: '',
        errors
      };
    }
  }

  /**
   * Rollback execution
   */
  async rollback(
    artifactId: string,
    backupId?: string
  ): Promise<{
    success: boolean;
    restoredPaths: string[];
    errors: string[];
  }> {
    const startTime = Date.now();
    const restoredPaths: string[] = [];
    const errors: string[] = [];

    try {
      // Get backup ID
      const targetBackupId = backupId || this.getLatestBackupId(artifactId);

      if (!targetBackupId) {
        throw new Error(`No backup found for artifact: ${artifactId}`);
      }

      // Get backup metadata
      const backup = this.getBackup(artifactId, targetBackupId);

      if (!backup) {
        throw new Error(`Backup not found: ${targetBackupId}`);
      }

      // Restore files from backup
      const backupPath = path.join(this.backupDir, targetBackupId);

      for (const originalPath of backup.paths) {
        try {
          const backupFilePath = path.join(backupPath, path.basename(originalPath));
          const resolvedPath = path.resolve(originalPath);

          if (fs.existsSync(backupFilePath)) {
            fs.copyFileSync(backupFilePath, resolvedPath);
            restoredPaths.push(resolvedPath);
          }
        } catch (error) {
          errors.push(
            `Failed to restore ${originalPath}: ${error instanceof Error ? error.message : String(error)}`
          );
        }
      }

      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'executor',
        component: 'rollback',
        action: 'rollback',
        status: errors.length > 0 ? 'warning' : 'success',
        input: { artifactId, backupId: targetBackupId },
        output: {
          restoredCount: restoredPaths.length,
          errorCount: errors.length
        },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        success: errors.length === 0,
        restoredPaths,
        errors
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      errors.push(errorMsg);

      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'executor',
        component: 'rollback',
        action: 'rollback',
        status: 'error',
        input: { artifactId },
        output: { error: errorMsg },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        success: false,
        restoredPaths,
        errors
      };
    }
  }

  /**
   * Record backup
   */
  private recordBackup(
    artifactId: string,
    backupId: string,
    paths: string[]
  ): void {
    if (!this.executionHistory.has(artifactId)) {
      this.executionHistory.set(artifactId, []);
    }

    this.executionHistory.get(artifactId)!.push({
      backupId,
      paths,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Get backup
   */
  private getBackup(artifactId: string, backupId: string): BackupRecord | null {
    const history = this.executionHistory.get(artifactId);

    if (!history) {
      return null;
    }

    return history.find(b => b.backupId === backupId) || null;
  }

  /**
   * Get latest backup ID
   */
  private getLatestBackupId(artifactId: string): string | undefined {
    const history = this.executionHistory.get(artifactId);

    if (!history || history.length === 0) {
      return undefined;
    }

    return history[history.length - 1].backupId;
  }

  /**
   * List backups for artifact
   */
  listBackups(artifactId: string): BackupRecord[] {
    return this.executionHistory.get(artifactId) || [];
  }

  /**
   * Delete old backups
   */
  async cleanupOldBackups(
    artifactId: string,
    keepCount: number = 5
  ): Promise<{
    deleted: string[];
    errors: string[];
  }> {
    const backups = this.listBackups(artifactId);
    const deleted: string[] = [];
    const errors: string[] = [];

    if (backups.length <= keepCount) {
      return { deleted, errors };
    }

    // Delete old backups
    const toDelete = backups.slice(0, backups.length - keepCount);

    for (const backup of toDelete) {
      try {
        const backupPath = path.join(this.backupDir, backup.backupId);
        
        if (fs.existsSync(backupPath)) {
          fs.rmSync(backupPath, { recursive: true });
        }

        deleted.push(backup.backupId);
      } catch (error) {
        errors.push(
          `Failed to delete backup ${backup.backupId}: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }

    // Update history
    const remaining = backups.slice(backups.length - keepCount);
    this.executionHistory.set(artifactId, remaining);

    return { deleted, errors };
  }

  /**
   * Ensure directory exists
   */
  private ensureDirectoryExists(dirPath: string): void {
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }
  }

  /**
   * Get evidence records
   */
  getEvidence(): EvidenceRecord[] {
    return this.evidence;
  }
}