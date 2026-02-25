// @ECO-governed
// @ECO-layer: GL20-29
// @ECO-semantic: github-repository-analyzer-main
// @ECO-audit-trail: ../../governance/GL_SEMANTIC_ANCHOR.json

import * as path from 'path';
import * as analyzers from './analyzers';
import { RepositoryConfig, AnalysisResult, RepositoryAnalysis } from './types';

export class GitHubRepositoryAnalyzer {
  constructor(private repoPath: string) {}

  async analyzeRepository(config?: Partial<RepositoryConfig>): Promise<RepositoryAnalysis> {
    console.log('Starting comprehensive repository analysis...');

    const structureAnalyzer = new analyzers.StructureAnalyzer(this.repoPath);
    const complexityAnalyzer = new analyzers.ComplexityAnalyzer();
    const dependencyAnalyzer = new analyzers.DependencyAnalyzer();
    const licenseAnalyzer = new analyzers.LicenseAnalyzer();
    const performanceAnalyzer = new analyzers.PerformanceAnalyzer();
    const issueTrackerAnalyzer = new analyzers.IssueTrackerAnalyzer();

    // Analyze structure
    const structureResult = await structureAnalyzer.analyzeStructure({
      owner: config?.owner || 'unknown',
      repo: config?.repo || 'unknown',
      branch: config?.branch || 'main',
      token: config?.token
    });

    // Analyze code complexity
    const complexityResult = complexityAnalyzer.analyzeCodeComplexity(this.repoPath);

    // Analyze dependencies
    const dependencyResult = await dependencyAnalyzer.analyzeDependencies(this.repoPath);

    // Analyze licenses
    const licenseResult = licenseAnalyzer.analyzeLicenses(this.repoPath);

    // Analyze performance
    const performanceResult = performanceAnalyzer.analyzePerformance(this.repoPath);

    // Generate comprehensive analysis
    const analysis: RepositoryAnalysis = {
      repository: {
        owner: config?.owner || 'unknown',
        repo: config?.repo || 'unknown',
        branch: config?.branch || 'main'
      },
      techStack: structureResult.data.techStack,
      dependencies: dependencyResult.data.dependencies,
      codeComplexity: complexityResult.data.complexities,
      licenses: [structureResult.data.documentation],
      performanceIssues: performanceResult.data.issues,
      documentation: structureResult.data.documentation,
      testCoverage: structureResult.data.testCoverage,
      contributors: [],
      issueMetrics: {
        openIssues: 0,
        closedIssues: 0,
        openPRs: 0,
        mergedPRs: 0,
        avgResolutionTime: 0,
        commonLabels: [],
        staleIssues: 0,
        mergeRate: 0
      },
      recommendations: [
        ...structureResult.recommendations,
        ...complexityResult.recommendations,
        ...dependencyResult.recommendations,
        ...licenseResult.recommendations,
        ...performanceResult.recommendations
      ],
      generatedAt: new Date()
    };

    console.log('Repository analysis complete!');
    return analysis;
  }

  analyzeStructure(config: Partial<RepositoryConfig> = {}) {
    const analyzer = new analyzers.StructureAnalyzer(this.repoPath);
    return analyzer.analyzeStructure({
      owner: config.owner || 'unknown',
      repo: config.repo || 'unknown',
      branch: config.branch || 'main',
      token: config.token
    });
  }

  analyzeCodeComplexity() {
    const analyzer = new analyzers.ComplexityAnalyzer();
    return analyzer.analyzeCodeComplexity(this.repoPath);
  }

  analyzeDependencies() {
    const analyzer = new analyzers.DependencyAnalyzer();
    return analyzer.analyzeDependencies(this.repoPath);
  }

  analyzeLicenses() {
    const analyzer = new analyzers.LicenseAnalyzer();
    return analyzer.analyzeLicenses(this.repoPath);
  }

  analyzePerformance() {
    const analyzer = new analyzers.PerformanceAnalyzer();
    return analyzer.analyzePerformance(this.repoPath);
  }

  analyzePR(prData: any) {
    const analyzer = new analyzers.PRReviewAnalyzer();
    return analyzer.analyzePR(prData);
  }

  analyzeContributors(contributorData: any) {
    const analyzer = new analyzers.ContributorAnalyzer();
    return analyzer.analyzeContributors(contributorData);
  }

  analyzeIssueTracker(issueData: any, prData: any) {
    const analyzer = new analyzers.IssueTrackerAnalyzer();
    return analyzer.analyzeIssueTracker(issueData, prData);
  }

  planMigration(migrationType: string) {
    const analyzer = new analyzers.MigrationPlanner();
    return analyzer.planMigration(this.repoPath, migrationType);
  }

  exportAnalysis(analysis: RepositoryAnalysis, outputPath: string): void {
    const json = JSON.stringify(analysis, null, 2);
    const fs = require('fs');
    fs.writeFileSync(outputPath, json, 'utf-8');
    console.log(`Analysis exported to ${outputPath}`);
  }

  generateMarkdownReport(analysis: RepositoryAnalysis): string {
    let markdown = '# Repository Analysis Report\n\n';
    markdown += `Generated: ${analysis.generatedAt.toISOString()}\n\n`;
    markdown += `Repository: ${analysis.repository.owner}/${analysis.repository.repo}\n\n`;
    
    markdown += '## Tech Stack\n\n';
    markdown += '### Languages\n\n';
    markdown += '| Language | Files | Lines | Percentage |\n';
    markdown += '|----------|-------|-------|------------|\n';
    for (const lang of analysis.techStack.languages) {
      markdown += `| ${lang.name} | ${lang.files} | ${lang.linesOfCode} | ${lang.percentage.toFixed(1)}% |\n`;
    }

    markdown += '\n## Dependencies\n\n';
    markdown += `Total Dependencies: ${analysis.dependencies.length}\n\n`;
    const vulnerable = analysis.dependencies.filter(d => d.vulnerabilities.length > 0);
    if (vulnerable.length > 0) {
      markdown += `### Vulnerabilities\n\n`;
      markdown += `**${vulnerable.length} dependencies with security issues**\n\n`;
    }

    markdown += '\n## Code Complexity\n\n';
    const critical = analysis.codeComplexity.filter(c => c.priority === 'critical');
    markdown += `Files analyzed: ${analysis.codeComplexity.length}\n\n`;
    if (critical.length > 0) {
      markdown += `### Critical Complexity (${critical.length} files)\n\n`;
      for (const file of critical.slice(0, 5)) {
        markdown += `- ${file.filePath} (Cyclomatic: ${file.complexity.cyclomaticComplexity})\n`;
      }
    }

    markdown += '\n## Performance Issues\n\n';
    markdown += `Total Issues: ${analysis.performanceIssues.length}\n\n`;
    if (analysis.performanceIssues.length > 0) {
      markdown += '| Type | Severity | Location |\n';
      markdown += '|------|----------|----------|\n';
      for (const issue of analysis.performanceIssues.slice(0, 10)) {
        markdown += `| ${issue.type} | ${issue.severity} | ${issue.location} |\n`;
      }
    }

    markdown += '\n## Recommendations\n\n';
    for (const rec of analysis.recommendations.slice(0, 10)) {
      markdown += `### ${rec.priority.toUpperCase()}: ${rec.category}\n\n`;
      markdown += `${rec.description}\n\n`;
      markdown += `- Estimated effort: ${rec.estimatedEffort}\n\n`;
    }

    return markdown;
  }
}

// Export types and analyzers
export * from './types';
export * from './analyzers';