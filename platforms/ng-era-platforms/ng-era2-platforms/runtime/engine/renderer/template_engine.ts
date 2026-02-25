/**
 * @ECO-governed
 * @ECO-layer: renderer
 * @ECO-semantic: renderer-template_engine
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

/**
 * @module template_engine
 * @description Jinja2/Nunjucks template rendering engine
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

import * as nunjucks from 'nunjucks';
import * as path from 'path';
import * as fs from 'fs';
import { RendererInterface, RenderResult, EvidenceRecord } from '../interfaces.d';
import type { DataPayload, TemplateRenderInput, TemplateFilter, TemplateEngineOptions } from '../types';

/**
 * Template Engine
 * 
 * GL30-49: Execution Layer - Renderer Stage
 * 
 * Renders Jinja2 templates with configuration data,
 * supporting filters, macros, and custom extensions.
 */
export class TemplateEngine implements RendererInterface {
  private evidence: EvidenceRecord[] = [];
  private readonly env: nunjucks.Environment;
  private readonly templatePaths: string[] = [];

  constructor(options?: TemplateEngineOptions) {
    this.templatePaths = options?.templatesDir ? [options.templatesDir] : ['./templates', './modules'];
    
    this.env = nunjucks.configure(this.templatePaths, {
      autoescape: true,
      trimBlocks: true,
      lstripBlocks: true,
      throwOnUndefined: false
    });

    // Register custom filters
    if (options?.filters) {
      for (const [name, filter] of options.filters.entries()) {
        this.env.addFilter(name, filter as nunjucks.IFilterCallback);
      }
    }

    // Register built-in filters
    this.registerBuiltInFilters();
  }

  /**
   * Render template with data
   */
  async render(
    templatePath: string,
    data: DataPayload,
    outputPath?: string
  ): Promise<RenderResult> {
    const startTime = Date.now();

    try {
      // Render template
      const rendered = this.env.render(templatePath, data);

      // Write to file if output path is specified
      if (outputPath) {
        this.ensureDirectoryExists(outputPath);
        fs.writeFileSync(outputPath, rendered, 'utf-8');
      }

      // Generate evidence record
      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'renderer',
        component: 'template_engine',
        action: 'render',
        status: 'success',
        input: { template: templatePath, output: outputPath },
        output: {
          renderedLength: rendered.length,
          written: !!outputPath
        },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'success',
        content: rendered,
        outputPath,
        errors: [],
        evidence: this.evidence
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);

      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'renderer',
        component: 'template_engine',
        action: 'render',
        status: 'error',
        input: { template: templatePath, output: outputPath },
        output: { error: errorMsg },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'error',
        content: '',
        outputPath,
        errors: [errorMsg],
        evidence: this.evidence
      };
    }
  }

  /**
   * Render multiple templates
   */
  async renderBatch(
    templates: TemplateRenderInput[]
  ): Promise<Map<string, RenderResult>> {
    const results: Map<string, RenderResult> = new Map();

    for (const template of templates) {
      const result = await this.render(template.path, template.data, template.output);
      results.set(template.path, result);
    }

    return results;
  }

  /**
   * Render string template
   */
  async renderString(
    templateString: string,
    data: DataPayload
  ): Promise<RenderResult> {
    const startTime = Date.now();

    try {
      const rendered = this.env.renderString(templateString, data);

      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'renderer',
        component: 'template_engine',
        action: 'render_string',
        status: 'success',
        input: { templateLength: templateString.length },
        output: { renderedLength: rendered.length },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'success',
        content: rendered,
        errors: [],
        evidence: this.evidence
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);

      this.evidence.push({
        timestamp: new Date().toISOString(),
        stage: 'renderer',
        component: 'template_engine',
        action: 'render_string',
        status: 'error',
        input: {},
        output: { error: errorMsg },
        metrics: { duration: Date.now() - startTime }
      });

      return {
        status: 'error',
        content: '',
        errors: [errorMsg],
        evidence: this.evidence
      };
    }
  }

  /**
   * Register custom filter
   */
  addFilter(name: string, filter: TemplateFilter): void {
    this.env.addFilter(name, filter as nunjucks.IFilterCallback);
  }

  /**
   * Register global variable
   */
  addGlobal(name: string, value: unknown): void {
    this.env.addGlobal(name, value);
  }

  /**
   * Register built-in filters
   */
  private registerBuiltInFilters(): void {
    // YAML filter
    this.env.addFilter('to_yaml', (obj: unknown) => {
      const yaml = require('js-yaml');
      return yaml.dump(obj) as string;
    });

    // JSON filter
    this.env.addFilter('to_json', (obj: unknown, indent?: number) => {
      return JSON.stringify(obj, null, indent || 2);
    });

    // Base64 filter
    this.env.addFilter('to_base64', (str: string) => {
      return Buffer.from(str).toString('base64');
    });

    // SHA256 filter
    this.env.addFilter('sha256', (str: string) => {
      const crypto = require('crypto');
      return crypto.createHash('sha256').update(str).digest('hex') as string;
    });

    // Default filter
    this.env.addFilter('default', (value: unknown, defaultValue: unknown) => {
      return value !== undefined && value !== null ? value : defaultValue;
    });

    // Slugify filter
    this.env.addFilter('slugify', (str: string) => {
      return str
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '');
    });
  }

  /**
   * Ensure directory exists
   */
  private ensureDirectoryExists(filePath: string): void {
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }

  /**
   * Get evidence records
   */
  getEvidence(): EvidenceRecord[] {
    return this.evidence;
  }
}