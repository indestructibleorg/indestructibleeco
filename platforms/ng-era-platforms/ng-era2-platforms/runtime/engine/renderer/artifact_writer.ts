/**
 * @ECO-governed
 * @ECO-layer: renderer
 * @ECO-semantic: renderer-artifact_writer
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

/**
 * @module artifact_writer
 * @description Write rendered artifacts with integrity verification
 * @gl-governed
 * GL Unified Charter Activated
 * @gl-layer ECO-30-EXECUTION
 * @gl-module engine/renderer
 * @gl-semantic-anchor ECO-30-EXEC-TS
 * @gl-evidence-required true
 * @version 1.0.0
 * @since 2026-01-24
 * @author MachineNativeOps Team
 */

import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';
import { EvidenceRecord } from '../interfaces.d';
import type { ArtifactMetadata, ArtifactWriteOptions } from '../types';

interface StoredArtifact {
  id: string;
  path: string;
  fullPath: string;
  hash: string;
  size: number;
  modified: string;
  created: string;
  metadata?: ArtifactMetadata;
}

interface ArtifactManifest {
  timestamp: string;
  outputDir: string;
  artifactCount: number;
  artifacts: StoredArtifact[];
}

/**
 * Artifact Writer
 * 
 * GL30-49: Execution Layer - Renderer Stage
 * 
 * Writes rendered artifacts to filesystem with hash-based
 * integrity verification and evidence chain generation.
 */
export class ArtifactWriter {
  private evidence: EvidenceRecord[] = [];
  private readonly outputDir: string;
  private readonly artifacts: Map<string, StoredArtifact> = new Map();

  constructor(outputDir: string = './artifacts') {
    this.outputDir = path.resolve(outputDir);
    this.ensureDirectoryExists(this.outputDir);
  }

  /**
   * Write artifact to filesystem
   */
  async write(
    artifactId: string,
    content: string,
    outputPath: string,
    metadata?: ArtifactMetadata
  ): Promise<{
    success: boolean;
    path: string;
    hash: string;
    size: number;
    errors: string[];
  }> {
    const startTime = Date.now();
    const errors: string[] = [];

    try {
      // Resolve output path
      const resolvedPath = path.resolve(this.outputDir, outputPath);

      // Ensure directory exists
      this.ensureDirectoryExists(path.dirname(resolvedPath));

      // Generate hash
      const hash = this.generateHash(content);

      // Write file
      fs.writeFileSync(resolvedPath, content, 'utf-8');

      // Get file stats
      const stats = fs.statSync(resolvedPath);

      // Store artifact metadata
      const artifact: StoredArtifact = {
        id: artifactId,
        path: outputPath,
        fullPath: resolvedPath,
        hash,
        size: stats.size,
        modified: stats.mtime.toISOString(),
        created: stats.birthtime.toISOString(),
        metadata
      };

      this.artifacts.set(artifactId, artifact);

      // Generate evidence record
      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'renderer',
        component: 'artifact_writer',
        action: 'write',
        status: 'success',
        input: { artifactId, outputPath },
        output: {
          hash,
          size: stats.size,
          path: resolvedPath
        },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        success: true,
        path: resolvedPath,
        hash,
        size: stats.size,
        errors: []
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      errors.push(errorMsg);

      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'renderer',
        component: 'artifact_writer',
        action: 'write',
        status: 'error',
        input: { artifactId, outputPath },
        output: { error: errorMsg },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        success: false,
        path: '',
        hash: '',
        size: 0,
        errors
      };
    }
  }

  /**
   * Write multiple artifacts
   */
  async writeBatch(
    artifacts: ArtifactWriteOptions[]
  ): Promise<{
    successes: number;
    failures: number;
    results: Map<string, { success: boolean; path: string; hash: string; size: number; errors: string[] }>;
  }> {
    let successes = 0;
    let failures = 0;
    const results = new Map<string, { success: boolean; path: string; hash: string; size: number; errors: string[] }>();

    for (const artifact of artifacts) {
      const result = await this.write(artifact.artifactId, artifact.content, artifact.outputPath, artifact.metadata);
      
      if (result.success) {
        successes++;
      } else {
        failures++;
      }

      results.set(artifact.artifactId, result);
    }

    return { successes, failures, results };
  }

  /**
   * Verify artifact integrity
   */
  async verify(
    artifactId: string
  ): Promise<{
    valid: boolean;
    currentHash: string;
    storedHash: string;
  }> {
    const artifact = this.artifacts.get(artifactId);

    if (!artifact) {
      return { valid: false, currentHash: '', storedHash: '' };
    }

    if (!fs.existsSync(artifact.fullPath)) {
      return { valid: false, currentHash: '', storedHash: artifact.hash };
    }

    const content = fs.readFileSync(artifact.fullPath, 'utf-8');
    const currentHash = this.generateHash(content);

    return {
      valid: currentHash === artifact.hash,
      currentHash,
      storedHash: artifact.hash
    };
  }

  /**
   * Delete artifact
   */
  async delete(artifactId: string): Promise<boolean> {
    const artifact = this.artifacts.get(artifactId);

    if (!artifact) {
      return false;
    }

    try {
      if (fs.existsSync(artifact.fullPath)) {
        fs.unlinkSync(artifact.fullPath);
      }
      this.artifacts.delete(artifactId);
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get artifact metadata
   */
  getArtifact(artifactId: string): StoredArtifact | undefined {
    return this.artifacts.get(artifactId);
  }

  /**
   * Get all artifacts
   */
  getAllArtifacts(): Map<string, StoredArtifact> {
    return new Map(this.artifacts);
  }

  /**
   * Generate artifact manifest
   */
  generateManifest(): ArtifactManifest {
    return {
      timestamp: new Date().toISOString(),
      outputDir: this.outputDir,
      artifactCount: this.artifacts.size,
      artifacts: Array.from(this.artifacts.values())
    };
  }

  /**
   * Generate SHA256 hash
   */
  private generateHash(content: string): string {
    return crypto.createHash('sha256').update(content).digest('hex');
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