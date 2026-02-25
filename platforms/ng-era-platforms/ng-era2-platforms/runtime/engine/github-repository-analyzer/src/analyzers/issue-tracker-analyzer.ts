// @ECO-governed
// @ECO-layer: GL20-29
// @ECO-semantic: issue-tracker-analyzer
// @ECO-audit-trail: ../../governance/GL_SEMANTIC_ANCHOR.json

import { IssueTrackerMetrics, LabelStat, AnalysisResult, Recommendation } from '../types';

export class IssueTrackerAnalyzer {
  analyzeIssueTracker(issueData: any, prData: any): AnalysisResult {
    const metrics = this.calculateMetrics(issueData, prData);
    const insights = this.generateInsights(metrics);
    const healthAssessment = this.assessProjectHealth(metrics);

    return {
      type: 'issues',
      summary: `Issue tracker analysis complete. ${metrics.openIssues} open issues, ${metrics.mergedPRs}/${metrics.openPRs} merged PRs. Avg resolution time: ${metrics.avgResolutionTime} days`,
      data: {
        metrics,
        insights,
        healthAssessment
      },
      insights,
      recommendations: this.generateRecommendations(metrics, healthAssessment),
      generatedAt: new Date()
    };
  }

  private calculateMetrics(issueData: any, prData: any): IssueTrackerMetrics {
    const issues = issueData.issues || [];
    const prs = prData.prs || [];

    // Calculate issue metrics
    const openIssues = issues.filter((i: any) => i.state === 'open').length;
    const closedIssues = issues.filter((i: any) => i.state === 'closed').length;

    // Calculate resolution time
    const closedWithDates = issues.filter((i: any) => 
      i.state === 'closed' && i.created_at && i.closed_at
    );
    
    let totalResolutionTime = 0;
    for (const issue of closedWithDates) {
      const created = new Date(issue.created_at);
      const closed = new Date(issue.closed_at);
      totalResolutionTime += (closed.getTime() - created.getTime()) / (1000 * 60 * 60 * 24);
    }

    const avgResolutionTime = closedWithDates.length > 0 
      ? Math.round(totalResolutionTime / closedWithDates.length) 
      : 0;

    // Calculate common labels
    const labelCounts = new Map<string, number>();
    for (const issue of issues) {
      const labels = issue.labels || [];
      for (const label of labels) {
        const name = label.name || label;
        labelCounts.set(name, (labelCounts.get(name) || 0) + 1);
      }
    }

    const totalIssuesWithLabels = issues.filter((i: any) => (i.labels || []).length > 0).length;
    const commonLabels: LabelStat[] = Array.from(labelCounts.entries())
      .map(([name, count]) => ({
        name,
        count,
        percentage: totalIssuesWithLabels > 0 ? (count / totalIssuesWithLabels) * 100 : 0
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    // Calculate stale issues (older than 90 days without activity)
    const ninetyDaysAgo = new Date();
    ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);

    const staleIssues = issues.filter((i: any) => {
      if (i.state !== 'open') return false;
      const lastUpdate = new Date(i.updated_at || i.created_at);
      return lastUpdate < ninetyDaysAgo;
    }).length;

    // Calculate PR metrics
    const openPRs = prs.filter((p: any) => p.state === 'open').length;
    const mergedPRs = prs.filter((p: any) => p.merged_at).length;
    const mergeRate = prs.length > 0 ? (mergedPRs / prs.length) * 100 : 0;

    // Calculate community engagement
    const uniqueCommenters = new Set<string>();
    for (const issue of issues) {
      const comments = issue.comments || [];
      for (const comment of comments) {
        if (comment.user?.login) {
          uniqueCommenters.add(comment.user.login);
        }
      }
    }

    return {
      openIssues,
      closedIssues,
      openPRs,
      mergedPRs,
      avgResolutionTime,
      commonLabels,
      staleIssues,
      mergeRate
    };
  }

  private generateInsights(metrics: IssueTrackerMetrics): string[] {
    const insights: string[] = [];

    const totalIssues = metrics.openIssues + metrics.closedIssues;
    const closureRate = totalIssues > 0 ? (metrics.closedIssues / totalIssues) * 100 : 0;

    insights.push(`Issue closure rate: ${closureRate.toFixed(1)}%`);
    insights.push(`Average resolution time: ${metrics.avgResolutionTime} days`);
    insights.push(`PR merge rate: ${metrics.mergeRate.toFixed(1)}%`);
    insights.push(`${metrics.staleIssues} stale issues (>90 days without activity)`);

    if (metrics.commonLabels.length > 0) {
      const topLabel = metrics.commonLabels[0];
      insights.push(`Most common label: "${topLabel.name}" (${topLabel.count} issues, ${topLabel.percentage.toFixed(1)}%)`);
    }

    if (metrics.avgResolutionTime > 30) {
      insights.push('Issue resolution time is high - consider improving triage process');
    }

    if (metrics.mergeRate < 70) {
      insights.push('Low PR merge rate - review process may need improvement');
    }

    if (metrics.staleIssues > metrics.openIssues * 0.3) {
      insights.push('High number of stale issues - implement stale issue automation');
    }

    return insights;
  }

  private assessProjectHealth(metrics: IssueTrackerMetrics): any {
    let healthScore = 100;
    const issues: string[] = [];

    // Assess issue backlog
    const backlogRatio = metrics.openIssues / (metrics.closedIssues + metrics.openIssues);
    if (backlogRatio > 0.5) {
      healthScore -= 20;
      issues.push('High issue backlog');
    } else if (backlogRatio > 0.3) {
      healthScore -= 10;
      issues.push('Moderate issue backlog');
    }

    // Assess resolution time
    if (metrics.avgResolutionTime > 60) {
      healthScore -= 25;
      issues.push('Very slow issue resolution');
    } else if (metrics.avgResolutionTime > 30) {
      healthScore -= 15;
      issues.push('Slow issue resolution');
    }

    // Assess stale issues
    const staleRatio = metrics.staleIssues / metrics.openIssues;
    if (staleRatio > 0.5) {
      healthScore -= 20;
      issues.push('Many stale issues');
    } else if (staleRatio > 0.3) {
      healthScore -= 10;
      issues.push('Some stale issues');
    }

    // Assess PR merge rate
    if (metrics.mergeRate < 50) {
      healthScore -= 20;
      issues.push('Low PR merge rate');
    } else if (metrics.mergeRate < 70) {
      healthScore -= 10;
      issues.push('Moderate PR merge rate');
    }

    const healthLevel = healthScore >= 80 ? 'excellent' :
                      healthScore >= 60 ? 'good' :
                      healthScore >= 40 ? 'acceptable' : 'needs-improvement';

    return {
      score: Math.max(0, healthScore),
      level: healthLevel,
      issues,
      bottlenecks: this.identifyBottlenecks(metrics)
    };
  }

  private identifyBottlenecks(metrics: IssueTrackerMetrics): string[] {
    const bottlenecks: string[] = [];

    if (metrics.avgResolutionTime > 30) {
      bottlenecks.push('Issue triage and resolution process');
    }

    if (metrics.mergeRate < 70) {
      bottlenecks.push('PR review process');
    }

    if (metrics.staleIssues > metrics.openIssues * 0.3) {
      bottlenecks.push('Issue maintenance and triage');
    }

    const topLabel = metrics.commonLabels[0];
    if (topLabel && topLabel.percentage > 30) {
      bottlenecks.push(`Issues with "${topLabel.name}" label`);
    }

    return bottlenecks;
  }

  private generateRecommendations(metrics: IssueTrackerMetrics, health: any): Recommendation[] {
    const recommendations: Recommendation[] = [];

    // Issue management recommendations
    if (metrics.avgResolutionTime > 30) {
      recommendations.push({
        category: 'process',
        priority: 'high',
        description: 'Implement automated triage and assignment to reduce resolution time',
        actionable: true,
        estimatedEffort: '2-4 hours'
      });
    }

    if (metrics.staleIssues > 0) {
      recommendations.push({
        category: 'maintenance',
        priority: 'medium',
        description: `Close or update ${metrics.staleIssues} stale issues`,
        actionable: true,
        estimatedEffort: '2-4 hours'
      });
    }

    if (metrics.mergeRate < 70) {
      recommendations.push({
        category: 'process',
        priority: 'high',
        description: 'Streamline PR review process with automated checks and reviewer assignment',
        actionable: true,
        estimatedEffort: '1-2 days'
      });
    }

    if (metrics.commonLabels.length > 0) {
      const topLabel = metrics.commonLabels[0];
      if (topLabel.percentage > 20) {
        recommendations.push({
          category: 'organization',
          priority: 'medium',
          description: `Address high volume of "${topLabel.name}" issues (${topLabel.percentage.toFixed(1)}%)`,
          actionable: true,
          estimatedEffort: '1-2 days'
        });
      }
    }

    // General recommendations
    recommendations.push({
      category: 'automation',
      priority: 'low',
      description: 'Implement issue and PR automation (labels, assignments, stale detection)',
      actionable: true,
      estimatedEffort: '2-4 hours'
    });

    recommendations.push({
      category: 'community',
      priority: 'low',
      description: 'Create contributor guidelines to improve community engagement',
      actionable: true,
      estimatedEffort: '2-4 hours'
    });

    if (health.score < 60) {
      recommendations.push({
        category: 'health',
        priority: 'high',
        description: 'Address project health issues to maintain momentum',
        actionable: true,
        estimatedEffort: '1-2 weeks'
      });
    }

    return recommendations;
  }
}