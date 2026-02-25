/**
 * @ECO-governed
 * @ECO-layer: parser
 * @ECO-semantic: parser-json_passthrough
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

/**
 * @module json_passthrough
 * @description JSON parsing with validation and passthrough
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

import { ParserInterface, ParseResult, EvidenceRecord } from '../interfaces.d';
import type { ConfigObject } from '../types';

/**
 * JSON Passthrough Parser
 * 
 * GL30-49: Execution Layer - Parser Stage
 * 
 * Parses JSON files with validation and error handling.
 * Provides passthrough functionality for pre-parsed JSON data.
 */
export class JsonPassthroughParser implements ParserInterface {
  private evidence: EvidenceRecord[] = [];

  /**
   * Parse JSON content to JavaScript object
   */
  async parse(content: string, filePath: string): Promise<ParseResult> {
    const startTime = Date.now();

    try {
      // Parse JSON
      const parsed = JSON.parse(content) as ConfigObject;

      // Validate parsed object
      if (parsed === null || typeof parsed !== 'object') {
        throw new Error('JSON must parse to an object, got ' + typeof parsed);
      }

      // Generate evidence record
      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'parser',
        component: 'json_passthrough',
        action: 'parse',
        status: 'success',
        input: { path: filePath, size: content.length },
        output: {
          type: typeof parsed,
          keys: Object.keys(parsed),
          isEmpty: Object.keys(parsed).length === 0
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
        component: 'json_passthrough',
        action: 'parse',
        status: 'error',
        input: { path: filePath },
        output: { error: errorMsg },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'error',
        data: {},
        errors: [errorMsg],
        evidence: this.evidence
      };
    }
  }

  /**
   * Passthrough method for already parsed JSON objects
   */
  passthrough(data: ConfigObject, filePath: string): ParseResult {
    const startTime = Date.now();

    try {
      if (data === null || typeof data !== 'object') {
        throw new Error('Data must be an object, got ' + typeof data);
      }

      // Generate evidence record
      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'parser',
        component: 'json_passthrough',
        action: 'passthrough',
        status: 'success',
        input: { path: filePath },
        output: {
          type: typeof data,
          keys: Object.keys(data)
        },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'success',
        data,
        errors: [],
        evidence: this.evidence
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);

      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'parser',
        component: 'json_passthrough',
        action: 'passthrough',
        status: 'error',
        input: { path: filePath },
        output: { error: errorMsg },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'error',
        data: {},
        errors: [errorMsg],
        evidence: this.evidence
      };
    }
  }

  /**
   * Validate JSON content before parsing
   */
  validate(content: string): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    try {
      JSON.parse(content);
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