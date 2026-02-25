// @ECO-governed
// @ECO-layer: GL20-29
// @ECO-semantic: code-complexity-analyzer
// @ECO-audit-trail: ../../governance/GL_SEMANTIC_ANCHOR.json

import * as fs from 'fs';
import * as path from 'path';
import { FileComplexity, CodeComplexityMetrics, AnalysisResult } from '../types';

export class ComplexityAnalyzer {
  analyzeCodeComplexity(repoPath: string): AnalysisResult {
    const complexities = this.analyzeFiles(repoPath);
    const summary = this.generateSummary(complexities);
    const recommendations = this.generateRefactoringRecommendations(complexities);

    return {
      type: 'complexity',
      summary: `Code complexity analysis complete. ${complexities.length} files analyzed. Average cyclomatic complexity: ${summary.avgCyclomatic.toFixed(2)}`,
      data: {
        complexities,
        summary,
        recommendations
      },
      insights: [
        'Most complex files identified for refactoring',
        'Cyclomatic complexity distribution analyzed',
        'Code duplication detected in specific modules',
        'Function length and nesting depth patterns identified'
      ],
      recommendations,
      generatedAt: new Date()
    };
  }

  private analyzeFiles(repoPath: string): FileComplexity[] {
    const complexities: FileComplexity[] = [];

    this.walkDirectory(repoPath, (filePath) => {
      const ext = path.extname(filePath).toLowerCase();
      if (['.ts', '.js', '.py', '.go', '.java', '.cpp', '.c'].includes(ext)) {
        const complexity = this.analyzeFile(filePath);
        complexities.push(complexity);
      }
    });

    return complexities.sort((a, b) => b.complexity.cyclomaticComplexity - a.complexity.cyclomaticComplexity);
  }

  private analyzeFile(filePath: string): FileComplexity {
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.split('\n');
    const language = this.detectLanguage(filePath);

    const complexity: CodeComplexityMetrics = {
      cyclomaticComplexity: this.calculateCyclomaticComplexity(content, language),
      linesOfCode: lines.filter(line => line.trim() && !line.trim().startsWith('//') && !line.trim().startsWith('#')).length,
      functionLength: this.calculateAverageFunctionLength(content, language),
      nestingDepth: this.calculateMaxNestingDepth(content, language),
      duplication: this.calculateDuplication(content)
    };

    return {
      filePath: path.relative(process.cwd(), filePath),
      language,
      complexity,
      priority: this.determinePriority(complexity)
    };
  }

  private calculateCyclomaticComplexity(content: string, language: string): number {
    let complexity = 1; // Base complexity

    // Decision points
    const patterns = {
      javascript: /\b(if|else|for|while|case|catch|switch|\?|\|\||&&)\b/g,
      python: /\b(if|elif|else|for|while|case|except|and|or)\b/g,
      go: /\b(if|else|for|switch|case|default|chan|&&|\|\|)\b/g,
      java: /\b(if|else|for|while|case|catch|switch|\?|\|\||&&)\b/g
    };

    const pattern = patterns[language as keyof typeof patterns] || patterns.javascript;
    const matches = content.match(pattern);

    if (matches) {
      complexity += matches.length;
    }

    return complexity;
  }

  private calculateAverageFunctionLength(content: string, language: string): number {
    const functionPatterns = {
      javascript: /function\s+\w+|=>\s*{|class\s+\w+|constructor\s*\(/g,
      python: /def\s+\w+\(|class\s+\w+/g,
      go: /func\s+\w+\(/g,
      java: /(public|private|protected)?.*\s+\w+\s*\([^)]*\)\s*{/g
    };

    const pattern = functionPatterns[language as keyof typeof functionPatterns] || functionPatterns.javascript;
    const functions = content.split(pattern).filter(f => f.trim().length > 0);

    if (functions.length === 0) return 0;

    const totalLines = functions.reduce((sum, fn) => sum + fn.split('\n').length, 0);
    return Math.round(totalLines / functions.length);
  }

  private calculateMaxNestingDepth(content: string, language: string): number {
    let maxDepth = 0;
    let currentDepth = 0;

    const lines = content.split('\n');
    const openBrackets = ['{', '[', '('];
    const closeBrackets = ['}', ']', ')'];

    for (const line of lines) {
      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        const openIndex = openBrackets.indexOf(char);
        const closeIndex = closeBrackets.indexOf(char);

        if (openIndex !== -1) {
          currentDepth++;
          maxDepth = Math.max(maxDepth, currentDepth);
        } else if (closeIndex !== -1) {
          currentDepth--;
        }
      }
    }

    return maxDepth;
  }

  private calculateDuplication(content: string): number {
    const lines = content.split('\n').filter(line => line.trim().length > 10);
    const lineMap = new Map<string, number>();
    let duplicates = 0;

    for (const line of lines) {
      const normalized = line.trim().toLowerCase();
      const count = lineMap.get(normalized) || 0;
      lineMap.set(normalized, count + 1);
      if (count > 0) {
        duplicates++;
      }
    }

    return lines.length > 0 ? Math.round((duplicates / lines.length) * 100) : 0;
  }

  private determinePriority(complexity: CodeComplexityMetrics): 'low' | 'medium' | 'high' | 'critical' {
    const score = 
      (complexity.cyclomaticComplexity > 15 ? 2 : 0) +
      (complexity.functionLength > 50 ? 2 : 0) +
      (complexity.nestingDepth > 5 ? 2 : 0) +
      (complexity.duplication > 30 ? 2 : 0);

    if (score >= 6) return 'critical';
    if (score >= 4) return 'high';
    if (score >= 2) return 'medium';
    return 'low';
  }

  private detectLanguage(filePath: string): string {
    const ext = path.extname(filePath).toLowerCase();
    const languageMap: { [key: string]: string } = {
      '.ts': 'TypeScript',
      '.js': 'JavaScript',
      '.py': 'Python',
      '.go': 'Go',
      '.java': 'Java',
      '.cpp': 'C++',
      '.c': 'C',
      '.cs': 'C#',
      '.kt': 'Kotlin',
      '.rs': 'Rust'
    };

    return languageMap[ext] || 'Unknown';
  }

  private generateSummary(complexities: FileComplexity[]): any {
    const totalCyclomatic = complexities.reduce((sum, c) => sum + c.complexity.cyclomaticComplexity, 0);
    const avgCyclomatic = complexities.length > 0 ? totalCyclomatic / complexities.length : 0;

    const byPriority: { [key: string]: number } = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0
    };

    for (const c of complexities) {
      byPriority[c.priority]++;
    }

    return {
      totalFiles: complexities.length,
      avgCyclomatic,
      avgFunctionLength: complexities.reduce((sum, c) => sum + c.complexity.functionLength, 0) / complexities.length,
      avgNestingDepth: complexities.reduce((sum, c) => sum + c.complexity.nestingDepth, 0) / complexities.length,
      avgDuplication: complexities.reduce((sum, c) => sum + c.complexity.duplication, 0) / complexities.length,
      byPriority
    };
  }

  private generateRefactoringRecommendations(complexities: FileComplexity[]): any[] {
    const recommendations: any[] = [];
    const criticalFiles = complexities.filter(c => c.priority === 'critical');
    const highFiles = complexities.filter(c => c.priority === 'high');

    for (const file of criticalFiles) {
      recommendations.push({
        filePath: file.filePath,
        priority: 'critical',
        issues: this.identifyIssues(file),
        recommendations: this.suggestRefactoring(file),
        estimatedEffort: '2-4 hours'
      });
    }

    for (const file of highFiles) {
      recommendations.push({
        filePath: file.filePath,
        priority: 'high',
        issues: this.identifyIssues(file),
        recommendations: this.suggestRefactoring(file),
        estimatedEffort: '1-2 hours'
      });
    }

    return recommendations;
  }

  private identifyIssues(file: FileComplexity): string[] {
    const issues: string[] = [];
    const c = file.complexity;

    if (c.cyclomaticComplexity > 15) {
      issues.push(`High cyclomatic complexity (${c.cyclomaticComplexity})`);
    }
    if (c.functionLength > 50) {
      issues.push(`Long functions (avg ${c.functionLength} lines)`);
    }
    if (c.nestingDepth > 5) {
      issues.push(`Deep nesting (${c.nestingDepth} levels)`);
    }
    if (c.duplication > 30) {
      issues.push(`High code duplication (${c.duplication}%)`);
    }

    return issues;
  }

  private suggestRefactoring(file: FileComplexity): string[] {
    const suggestions: string[] = [];
    const c = file.complexity;

    if (c.cyclomaticComplexity > 15) {
      suggestions.push('Extract methods to reduce cyclomatic complexity');
      suggestions.push('Use strategy pattern for complex conditional logic');
    }
    if (c.functionLength > 50) {
      suggestions.push('Break down large functions into smaller units');
      suggestions.push('Apply single responsibility principle');
    }
    if (c.nestingDepth > 5) {
      suggestions.push('Reduce nesting using guard clauses');
      suggestions.push('Extract nested logic into separate methods');
    }
    if (c.duplication > 30) {
      suggestions.push('Extract common code into reusable functions');
      suggestions.push('Use DRY principles to eliminate duplication');
    }

    return suggestions;
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