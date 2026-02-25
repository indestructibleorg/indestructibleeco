/**
 * @ECO-governed
 * @ECO-layer: parser
 * @ECO-semantic: parser-anchor_resolver
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

/**
 * @module anchor_resolver
 * @description YAML anchor and alias resolution
 * @gl-governed
 * GL Unified Charter Activated
 * @gl-layer ECO-30-EXECUTION
 * @gl-module engine/parser
 * @gl-semantic-anchor ECO-30-EXEC-TS
 * @gl-evidence-required true
 * @version 1.0.0
 * @since 2026-01-24
 * @author MachineNativeOps Team
 */

import * as yaml from 'js-yaml';
import { EvidenceRecord } from '../interfaces.d';
import type { ExtractedAnchor, StoredAnchorDefinition } from '../types';

interface AliasUsage {
  name: string;
  line: number;
}

/**
 * Anchor Resolver
 * 
 * GL30-49: Execution Layer - Parser Stage
 * 
 * Resolves YAML anchors and aliases, maintaining complete
 * traceability of anchor definitions and usages.
 */
export class AnchorResolver {
  private evidence: EvidenceRecord[] = [];
  private anchorDefinitions: Map<string, StoredAnchorDefinition> = new Map();
  private anchorUsages: Map<string, string[]> = new Map();

  /**
   * Resolve all anchors in YAML content
   */
  async resolve(content: string, filePath: string): Promise<{
    resolved: string;
    anchorsFound: number;
    aliasesFound: number;
    errors: string[];
  }> {
    const startTime = Date.now();
    const errors: string[] = [];
    let anchorsFound = 0;
    let aliasesFound = 0;

    try {
      // Extract anchor definitions
      const anchorDefs = this.extractAnchors(content);
      anchorsFound = anchorDefs.length;

      // Store anchor definitions for tracking
      for (const def of anchorDefs) {
        this.anchorDefinitions.set(def.name, {
          filePath,
          value: def.value
        });

        this.evidence.push({
          timestamp: new Date().toISOString(),
          stage: 'parser',
          component: 'anchor_resolver',
          action: 'anchor_found',
          status: 'success',
          input: { path: filePath, anchor: def.name },
          output: { line: def.line },
          metrics: {}
        });
      }

      // Extract alias usages
      const aliasUsages = this.extractAliases(content);
      aliasesFound = aliasUsages.length;

      // Track alias usages
      for (const alias of aliasUsages) {
        if (!this.anchorUsages.has(alias.name)) {
          this.anchorUsages.set(alias.name, []);
        }
        this.anchorUsages.get(alias.name)!.push(`${filePath}:${alias.line}`);

        this.evidence.push({
          timestamp: new Date().toISOString(),
          stage: 'parser',
          component: 'anchor_resolver',
          action: 'alias_found',
          status: 'success',
          input: { path: filePath, alias: alias.name },
          output: { line: alias.line },
          metrics: {}
        });
      }

      // Validate that all aliases have corresponding anchors
      const validationErrors = this.validateAnchorsAndAliases(anchorDefs, aliasUsages);
      errors.push(...validationErrors);

      // Parse and resolve anchors
      const resolvedObj = yaml.load(content, {
        schema: yaml.DEFAULT_SCHEMA
      });

      if (resolvedObj === null || typeof resolvedObj !== 'object') {
        throw new Error('Resolved content is not an object');
      }

      // Dump back to YAML
      const resolved = yaml.dump(resolvedObj, {
        indent: 2,
        lineWidth: -1,
        noRefs: true // Don't keep references, fully resolve them
      });

      // Generate evidence record
      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'parser',
        component: 'anchor_resolver',
        action: 'resolve',
        status: errors.length > 0 ? 'warning' : 'success',
        input: { path: filePath },
        output: {
          anchorsFound,
          aliasesFound,
          originalSize: content.length,
          resolvedSize: resolved.length,
          errors: errors.length
        },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        resolved,
        anchorsFound,
        aliasesFound,
        errors
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      errors.push(errorMsg);

      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'parser',
        component: 'anchor_resolver',
        action: 'resolve',
        status: 'error',
        input: { path: filePath },
        output: { error: errorMsg },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        resolved: content,
        anchorsFound,
        aliasesFound,
        errors
      };
    }
  }

  /**
   * Extract anchor definitions from YAML content
   */
  private extractAnchors(content: string): ExtractedAnchor[] {
    const anchors: ExtractedAnchor[] = [];
    const lines = content.split('\n');
    const anchorRegex = /^(\s*)&([a-zA-Z_][a-zA-Z0-9_-]*)/;

    for (let i = 0; i < lines.length; i++) {
      const match = lines[i].match(anchorRegex);
      if (match) {
        anchors.push({
          name: match[2],
          line: i + 1,
          value: null // Would need full parsing to get value
        });
      }
    }

    return anchors;
  }

  /**
   * Extract alias usages from YAML content
   */
  private extractAliases(content: string): AliasUsage[] {
    const aliases: AliasUsage[] = [];
    const lines = content.split('\n');
    const aliasRegex = /\*([a-zA-Z_][a-zA-Z0-9_-]*)/g;

    for (let i = 0; i < lines.length; i++) {
      let match;
      while ((match = aliasRegex.exec(lines[i])) !== null) {
        aliases.push({
          name: match[1],
          line: i + 1
        });
      }
    }

    return aliases;
  }

  /**
   * Validate that all aliases have corresponding anchors
   */
  private validateAnchorsAndAliases(
    anchors: ExtractedAnchor[],
    aliases: AliasUsage[]
  ): string[] {
    const errors: string[] = [];
    const anchorNames = new Set(anchors.map(a => a.name));

    for (const alias of aliases) {
      if (!anchorNames.has(alias.name)) {
        errors.push(`Undefined anchor referenced: *${alias.name}`);
      }
    }

    // Check for unused anchors
    const usedAnchors = new Set(aliases.map(a => a.name));
    for (const anchor of anchors) {
      if (!usedAnchors.has(anchor.name)) {
        // Warning, not error
        this.evidence.push({
          timestamp: new Date().toISOString(),
          stage: 'parser',
          component: 'anchor_resolver',
          action: 'warning',
          status: 'warning',
          input: { anchor: anchor.name },
          output: { message: 'Unused anchor definition' },
          metrics: {}
        });
      }
    }

    return errors;
  }

  /**
   * Get all anchor definitions
   */
  getAnchorDefinitions(): Map<string, StoredAnchorDefinition> {
    return this.anchorDefinitions;
  }

  /**
   * Get all anchor usages
   */
  getAnchorUsages(): Map<string, string[]> {
    return this.anchorUsages;
  }

  /**
   * Get evidence records
   */
  getEvidence(): EvidenceRecord[] {
    return this.evidence;
  }
}