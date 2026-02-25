/**
 * @ECO-governed
 * @ECO-layer: normalizer
 * @ECO-semantic: normalizer-defaults_applier
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

/**
 * @module defaults_applier
 * @description Apply default values to configuration
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
import type { ConfigObject, DefaultsApplicationResult } from '../types';

/**
 * Defaults Applier
 * 
 * GL30-49: Execution Layer - Normalizer Stage
 * 
 * Applies default values to configuration, respecting
 * existing values and schema-defined defaults.
 */
export class DefaultsApplier {
  private evidence: EvidenceRecord[] = [];

  /**
   * Apply defaults to configuration
   */
  async apply(
    config: ConfigObject,
    defaults: ConfigObject,
    overwrite: boolean = false
  ): Promise<DefaultsApplicationResult> {
    const startTime = Date.now();
    const appliedDefaults: string[] = [];
    const errors: string[] = [];

    try {
      // Validate inputs
      if (!config || typeof config !== 'object') {
        throw new Error('Config must be an object');
      }

      if (!defaults || typeof defaults !== 'object') {
        throw new Error('Defaults must be an object');
      }

      // Apply defaults with tracking
      const applied = this.applyDefaults(config, defaults, '', appliedDefaults, overwrite);

      // Generate evidence record
      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'normalizer',
        component: 'defaults_applier',
        action: 'apply',
        status: 'success',
        input: {
          configKeys: Object.keys(config),
          defaultKeys: Object.keys(defaults),
          overwrite
        },
        output: {
          appliedKeys: Object.keys(applied),
          appliedCount: appliedDefaults.length
        },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'success',
        applied,
        changes: appliedDefaults,
        errors
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      errors.push(errorMsg);

      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'normalizer',
        component: 'defaults_applier',
        action: 'apply',
        status: 'error',
        input: { overwrite },
        output: { error: errorMsg },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'error',
        applied: config || {},
        changes: appliedDefaults,
        errors
      };
    }
  }

  /**
   * Recursively apply defaults
   */
  private applyDefaults(
    config: ConfigObject,
    defaults: ConfigObject,
    path: string,
    appliedDefaults: string[],
    overwrite: boolean
  ): ConfigObject {
    const result: ConfigObject = { ...config };

    for (const key in defaults) {
      const newPath = path ? `${path}.${key}` : key;
      const defaultValue = defaults[key];
      const currentValue = config[key];

      // Handle null/undefined values
      if (currentValue === null || currentValue === undefined) {
        result[key] = defaultValue;
        appliedDefaults.push(newPath);
        continue;
      }

      // Handle object values
      if (typeof defaultValue === 'object' && !Array.isArray(defaultValue)) {
        if (typeof currentValue === 'object' && !Array.isArray(currentValue)) {
          result[key] = this.applyDefaults(
            currentValue as ConfigObject,
            defaultValue as ConfigObject,
            newPath,
            appliedDefaults,
            overwrite
          );
        } else if (overwrite) {
          result[key] = defaultValue;
          appliedDefaults.push(newPath);
        }
        continue;
      }

      // Handle array values
      if (Array.isArray(defaultValue)) {
        if (Array.isArray(currentValue)) {
          result[key] = currentValue;
        } else if (overwrite) {
          result[key] = defaultValue;
          appliedDefaults.push(newPath);
        }
        continue;
      }

      // Handle scalar values
      if (overwrite) {
        result[key] = defaultValue;
        appliedDefaults.push(newPath);
      }
    }

    return result;
  }

  /**
   * Apply defaults based on schema
   */
  async applyFromSchema(
    config: ConfigObject,
    schema: ConfigObject
  ): Promise<DefaultsApplicationResult> {
    const startTime = Date.now();
    const appliedDefaults: string[] = [];
    const errors: string[] = [];

    try {
      // Extract defaults from JSON Schema
      const defaults = this.extractDefaultsFromSchema(schema);

      // Apply defaults
      const result = await this.apply(config, defaults, false);

      return {
        status: result.status,
        applied: result.applied,
        changes: result.changes,
        errors
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      errors.push(errorMsg);

      return {
        status: 'error',
        applied: config || {},
        changes: appliedDefaults,
        errors
      };
    }
  }

  /**
   * Extract default values from JSON Schema
   */
  private extractDefaultsFromSchema(schema: ConfigObject): ConfigObject {
    const defaults: ConfigObject = {};

    if (!schema || typeof schema !== 'object') {
      return defaults;
    }

    // Handle top-level default
    if ('default' in schema) {
      return schema.default as ConfigObject;
    }

    // Handle properties
    const properties = schema.properties as ConfigObject | undefined;
    if (properties) {
      for (const key in properties) {
        const propertySchema = properties[key] as ConfigObject;

        if ('default' in propertySchema) {
          defaults[key] = propertySchema.default;
        } else if (propertySchema.type === 'object' && propertySchema.properties) {
          defaults[key] = this.extractDefaultsFromSchema(propertySchema);
        }
      }
    }

    return defaults;
  }

  /**
   * Get evidence records
   */
  getEvidence(): EvidenceRecord[] {
    return this.evidence;
  }
}