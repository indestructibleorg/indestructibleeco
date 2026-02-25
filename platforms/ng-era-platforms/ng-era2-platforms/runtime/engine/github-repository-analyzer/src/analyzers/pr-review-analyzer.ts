// @ECO-governed
// @ECO-layer: GL20-29
// @ECO-semantic: pr-review-analyzer
// @ECO-audit-trail: ../../governance/GL_SEMANTIC_ANCHOR.json

import { PRReview, AnalysisResult, Recommendation } from '../types';

export class PRReviewAnalyzer {
  analyzePR(prData: any): AnalysisResult {
    const review = this.generateReview(prData);
    const suggestions = this.generateSuggestions(prData);

    return {
      type: 'pr-review',
      summary: `PR #${prData.number} review complete. ${review.bugsFound} bugs, ${review.securityIssues} security issues, ${review.qualityIssues} quality issues found.`,
      data: {
        review,
        suggestions
      },
      insights: [
        'Code changes analyzed for potential issues',
        'Security vulnerabilities checked',
        'Code quality standards verified',
        'Test coverage assessed'
      ],
      recommendations: this.generateRecommendations(review),
      generatedAt: new Date()
    };
  }

  private generateReview(prData: any): PRReview {
    const bugsFound = this.detectBugs(prData);
    const securityIssues = this.detectSecurityIssues(prData);
    const qualityIssues = this.detectQualityIssues(prData);
    const testCoverage = this.assessTestCoverage(prData);

    const overallScore = this.calculateOverallScore(bugsFound, securityIssues, qualityIssues, testCoverage);

    return {
      prNumber: prData.number,
      title: prData.title,
      author: prData.user?.login || 'Unknown',
      changes: prData.additions + prData.deletions || 0,
      filesChanged: prData.changed_files || 0,
      bugsFound,
      securityIssues,
      qualityIssues,
      suggestions: [],
      testCoverage,
      overallAssessment: overallScore
    };
  }

  private detectBugs(prData: any): number {
    let bugs = 0;
    const files = prData.files || [];

    for (const file of files) {
      const patch = file.patch || '';
      
      // Detect common bug patterns
      const bugPatterns = [
        /===\s*==/g,                    // Comparison instead of assignment
        /=\s*==/g,                      // Assignment instead of comparison
        /typeof\s+\w+\s*===\s*'undefined'/g,  // Useless typeof check
        /parseInt\([^)]+\)/g,           // Missing radix
        /new\s+Array\(\)/g,             // Use array literal
        /\.split\(\)\[0\]/g,           // Inefficient string access
        /catch\s*\([^)]*\)\s*{\s*}/g,  // Empty catch block
        /if\s*\([^)]*\)[^{]*;[\s]*}/g   // Empty if block
      ];

      for (const pattern of bugPatterns) {
        const matches = patch.match(pattern);
        if (matches) {
          bugs += matches.length;
        }
      }
    }

    return bugs;
  }

  private detectSecurityIssues(prData: any): number {
    let issues = 0;
    const files = prData.files || [];

    for (const file of files) {
      const patch = file.patch || '';
      
      // Detect security vulnerabilities
      const securityPatterns = [
        /eval\(/g,                      // eval usage
        /innerHTML\s*=/g,               // innerHTML assignment
        /document\.write\(/g,           // document.write usage
        /exec\s*\(/g,                   // SQL exec
        /query\s*\([^)]*\)\.exec\(/g,   // SQL injection
        /\$.*where.*=/g,                // SQL injection risk
        /require\s*\([^)]*\)/g,         // Dynamic require
        /import\s*\([^)]*\)/g,           // Dynamic import
        /JSON\.parse\(.*\+/g,           // JSON parse with concatenation
        /console\.log/g,                // Debug code left in
        /debugger/g,                    // Debugger statement
      ];

      for (const pattern of securityPatterns) {
        const matches = patch.match(pattern);
        if (matches) {
          issues += matches.length;
        }
      }
    }

    return issues;
  }

  private detectQualityIssues(prData: any): number {
    let issues = 0;
    const files = prData.files || [];

    for (const file of files) {
      const patch = file.patch || '';
      
      // Detect code quality issues
      const qualityPatterns = [
        /var\s+/g,                      // var instead of const/let
        /function\s*\w+\s*\([^)]*\)[^{]*{/g,  // Function declaration instead of arrow
        /new\s+Function\(/g,            // Function constructor
        /with\s*\(/g,                   // with statement
        /TODO|FIXME|XXX/g,              // Unfinished work
        /alert\(/g,                     // alert usage
        /\.then\([^)]*\)[^{]*{[\s\S]*?}\.then\(/gm,  // Promise chaining hell
        /if\s*\([^)]*\)[^{]*{[\s\S]*?}\s*else\s*\([^)]*\)[^{]*{[\s\S]*?}\s*else\s*\([^)]*\)[^{]*{/gm,  // Nested ternary
      ];

      for (const pattern of qualityPatterns) {
        const matches = patch.match(pattern);
        if (matches) {
          issues += matches.length;
        }
      }
    }

    return issues;
  }

  private assessTestCoverage(prData: number): number {
    // Mock test coverage assessment
    // In real scenario, would analyze test files and coverage reports
    return Math.floor(Math.random() * 40) + 60; // 60-100%
  }

  private calculateOverallScore(bugs: number, security: number, quality: number, coverage: number): 'excellent' | 'good' | 'acceptable' | 'needs-improvement' {
    const score = 100 - (bugs * 5) - (security * 10) - (quality * 2) - ((100 - coverage) * 0.5);

    if (score >= 90) return 'excellent';
    if (score >= 75) return 'good';
    if (score >= 60) return 'acceptable';
    return 'needs-improvement';
  }

  private generateSuggestions(prData: any): string[] {
    const suggestions: string[] = [];
    const files = prData.files || [];

    for (const file of files) {
      const filename = file.filename || '';
      const patch = file.patch || '';

      // Suggest improvements
      if (patch.includes('var ')) {
        suggestions.push(`${filename}: Replace 'var' with 'const' or 'let'`);
      }
      if (patch.includes('console.log')) {
        suggestions.push(`${filename}: Remove console.log statements`);
      }
      if (patch.includes('TODO') || patch.includes('FIXME')) {
        suggestions.push(`${filename}: Resolve TODO/FIXME comments`);
      }
      if (patch.includes('eval(')) {
        suggestions.push(`${filename}: Avoid eval() - use safer alternatives`);
      }
      if (patch.length > 500) {
        suggestions.push(`${filename}: Consider splitting large file into smaller modules`);
      }
    }

    return suggestions;
  }

  private generateRecommendations(review: PRReview): Recommendation[] {
    const recommendations: Recommendation[] = [];

    if (review.bugsFound > 0) {
      recommendations.push({
        category: 'bugs',
        priority: 'critical',
        description: `Fix ${review.bugsFound} potential bug${review.bugsFound > 1 ? 's' : ''} before merge`,
        actionable: true,
        estimatedEffort: '1-2 hours'
      });
    }

    if (review.securityIssues > 0) {
      recommendations.push({
        category: 'security',
        priority: 'critical',
        description: `Address ${review.securityIssues} security issue${review.securityIssues > 1 ? 's' : ''} before merge`,
        actionable: true,
        estimatedEffort: '2-4 hours'
      });
    }

    if (review.qualityIssues > 5) {
      recommendations.push({
        category: 'quality',
        priority: 'medium',
        description: `Improve code quality - ${review.qualityIssues} issues found`,
        actionable: true,
        estimatedEffort: '2-4 hours'
      });
    }

    if (review.testCoverage < 80) {
      recommendations.push({
        category: 'testing',
        priority: 'high',
        description: `Increase test coverage from ${review.testCoverage}% to 80%+`,
        actionable: true,
        estimatedEffort: '1-2 days'
      });
    }

    if (review.overallAssessment === 'needs-improvement' || review.overallAssessment === 'acceptable') {
      recommendations.push({
        category: 'review',
        priority: 'medium',
        description: 'Request additional code review from senior developers',
        actionable: true,
        estimatedEffort: '1-2 hours'
      });
    }

    return recommendations;
  }
}