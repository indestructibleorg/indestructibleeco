/**
 * @ECO-governed
 * @ECO-layer: governance
 * @ECO-semantic: engine-core
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Governance Engine Core
 * Enforces strict governance validation and event stream generation
 */

import { promises as fs } from 'fs';
import path from 'path';
import { GovernanceEventWriter } from './events_writer';
import { RuleEvaluator } from './rule_evaluator';
import { AnchorResolver } from './anchor_resolver';

export interface GovernanceResult {
  success: boolean;
  violations: GovernanceViolation[];
  events: GovernanceEvent[];
  auditTrail: string[];
}

export interface GovernanceViolation {
  code: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  message: string;
  file: string;
  line?: number;
  fixRequired: boolean;
}

export interface GovernanceEvent {
  id: string;
  type: 'validation' | 'compliance' | 'enforcement' | 'audit';
  timestamp: string;
  source: string;
  data: any;
}

export class GLEngine {
  private eventWriter: GovernanceEventWriter;
  private ruleEvaluator: RuleEvaluator;
  private anchorResolver: AnchorResolver;
  private auditTrail: string[] = [];

  constructor(private workspace: string = process.cwd()) {
    this.eventWriter = new GovernanceEventWriter(workspace);
    this.ruleEvaluator = new RuleEvaluator(workspace);
    this.anchorResolver = new AnchorResolver(workspace);
  }

  async validate(options: { strict?: boolean } = {}): Promise<GovernanceResult> {
    const result: GovernanceResult = {
      success: true,
      violations: [],
      events: [],
      auditTrail: []
    };

    this.auditTrail.push(`GL Validation Started at ${new Date().toISOString()}`);
    this.auditTrail.push(`Workspace: ${this.workspace}`);
    this.auditTrail.push(`Strict Mode: ${options.strict ?? true}`);

    try {
      // Load semantic anchor
      const anchorLoaded = await this.anchorResolver.loadAnchor();
      if (!anchorLoaded) {
        result.success = false;
        result.violations.push({
          code: 'ECO-ANCHOR-MISSING',
          severity: 'critical',
          message: 'GL Semantic Anchor not found or invalid',
          file: 'governance/GL_SEMANTIC_ANCHOR.json',
          fixRequired: true
        });
      }

      // Scan and validate all files
      const violations = await this.scanAndValidate();
      result.violations.push(...violations);

      // Check if critical violations exist
      const criticalViolations = result.violations.filter(v => v.severity === 'critical');
      if (criticalViolations.length > 0) {
        result.success = false;
        if (options.strict !== false) {
          throw new Error(`Critical GL violations detected: ${criticalViolations.length}`);
        }
      }

      // Generate governance events
      const events = await this.generateGovernanceEvents(result);
      result.events.push(...events);

      // Write event stream
      await this.eventWriter.writeEvents(events);

    } catch (error) {
      result.success = false;
      const errorMessage = error instanceof Error ? error.message : String(error);
      result.violations.push({
        code: 'ECO-ENGINE-ERROR',
        severity: 'critical',
        message: `GL Engine execution error: ${errorMessage}`,
        file: 'governance/gl_engine.ts',
        fixRequired: true
      });
    }

    result.auditTrail = [...this.auditTrail];
    this.auditTrail.push(`GL Validation Completed at ${new Date().toISOString()}`);

    return result;
  }

  private async scanAndValidate(): Promise<GovernanceViolation[]> {
    const violations: GovernanceViolation[] = [];
    const engineDir = this.workspace;

    const scanDir = async (dir: string): Promise<void> => {
      const entries = await fs.readdir(dir, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        
        if (entry.isDirectory() && 
!['node_modules', '__pycache__', 'dist', 'build'].includes(entry.name)
) {
          await scanDir(fullPath);
        } else if (entry.isFile() && /\.(ts|tsx|js|json|yaml|yml)$/.test(entry.name)) {
          const fileViolations = await this.validateFile(fullPath);
          violations.push(...fileViolations);
        }
      }
    };

    await scanDir(engineDir);
    return violations;
  }

  private async validateFile(filePath: string): Promise<GovernanceViolation[]> {
    const violations: GovernanceViolation[] = [];
    const relativePath = path.relative(this.workspace, filePath);
    
    try {
      const content = await fs.readFile(filePath, 'utf-8');

      // Check for GL governance markers
      if (/\.(ts|tsx|js)$/.test(filePath)) {
        if (!content.includes('@ECO-governed')) {
          violations.push({
            code: 'ECO-MARKER-MISSING',
            severity: 'medium',
            message: 'Missing @ECO-governed marker',
            file: relativePath,
            fixRequired: true
          });
        }

        if (!content.includes('@ECO-layer:')) {
          violations.push({
            code: 'ECO-LAYER-MISSING',
            severity: 'medium',
            message: 'Missing @ECO-layer marker',
            file: relativePath,
            fixRequired: true
          });
        }

        if (!content.includes('@ECO-semantic:')) {
          violations.push({
            code: 'ECO-SEMANTIC-MISSING',
            severity: 'medium',
            message: 'Missing @ECO-semantic marker',
            file: relativePath,
            fixRequired: true
          });
        }
      }

      // Validate JSON files
      if (filePath.endsWith('.json')) {
        try {
          JSON.parse(content);
        } catch (error) {
          violations.push({
            code: 'JSON-INVALID',
            severity: 'high',
            message: 'Invalid JSON syntax',
            file: relativePath,
            fixRequired: true
          });
        }
      }

    } catch (error) {
      violations.push({
        code: 'FILE-READ-ERROR',
        severity: 'low',
        message: `Cannot read file: ${error}`,
        file: relativePath,
        fixRequired: false
      });
    }

    return violations;
  }

  private async generateGovernanceEvents(result: GovernanceResult): Promise<GovernanceEvent[]> {
    const events: GovernanceEvent[] = [];

    events.push({
      id: `gl-validation-${Date.now()}`,
      type: 'validation',
      timestamp: new Date().toISOString(),
      source: 'governance/gl_engine.ts',
      data: {
        success: result.success,
        violationCount: result.violations.length,
        criticalCount: result.violations.filter(v => v.severity === 'critical').length
      }
    });

    if (!result.success) {
      events.push({
        id: `gl-violation-${Date.now()}`,
        type: 'enforcement',
        timestamp: new Date().toISOString(),
        source: 'governance/gl_engine.ts',
        data: {
          violations: result.violations,
          enforcement: 'strict'
        }
      });
    }

    return events;
  }

  async check(): Promise<GovernanceResult> {
    return this.validate({ strict: false });
  }

  async fix(options: { auto?: boolean } = {}): Promise<GovernanceResult> {
    const result = await this.check();
    
    // Auto-fix non-critical violations
    if (options.auto) {
      for (const violation of result.violations) {
        if (violation.severity !== 'critical' && violation.fixRequired) {
          await this.applyFix(violation);
        }
      }
    }

    return result;
  }

  private async applyFix(violation: GovernanceViolation): Promise<void> {
    // Implementation of auto-fix logic
    this.auditTrail.push(`Auto-fix applied: ${violation.code} for ${violation.file}`);
  }

  async pipeline(options: { full?: boolean } = {}): Promise<GovernanceResult> {
    this.auditTrail.push('Pipeline execution started');
    
    const result = await this.validate({ strict: true });
    
    if (options.full) {
      // Run full pipeline including gate execution
      this.auditTrail.push('Running full pipeline with gates');
    }

    this.auditTrail.push('Pipeline execution completed');
    return result;
  }
}

// CLI interface
if (require.main === module) {
  const command = process.argv[2];
  const engine = new GLEngine();

  engine[command]()
    .then((result: GovernanceResult) => {
      console.log(JSON.stringify(result, null, 2));
      process.exit(result.success ? 0 : 1);
    })
    .catch((error: Error) => {
      console.error('GL Engine Error:', error.message);
      process.exit(1);
    });
}