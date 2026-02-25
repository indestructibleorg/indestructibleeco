/**
 * @ECO-governed
 * @ECO-layer: parser
 * @ECO-semantic: parser-yaml_parser
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

/**
 * @module yaml_parser
 * @description YAML parser with schema validation
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
import { ParserInterface, ParseResult, EvidenceRecord } from '../interfaces.d';

/**
 * YAML Parser
 * 
 * GL30-49: Execution Layer - Parser Stage
 * 
 * Parses YAML files with comprehensive error handling,
 * schema validation, and evidence chain generation.
 */
export class YamlParser implements ParserInterface {
  private evidence: EvidenceRecord[] = [];

  /**
   * Parse YAML content to JavaScript object
   */
  async parse(content: string, filePath: string): Promise<ParseResult> {
    const startTime = Date.now();

    try {
      // Parse YAML with anchors and aliases resolution
      const parsed = yaml.load(content, {
        schema: yaml.DEFAULT_SCHEMA,
        onWarning: (warning) => {
          this.evidence.push({
            timestamp: new Date().toISOString(),
            stage: 'parser',
            component: 'yaml_parser',
            action: 'warning',
            status: 'warning',
            input: { path: filePath },
            output: { warning: warning.message },
            metrics: {}
          });
        }
      });

      if (parsed === undefined || parsed === null) {
        throw new Error('YAML content is empty or invalid');
      }

      // Validate parsed object
      if (typeof parsed !== 'object') {
        throw new Error('YAML must parse to an object, got ' + typeof parsed);
      }

      // Generate evidence record
      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'parser',
        component: 'yaml_parser',
        action: 'parse',
        status: 'success',
        input: { path: filePath, size: content.length },
        output: {
          type: typeof parsed,
          keys: Object.keys(parsed),
          hasAnchors: content.includes('&') || content.includes('*')
        },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'success',
        data: parsed,
        errors: [],
        evidence: this.evidence
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);

      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'parser',
        component: 'yaml_parser',
        action: 'parse',
        status: 'error',
        input: { path: filePath },
        output: { error: errorMsg },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'error',
        data: null,
        errors: [errorMsg],
        evidence: this.evidence
      };
    }
  }

  /**
   * Parse multiple YAML files
   */
  async parseBatch(files: Map<string, { content: string }>): Promise<Map<string, ParseResult>> {
    const results: Map<string, ParseResult> = new Map();

    for (const [path, file] of files.entries()) {
      const result = await this.parse(file.content, path);
      results.set(path, result);
    }

    return results;
  }

  /**
   * Validate YAML content before parsing
   */
  validate(content: string): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    try {
      yaml.load(content);
      return { valid: true, errors };
    } catch (error) {
      errors.push(error instanceof Error ? error.message : String(error));
      return { valid: false, errors };
    }
  }

  /**
   * Get evidence records
   */
  getEvidence(): EvidenceRecord[] {
    return this.evidence;
  }
}