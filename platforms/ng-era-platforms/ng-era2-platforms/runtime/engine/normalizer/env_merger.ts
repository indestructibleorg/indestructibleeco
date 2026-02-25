/**
 * @ECO-governed
 * @ECO-layer: normalizer
 * @ECO-semantic: normalizer-env_merger
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

/**
 * @module env_merger
 * @description Merge environment-specific configuration with base
 * @gl-governed
 * GL Unified Charter Activated
 * @gl-layer ECO-30-EXECUTION
 * @gl-module engine/normalizer
 * @gl-semantic-anchor ECO-30-EXEC-TS
 * @gl-evidence-required true
 * @version 1.0.0
 * @since 2026-01-24
 * @author MachineNativeOps Team
 */

import { EvidenceRecord } from '../interfaces.d';
import type { ConfigObject, EnvMergeResult } from '../types';

/**
 * Environment Merger
 * 
 * GL30-49: Execution Layer - Normalizer Stage
 * 
 * Merges environment-specific configuration with base configuration,
 * following precedence: env overrides > base > defaults.
 */
export class EnvMerger {
  private evidence: EvidenceRecord[] = [];

  /**
   * Merge environment configuration with base configuration
   */
  async merge(
    baseConfig: ConfigObject,
    envConfig: ConfigObject,
    envName: string
  ): Promise<EnvMergeResult> {
    const startTime = Date.now();
    const overrides: string[] = [];
    const errors: string[] = [];

    try {
      // Validate inputs
      if (!baseConfig || typeof baseConfig !== 'object') {
        throw new Error('Base config must be an object');
      }

      if (!envConfig || typeof envConfig !== 'object') {
        throw new Error('Environment config must be an object');
      }

      // Deep merge with override tracking
      const merged = this.deepMerge(baseConfig, envConfig, '', overrides);

      // Generate evidence record
      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'normalizer',
        component: 'env_merger',
        action: 'merge',
        status: 'success',
        input: {
          envName,
          baseKeys: Object.keys(baseConfig),
          envKeys: Object.keys(envConfig)
        },
        output: {
          mergedKeys: Object.keys(merged),
          overrideCount: overrides.length,
          overrides: overrides.slice(0, 10) // Limit in evidence
        },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'success',
        merged,
        changes: overrides,
        errors
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      errors.push(errorMsg);

      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'normalizer',
        component: 'env_merger',
        action: 'merge',
        status: 'error',
        input: { envName },
        output: { error: errorMsg },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'error',
        merged: baseConfig || {},
        changes: overrides,
        errors
      };
    }
  }

  /**
   * Deep merge objects with override tracking
   */
  private deepMerge(
    base: ConfigObject,
    override: ConfigObject,
    path: string,
    overrides: string[]
  ): ConfigObject {
    // If override is null/undefined, use base
    if (override === null || override === undefined) {
      return base;
    }

    // If base is null/undefined or override is not an object, use override
    if (base === null || base === undefined || typeof override !== 'object' || Array.isArray(override)) {
      if (path) {
        overrides.push(path);
      }
      return override;
    }

    // If base is not an object, use override
    if (typeof base !== 'object' || Array.isArray(base)) {
      if (path) {
        overrides.push(path);
      }
      return override;
    }

    // Both are objects, merge recursively
    const merged: ConfigObject = { ...base };

    for (const key in override) {
      const newPath = path ? `${path}.${key}` : key;

      if (key in merged) {
        merged[key] = this.deepMerge(
          merged[key] as ConfigObject,
          override[key] as ConfigObject,
          newPath,
          overrides
        );
      } else {
        merged[key] = override[key];
        overrides.push(newPath);
      }
    }

    return merged;
  }

  /**
   * Merge multiple environment configurations in order
   */
  async mergeMultiple(
    configs: Array<{ config: ConfigObject; name: string }>
  ): Promise<EnvMergeResult> {
    let merged: ConfigObject = {};
    const allOverrides: string[] = [];
    const allErrors: string[] = [];

    for (const { config, name } of configs) {
      const result = await this.merge(merged, config, name);
      merged = result.merged;
      allOverrides.push(...result.changes.map(o => `${name}:${o}`));
      allErrors.push(...result.errors);
    }

    return {
      status: allErrors.length > 0 ? 'error' : 'success',
      merged,
      changes: allOverrides,
      errors: allErrors
    };
  }

  /**
   * Get evidence records
   */
  getEvidence(): EvidenceRecord[] {
    return this.evidence;
  }
}