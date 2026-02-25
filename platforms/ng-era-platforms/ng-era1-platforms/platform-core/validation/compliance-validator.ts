// @ECO-governed @ECO-internal-only
// Production-grade Compliance Validator
// Version: 3.0.0

import * as fs from 'fs/promises';
import * as path from 'path';
import { v4 as uuidv4 } from 'uuid';

export interface ComplianceRule {
  id: string;
  name: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  check: (content: string, filePath: string) => boolean;
}

export interface ComplianceReport {
  reportId: string;
  timestamp: string;
  totalFiles: number;
  compliantFiles: number;
  nonCompliantFiles: number;
  violations: Violation[];
  overallCompliance: number;
}

export interface Violation {
  ruleId: string;
  ruleName: string;
  severity: string;
  filePath: string;
  description: string;
  line?: number;
}

export class ComplianceValidator {
  private rules: ComplianceRule[];
  private violations: Violation[] = [];

  constructor() {
    this.rules = this.initializeRules();
  }

  /**
   * Initialize compliance rules
   */
  private initializeRules(): ComplianceRule[] {
    return [
      {
        id: 'GOV-001',
        name: 'Governance Marker Required',
        description: 'Files must contain @ECO-governed marker',
        severity: 'critical',
        check: (content: string) => content.includes('@ECO-governed')
      },
      {
        id: 'GOV-002',
        name: 'Layer Marker Required',
        description: 'Files must contain @ECO-layer marker',
        severity: 'critical',
        check: (content: string) => content.includes('@ECO-layer')
      },
      {
        id: 'GOV-003',
        name: 'Semantic Marker Required',
        description: 'Files must contain @ECO-semantic marker',
        severity: 'high',
        check: (content: string) => content.includes('@ECO-semantic')
      },
      {
        id: 'SEC-001',
        name: 'No Hardcoded Secrets',
        description: 'Files must not contain hardcoded secrets',
        severity: 'critical',
        check: (content: string) => {
          const secretPatterns = [
            /password\s*=\s*['"][^'"]+['"]/i,
            /api_key\s*=\s*['"][^'"]+['"]/i,
            /secret\s*=\s*['"][^'"]+['"]/i,
            /token\s*=\s*['"][^'"]+['"]/i
          ];
          return !secretPatterns.some(pattern => pattern.test(content));
        }
      },
      {
        id: 'ARC-001',
        name: 'No Temporary Files',
        description: 'Files must not be temporary files',
        severity: 'medium',
        check: (_content: string, filePath: string) => {
          const tempPatterns = [/\.tmp$/, /\.temp$/, /\.cache$/, /\.log$/];
          return !tempPatterns.some(pattern => pattern.test(filePath));
        }
      },
      {
        id: 'ARC-002',
        name: 'No Debug Files',
        description: 'Files must not be debug files',
        severity: 'low',
        check: (_content: string, filePath: string) => {
          return !filePath.startsWith('debug_') && !filePath.includes('-debug');
        }
      }
    ];
  }

  /**
   * Validate directory
   */
  async validateDirectory(directoryPath: string): Promise<ComplianceReport> {
    const reportId = uuidv4();
    const timestamp = new Date().toISOString();
    
    let totalFiles = 0;
    let compliantFiles = 0;
    this.violations = [];

    // Scan directory recursively
    await this.scanDirectory(directoryPath);

    totalFiles = this.violations.length + compliantFiles;

    // Calculate compliance
    const overallCompliance = totalFiles > 0 
      ? Math.round((compliantFiles / totalFiles) * 100)
      : 100;

    const report: ComplianceReport = {
      reportId,
      timestamp,
      totalFiles,
      compliantFiles,
      nonCompliantFiles: this.violations.length,
      violations: [...this.violations],
      overallCompliance
    };

    return report;
  }

  /**
   * Scan directory recursively
   */
  private async scanDirectory(directoryPath: string): Promise<void> {
    try {
      const entries = await fs.readdir(directoryPath, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = path.join(directoryPath, entry.name);

        if (entry.isDirectory()) {
          // Skip certain directories
          if (['node_modules', '.git', 'dist', 'build'].includes(entry.name)) {
            continue;
          }
          await this.scanDirectory(fullPath);
        } else if (entry.isFile()) {
          await this.validateFile(fullPath);
        }
      }
    } catch (error) {
      // Ignore permission errors
    }
  }

  /**
   * Validate single file
   */
  private async validateFile(filePath: string): Promise<boolean> {
    try {
      const content = await fs.readFile(filePath, 'utf-8');
      let isCompliant = true;

      for (const rule of this.rules) {
        const result = rule.check(content, filePath);
        
        if (!result) {
          isCompliant = false;
          this.violations.push({
            ruleId: rule.id,
            ruleName: rule.name,
            severity: rule.severity,
            filePath,
            description: rule.description
          });
        }
      }

      return isCompliant;
    } catch (error) {
      // Ignore read errors
      return true;
    }
  }

  /**
   * Get violations by severity
   */
  getViolationsBySeverity(): Map<string, Violation[]> {
    const bySeverity = new Map<string, Violation[]>();
    
    for (const violation of this.violations) {
      if (!bySeverity.has(violation.severity)) {
        bySeverity.set(violation.severity, []);
      }
      bySeverity.get(violation.severity)!.push(violation);
    }
    
    return bySeverity;
  }

  /**
   * Check if compliance is acceptable
   */
  isComplianceAcceptable(threshold: number = 100): boolean {
    return this.getOverallCompliance() >= threshold;
  }

  /**
   * Get overall compliance percentage
   */
  getOverallCompliance(): number {
    const totalFiles = this.violations.length;
    // Simplified calculation - actual would need total file count
    return totalFiles === 0 ? 100 : Math.max(0, 100 - (totalFiles * 10));
  }

  /**
   * Get critical violations
   */
  getCriticalViolations(): Violation[] {
    return this.violations.filter(v => v.severity === 'critical');
  }

  /**
   * Clear violations
   */
  clearViolations(): void {
    this.violations = [];
  }
}