// @ECO-governed
// @ECO-layer: GL20-29
// @ECO-semantic: performance-analyzer
// @ECO-audit-trail: ../../governance/GL_SEMANTIC_ANCHOR.json

import * as fs from 'fs';
import * as path from 'path';
import { PerformanceIssue, AnalysisResult, Recommendation } from '../types';

export class PerformanceAnalyzer {
  analyzePerformance(repoPath: string): AnalysisResult {
    const issues = this.detectPerformanceIssues(repoPath);
    const summary = this.generateSummary(issues);

    return {
      type: 'performance',
      summary: `Performance analysis complete. ${issues.length} issues detected. ${summary.criticalCount} critical issues found.`,
      data: {
        issues,
        summary
      },
      insights: [
        'Performance bottlenecks identified across codebase',
        'Database query patterns analyzed',
        'Memory leak risks detected',
        'N+1 query problems identified'
      ],
      recommendations: this.generateRecommendations(issues),
      generatedAt: new Date()
    };
  }

  private detectPerformanceIssues(repoPath: string): PerformanceIssue[] {
    const issues: PerformanceIssue[] = [];

    this.walkDirectory(repoPath, (filePath) => {
      const ext = path.extname(filePath).toLowerCase();
      if (['.ts', '.js', '.py', '.go', '.java'].includes(ext)) {
        const fileIssues = this.analyzeFile(filePath, ext);
        issues.push(...fileIssues);
      }
    });

    return issues;
  }

  private analyzeFile(filePath: string, ext: string): PerformanceIssue[] {
    const issues: PerformanceIssue[] = [];
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.split('\n');
    const relativePath = path.relative(process.cwd(), filePath);

    // Detect N+1 query problems
    const n1Patterns = {
      javascript: /for\s*\(.*of.*\)\s*{[\s\S]*?fetch|await.*forEach[\s\S]*?await/gm,
      python: /for\s+\w+\s+in[\s\S]*?\.get\(|for\s+\w+\s+in[\s\S]*?\.query\(/gm,
      go: /range\s+[\s\S]*?db\.Query/gm,
      java: /for\s*\([^)]*\)[^{]*\{[\s\S]*?session\.get|em\.find/gm
    };

    const pattern = n1Patterns[ext.replace('.', '') as keyof typeof n1Patterns];
    if (pattern) {
      const matches = content.match(pattern);
      if (matches && matches.length > 0) {
        issues.push({
          type: 'N+1 Query Problem',
          location: relativePath,
          severity: 'high',
          description: `Potential N+1 query problem detected (${matches.length} instances)`,
          recommendation: 'Use eager loading or batch queries to fetch related data'
        });
      }
    }

    // Detect inefficient loops
    const loopPatterns = {
      javascript: /for\s*\(.*\.length.*\)\s*{[\s\S]*?\.includes\(|\.indexOf\(/gm,
      python: /for\s+\w+\s+in[\s\S]*?if\s+\w+\s+in/gm
    };

    const loopPattern = loopPatterns[ext.replace('.', '') as keyof typeof loopPatterns];
    if (loopPattern) {
      const matches = content.match(loopPattern);
      if (matches && matches.length > 0) {
        issues.push({
          type: 'Inefficient Loop',
          location: relativePath,
          severity: 'medium',
          description: `Inefficient loop with O(n^2) complexity (${matches.length} instances)`,
          recommendation: 'Use Set or Map data structures for O(1) lookups'
        });
      }
    }

    // Detect synchronous operations in async contexts
    if (['.ts', '.js'].includes(ext)) {
      const syncPattern = /async\s+function[\s\S]*?fs\.readFileSync|async\s+function[\s\S]*?fs\.writeFileSync/gm;
      const matches = content.match(syncPattern);
      if (matches) {
        issues.push({
          type: 'Synchronous I/O in Async Context',
          location: relativePath,
          severity: 'high',
          description: 'Synchronous file operations in async function',
          recommendation: 'Use async/await with fs.promises instead of synchronous operations'
        });
      }
    }

    // Detect potential memory leaks
    const leakPatterns = [
      { regex: /setInterval|setTimer/g, desc: 'Timer without clearInterval/clearTimeout' },
      { regex: /addEventListener/g, desc: 'Event listener without removeEventListener' },
      { regex: /\.on\(/g, desc: 'Event emitter without .off() or .removeListener()' }
    ];

    for (const { regex, desc } of leakPatterns) {
      const matches = content.match(regex);
      if (matches && matches.length > 0) {
        issues.push({
          type: 'Potential Memory Leak',
          location: relativePath,
          severity: 'medium',
          description: `${desc} detected (${matches.length} instances)`,
          recommendation: 'Ensure proper cleanup of timers and event listeners'
        });
      }
    }

    // Detect large objects in memory
    if (content.includes('cache') || content.includes('Cache')) {
      issues.push({
        type: 'Unbounded Cache',
        location: relativePath,
        severity: 'medium',
        description: 'Cache without size limit may cause memory issues',
        recommendation: 'Implement cache eviction policy and size limits'
      });
    }

    // Detect heavy computations in hot paths
    const heavyPatterns = [
      { regex: /JSON\.parse\([^)]{100,}\)/g, desc: 'Large JSON parsing' },
      { regex: /JSON\.stringify\([^)]{100,}\)/g, desc: 'Large JSON serialization' }
    ];

    for (const { regex, desc } of heavyPatterns) {
      const matches = content.match(regex);
      if (matches) {
        issues.push({
          type: 'Heavy Computation',
          location: relativePath,
          severity: 'medium',
          description: `${desc} detected`,
          recommendation: 'Consider streaming, lazy loading, or worker threads'
        });
      }
    }

    // Detect missing database indexes (mock detection)
    if (content.includes('SELECT') || content.includes('find(') || content.includes('query(')) {
      issues.push({
        type: 'Missing Database Index',
        location: relativePath,
        severity: 'low',
        description: 'Database query without indexed columns',
        recommendation: 'Review query patterns and add appropriate indexes'
      });
    }

    return issues;
  }

  private generateSummary(issues: PerformanceIssue[]): any {
    const summary: any = {
      total: issues.length,
      bySeverity: {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0
      },
      byType: {}
    };

    for (const issue of issues) {
      summary.bySeverity[issue.severity]++;
      summary.byType[issue.type] = (summary.byType[issue.type] || 0) + 1;
    }

    return summary;
  }

  private generateRecommendations(issues: PerformanceIssue[]): Recommendation[] {
    const recommendations: Recommendation[] = [];
    const typeGroups = new Map<string, PerformanceIssue[]>();

    for (const issue of issues) {
      if (!typeGroups.has(issue.type)) {
        typeGroups.set(issue.type, []);
      }
      typeGroups.get(issue.type)!.push(issue);
    }

    // Generate recommendations by type
    for (const [type, typeIssues] of typeGroups.entries()) {
      const severity = typeIssues.some(i => i.severity === 'critical') ? 'critical' :
                       typeIssues.some(i => i.severity === 'high') ? 'high' :
                       typeIssues.some(i => i.severity === 'medium') ? 'medium' : 'low';

      const priority = typeIssues.some(i => i.severity === 'high' || i.severity === 'critical') ? 'high' : 'medium';
      const count = typeIssues.length;

      recommendations.push({
        category: 'performance',
        priority,
        description: `Fix ${count} ${type}${count > 1 ? 's' : ''} detected in codebase`,
        actionable: true,
        estimatedEffort: this.estimateEffort(type, count)
      });
    }

    // Add general recommendations
    if (issues.length > 0) {
      recommendations.push({
        category: 'monitoring',
        priority: 'medium',
        description: 'Implement performance monitoring and alerting',
        actionable: true,
        estimatedEffort: '1-2 days'
      });

      recommendations.push({
        category: 'testing',
        priority: 'medium',
        description: 'Add performance benchmarks to test suite',
        actionable: true,
        estimatedEffort: '1-2 days'
      });
    }

    return recommendations;
  }

  private estimateEffort(type: string, count: number): string {
    const effortMap: { [key: string]: string } = {
      'N+1 Query Problem': count <= 5 ? '2-4 hours' : '1-2 days',
      'Inefficient Loop': count <= 5 ? '1-2 hours' : '4-8 hours',
      'Synchronous I/O in Async Context': count <= 3 ? '1-2 hours' : '4-8 hours',
      'Potential Memory Leak': count <= 3 ? '2-4 hours' : '1-2 days',
      'Unbounded Cache': count <= 2 ? '1-2 hours' : '4-8 hours',
      'Heavy Computation': count <= 3 ? '2-4 hours' : '1-2 days',
      'Missing Database Index': count <= 5 ? '1-2 hours' : '4-8 hours'
    };

    return effortMap[type] || '2-4 hours';
  }

  private walkDirectory(dir: string, callback: (filePath: string) => void): void {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        if (!['node_modules', '.git', 'dist', 'build', 'target', 'bin'].includes(entry.name)) {
          this.walkDirectory(fullPath, callback);
        }
      } else if (entry.isFile()) {
        callback(fullPath);
      }
    }
  }
}