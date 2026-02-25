/**
 * @ECO-governed
 * @ECO-layer: server
 * @ECO-semantic: organization-service
 * @ECO-audit-trail: ../.governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - File Organization Service
 */

import { File, Rule } from '../types';
import { promises as fs } from 'fs';
import path from 'path';

export class OrganizationService {
  /**
   * Organize a single file based on rules
   */
  async organizeFile(file: File, rule: Rule): Promise<boolean> {
    const sourcePath = file.path;
    const destPath = path.join(rule.destination, file.name);

    try {
      switch (rule.action) {
        case 'move':
          await fs.mkdir(rule.destination, { recursive: true });
          await fs.rename(sourcePath, destPath);
          return true;
        case 'copy':
          await fs.mkdir(rule.destination, { recursive: true });
          await fs.copyFile(sourcePath, destPath);
          return true;
        case 'delete':
          await fs.unlink(sourcePath);
          return true;
        default:
          return false;
      }
    } catch (error) {
      console.error(`Failed to organize file ${file.name}:`, error);
      return false;
    }
  }

  /**
   * Batch organize files
   */
  async organizeFiles(files: File[], rules: Rule[]): Promise<Map<string, boolean>> {
    const results = new Map<string, boolean>();

    for (const file of files) {
      const applicableRule = rules.find(rule => 
        rule.enabled && file.name.match(new RegExp(rule.pattern))
      );

      if (applicableRule) {
        const success = await this.organizeFile(file, applicableRule);
        results.set(file.id, success);
      }
    }

    return results;
  }

  /**
   * Validate organization structure
   */
  async validateStructure(basePath: string): Promise<{
    valid: boolean;
    issues: string[];
  }> {
    const issues: string[] = [];

    try {
      const entries = await fs.readdir(basePath, { withFileTypes: true });

      for (const entry of entries) {
        if (entry.isDirectory()) {
          // Check for proper directory naming
          if (!/^[a-z][a-z0-9-]*$/.test(entry.name)) {
            issues.push(`Invalid directory name: ${entry.name}`);
          }
        }
      }

      return {
        valid: issues.length === 0,
        issues
      };
    } catch (error) {
      issues.push(`Failed to validate structure: ${error}`);
      return {
        valid: false,
        issues
      };
    }
  }
}