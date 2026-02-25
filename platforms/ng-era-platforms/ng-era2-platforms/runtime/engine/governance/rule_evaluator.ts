/**
 * @ECO-governed
 * @ECO-layer: governance
 * @ECO-semantic: rule-engine
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Rule Evaluator
 * Evaluates governance rules against artifacts
 */

import { promises as fs } from 'fs';
import path from 'path';

export interface Rule {
  id: string;
  name: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  check: (content: string, filePath: string) => boolean;
}

export class RuleEvaluator {
  private rules: Rule[] = [
    {
      id: 'ECO-GOVERNANCE-MARKER',
      name: 'GL Governance Marker',
      description: 'All source files must contain @ECO-governed marker',
      severity: 'medium',
      check: (content: string, filePath: string) => {
        return /\.(ts|tsx|js)$/.test(filePath) ? content.includes('@ECO-governed') : true;
      }
    },
    {
      id: 'ECO-LAYER-MARKER',
      name: 'GL Layer Marker',
      description: 'All source files must contain @ECO-layer marker',
      severity: 'medium',
      check: (content: string, filePath: string) => {
        return /\.(ts|tsx|js)$/.test(filePath) ? content.includes('@ECO-layer:') : true;
      }
    },
    {
      id: 'ECO-SEMANTIC-MARKER',
      name: 'GL Semantic Marker',
      description: 'All source files must contain @ECO-semantic marker',
      severity: 'medium',
      check: (content: string, filePath: string) => {
        return /\.(ts|tsx|js)$/.test(filePath) ? content.includes('@ECO-semantic:') : true;
      }
    },
    {
      id: 'ECO-AUDIT-TRAIL',
      name: 'GL Audit Trail Reference',
      description: 'All source files must reference audit trail',
      severity: 'medium',
      check: (content: string, filePath: string) => {
        return /\.(ts|tsx|js)$/.test(filePath) ? content.includes('@ECO-audit-trail:') : true;
      }
    },
    {
      id: 'DAG-INTEGRITY',
      name: 'DAG Integrity',
      description: 'Files must not break DAG dependencies',
      severity: 'critical',
      check: (content: string, filePath: string) => {
        // Check for circular dependencies (simplified)
        const imports = content.match(/import.*from\s+['"](\.\.\/|\.\.\/\.\.\/)/g);
        if (imports && imports.length > 5) {
          return false;
        }
        return true;
      }
    }
  ];

  constructor(private workspace: string = process.cwd()) {}

  async evaluate(filePath: string): Promise<Array<{
    rule: Rule;
    passed: boolean;
  }>> {
    try {
      const content = await fs.readFile(filePath, 'utf-8');
      
      return this.rules.map(rule => ({
        rule,
        passed: rule.check(content, filePath)
      }));
    } catch (error) {
      return [];
    }
  }

  async evaluateDirectory(dirPath: string): Promise<Map<string, Array<{
    rule: Rule;
    passed: boolean;
  }>>> {
    const results = new Map<string, Array<{ rule: Rule; passed: boolean }>>();

    const scanDir = async (dir: string): Promise<void> => {
      const entries = await fs.readdir(dir, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        
        if (entry.isDirectory() && 
!['node_modules', '__pycache__', 'dist', 'build'].includes(entry.name)
) {
          await scanDir(fullPath);
        } else if (entry.isFile() && /\.(ts|tsx|js|json)$/.test(entry.name)) {
          const result = await this.evaluate(fullPath);
          results.set(fullPath, result);
        }
      }
    };

    await scanDir(dirPath);
    return results;
  }

  getRules(): Rule[] {
    return [...this.rules];
  }

  addRule(rule: Rule): void {
    this.rules.push(rule);
  }
}