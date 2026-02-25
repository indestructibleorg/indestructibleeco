/**
 * @ECO-governed
 * @ECO-layer: normalizer
 * @ECO-semantic: normalizer-module_defaults
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

/**
 * @module module_defaults
 * @description Apply module-level default configurations
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
import type { ConfigObject, ModuleDefaultsResult } from '../types';

/**
 * Module Defaults
 * 
 * GL30-49: Execution Layer - Normalizer Stage
 * 
 * Applies module-level default configurations based on
 * module manifests and system-wide defaults.
 */
export class ModuleDefaults {
  private evidence: EvidenceRecord[] = [];
  private readonly moduleRegistry: Map<string, ConfigObject> = new Map();

  constructor(moduleDefaults?: Map<string, ConfigObject>) {
    if (moduleDefaults) {
      this.moduleRegistry = moduleDefaults;
    }
  }

  /**
   * Register module defaults
   */
  registerModule(moduleName: string, defaults: ConfigObject): void {
    this.moduleRegistry.set(moduleName, defaults);
  }

  /**
   * Apply module defaults to configuration
   */
  async apply(
    config: ConfigObject,
    moduleName: string
  ): Promise<ModuleDefaultsResult> {
    const startTime = Date.now();
    const appliedDefaults: string[] = [];
    const errors: string[] = [];

    try {
      // Validate inputs
      if (!config || typeof config !== 'object') {
        throw new Error('Config must be an object');
      }

      if (!moduleName) {
        throw new Error('Module name is required');
      }

      // Get module defaults
      const moduleDefaults = this.moduleRegistry.get(moduleName);

      if (!moduleDefaults) {
        this.evidence.push({
          timestamp: new Date().toISOString(),
          stage: 'normalizer',
          component: 'module_defaults',
          action: 'apply',
          status: 'warning',
          input: { moduleName },
          output: { message: 'No defaults found for module' },
          metrics: { duration: Date.now() - startTime }
        });

        return {
          status: 'warning',
          applied: config,
          modulesApplied: [],
          errors: ['No defaults found for module: ' + moduleName]
        };
      }

      // Apply defaults
      const applied = this.applyModuleDefaults(config, moduleDefaults, moduleName, appliedDefaults);

      // Generate evidence record
      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'normalizer',
        component: 'module_defaults',
        action: 'apply',
        status: 'success',
        input: { moduleName, defaultKeys: Object.keys(moduleDefaults) },
        output: {
          appliedKeys: Object.keys(applied),
          appliedCount: appliedDefaults.length
        },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'success',
        applied,
        modulesApplied: [moduleName],
        errors
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      errors.push(errorMsg);

      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'normalizer',
        component: 'module_defaults',
        action: 'apply',
        status: 'error',
        input: { moduleName },
        output: { error: errorMsg },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'error',
        applied: config || {},
        modulesApplied: [],
        errors
      };
    }
  }

  /**
   * Apply module defaults recursively
   */
  private applyModuleDefaults(
    config: ConfigObject,
    defaults: ConfigObject,
    modulePath: string,
    appliedDefaults: string[]
  ): ConfigObject {
    const result: ConfigObject = { ...config };

    for (const key in defaults) {
      const defaultValue = defaults[key];
      const currentValue = config[key];
      const path = `${modulePath}.${key}`;

      // Skip if value already exists
      if (currentValue !== null && currentValue !== undefined) {
        // Recursively apply defaults for nested objects
        if (
          typeof defaultValue === 'object' &&
          !Array.isArray(defaultValue) &&
          typeof currentValue === 'object' &&
          !Array.isArray(currentValue)
        ) {
          result[key] = this.applyModuleDefaults(
            currentValue as ConfigObject,
            defaultValue as ConfigObject,
            path,
            appliedDefaults
          );
        }
        continue;
      }

      // Apply default value
      result[key] = defaultValue;
      appliedDefaults.push(path);
    }

    return result;
  }

  /**
   * Apply defaults to multiple modules
   */
  async applyBatch(
    config: ConfigObject,
    modules: Map<string, ConfigObject>
  ): Promise<{
    applied: ConfigObject;
    appliedDefaults: Map<string, string[]>;
    errors: string[];
  }> {
    const allAppliedDefaults: Map<string, string[]> = new Map();
    const allErrors: string[] = [];
    const applied: ConfigObject = { ...config };

    for (const [moduleName, moduleConfig] of modules.entries()) {
      // Register module defaults if not already registered
      if (!this.moduleRegistry.has(moduleName)) {
        this.registerModule(moduleName, {});
      }

      // Apply defaults
      const result = await this.apply(moduleConfig, moduleName);
      applied[moduleName] = result.applied;
      allAppliedDefaults.set(moduleName, result.modulesApplied);
      allErrors.push(...result.errors);
    }

    return {
      applied,
      appliedDefaults: allAppliedDefaults,
      errors: allErrors
    };
  }

  /**
   * Get registered module defaults
   */
  getModuleDefaults(moduleName: string): ConfigObject | undefined {
    return this.moduleRegistry.get(moduleName);
  }

  /**
   * Get all registered modules
   */
  getRegisteredModules(): string[] {
    return Array.from(this.moduleRegistry.keys());
  }

  /**
   * Get evidence records
   */
  getEvidence(): EvidenceRecord[] {
    return this.evidence;
  }
}