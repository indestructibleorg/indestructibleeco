/**
 * @ECO-governed
 * @ECO-layer: renderer
 * @ECO-semantic: renderer-module_mapper
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

/**
 * @module module_mapper
 * @description Map module configurations to artifacts
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

import { EvidenceRecord } from '../interfaces.d';
import type { ConfigObject, MappedArtifact, ModuleManifest, ModuleMappingResult } from '../types';

interface TemplateDefinition {
  name: string;
  type?: string;
  path: string;
  output: string;
}

interface ModuleManifestWithTemplates extends ModuleManifest {
  templates?: TemplateDefinition[];
}

/**
 * Module Mapper
 * 
 * GL30-49: Execution Layer - Renderer Stage
 * 
 * Maps module configurations to artifacts, handling
 * dependencies, ordering, and resource allocation.
 */
export class ModuleMapper {
  private evidence: EvidenceRecord[] = [];
  private readonly moduleRegistry: Map<string, ModuleManifestWithTemplates> = new Map();
  private readonly dependencyGraph: Map<string, string[]> = new Map();

  constructor() {
    // Initialize with default module mappings
  }

  /**
   * Map modules to artifacts
   */
  async mapModules(
    modules: Map<string, ConfigObject>,
    config: ConfigObject
  ): Promise<ModuleMappingResult> {
    const startTime = Date.now();
    const artifacts: MappedArtifact[] = [];
    const errors: string[] = [];

    try {
      // Resolve module order based on dependencies
      const orderedModules = this.resolveDependencies(modules);

      // Map each module to artifacts
      for (const [moduleName, moduleConfig] of orderedModules.entries()) {
        try {
          const moduleArtifacts = await this.mapModule(moduleName, moduleConfig, config);
          artifacts.push(...moduleArtifacts);
        } catch (error) {
          errors.push(
            `Failed to map module ${moduleName}: ${error instanceof Error ? error.message : String(error)}`
          );
        }
      }

      // Generate evidence record
      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'renderer',
        component: 'module_mapper',
        action: 'map_modules',
        status: errors.length > 0 ? 'warning' : 'success',
        input: { moduleCount: modules.size },
        output: {
          artifactCount: artifacts.length,
          errorCount: errors.length
        },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: errors.length > 0 ? 'warning' : 'success',
        artifacts,
        errors
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      errors.push(errorMsg);

      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'renderer',
        component: 'module_mapper',
        action: 'map_modules',
        status: 'error',
        input: {},
        output: { error: errorMsg },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'error',
        artifacts,
        errors
      };
    }
  }

  /**
   * Map single module to artifacts
   */
  private async mapModule(
    moduleName: string,
    moduleConfig: ConfigObject,
    globalConfig: ConfigObject
  ): Promise<MappedArtifact[]> {
    const artifacts: MappedArtifact[] = [];

    // Get module manifest
    const manifest = this.moduleRegistry.get(moduleName);
    
    if (!manifest) {
      throw new Error(`Module manifest not found: ${moduleName}`);
    }

    // Map templates from manifest
    if (manifest.templates) {
      for (const template of manifest.templates) {
        const artifact: MappedArtifact = {
          moduleId: moduleName,
          artifactId: `${moduleName}-${template.name}`,
          type: template.type || 'config',
          data: this.mergeConfigs(moduleConfig, globalConfig),
          metadata: {
            template: template.path,
            output: template.output,
            dependencies: (moduleConfig.dependencies as string[]) || []
          }
        };

        artifacts.push(artifact);
      }
    }

    return artifacts;
  }

  /**
   * Resolve module dependencies
   */
  private resolveDependencies(modules: Map<string, ConfigObject>): Map<string, ConfigObject> {
    const resolved: Map<string, ConfigObject> = new Map();
    const unresolved: Map<string, ConfigObject> = new Map(modules);
    const resolvedSet = new Set<string>();

    // Build dependency graph
    for (const [name, config] of modules.entries()) {
      const deps = (config.dependencies as string[]) || [];
      this.dependencyGraph.set(name, deps);
    }

    // Topological sort
    let iterations = 0;
    const maxIterations = modules.size * 2; // Prevent infinite loops

    while (unresolved.size > 0 && iterations < maxIterations) {
      let progress = false;

      for (const [name, config] of unresolved.entries()) {
        const deps = this.dependencyGraph.get(name) || [];
        
        // Check if all dependencies are resolved
        const allDepsResolved = deps.every((dep: string) => resolvedSet.has(dep));

        if (allDepsResolved) {
          resolved.set(name, config);
          resolvedSet.add(name);
          unresolved.delete(name);
          progress = true;
        }
      }

      if (!progress) {
        // Circular dependency detected
        const remaining = Array.from(unresolved.keys());
        throw new Error(`Circular dependency detected in modules: ${remaining.join(', ')}`);
      }

      iterations++;
    }

    return resolved;
  }

  /**
   * Merge module config with global config
   */
  private mergeConfigs(moduleConfig: ConfigObject, globalConfig: ConfigObject): ConfigObject {
    return {
      ...globalConfig,
      module: moduleConfig,
      globals: {
        env: globalConfig.env || 'dev',
        timestamp: new Date().toISOString()
      }
    };
  }

  /**
   * Register module manifest
   */
  registerModule(name: string, manifest: ModuleManifestWithTemplates): void {
    this.moduleRegistry.set(name, manifest);
  }

  /**
   * Get module manifest
   */
  getModule(name: string): ModuleManifestWithTemplates | undefined {
    return this.moduleRegistry.get(name);
  }

  /**
   * Get evidence records
   */
  getEvidence(): EvidenceRecord[] {
    return this.evidence;
  }
}