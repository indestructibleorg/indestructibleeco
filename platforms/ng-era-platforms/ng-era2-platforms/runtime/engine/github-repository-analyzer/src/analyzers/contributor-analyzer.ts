// @ECO-governed
// @ECO-layer: GL20-29
// @ECO-semantic: contributor-analyzer
// @ECO-audit-trail: ../../governance/GL_SEMANTIC_ANCHOR.json

import { ContributorActivity, AnalysisResult, Recommendation } from '../types';

export class ContributorAnalyzer {
  analyzeContributors(contributorData: any): AnalysisResult {
    const contributors = this.processContributorData(contributorData);
    const leaderboard = this.generateLeaderboard(contributors);
    const coreMaintainers = this.identifyCoreMaintainers(contributors);
    const decliningContributors = this.detectDecliningEngagement(contributors);
    const insights = this.generateInsights(contributors);

    return {
      type: 'contributors',
      summary: `Contributor analysis complete. ${contributors.length} contributors analyzed. ${coreMaintainers.length} core maintainers identified.`,
      data: {
        contributors,
        leaderboard,
        coreMaintainers,
        decliningContributors,
        insights
      },
      insights,
      recommendations: this.generateRecommendations(contributors, decliningContributors),
      generatedAt: new Date()
    };
  }

  private processContributorData(data: any): ContributorActivity[] {
    const contributors: ContributorActivity[] = [];
    const contributorMap = new Map<string, ContributorActivity>();

    // Process commits
    const commits = data.commits || [];
    for (const commit of commits) {
      const login = commit.author?.login || commit.committer?.login || 'Unknown';
      if (!contributorMap.has(login)) {
        contributorMap.set(login, {
          login,
          commits: 0,
          prsOpened: 0,
          prsReviewed: 0,
          issuesTrialed: 0,
          codeAdditions: 0,
          codeDeletions: 0,
          lastActiveDate: new Date(commit.commit?.author?.date || Date.now()),
          engagement: 'moderate'
        });
      }
      const contributor = contributorMap.get(login)!;
      contributor.commits++;
      contributor.codeAdditions += commit.additions || 0;
      contributor.codeDeletions += commit.deletions || 0;
      
      const commitDate = new Date(commit.commit?.author?.date || Date.now());
      if (commitDate > contributor.lastActiveDate) {
        contributor.lastActiveDate = commitDate;
      }
    }

    // Process PRs
    const prs = data.prs || [];
    for (const pr of prs) {
      const login = pr.user?.login || 'Unknown';
      if (!contributorMap.has(login)) {
        contributorMap.set(login, {
          login,
          commits: 0,
          prsOpened: 0,
          prsReviewed: 0,
          issuesTrialed: 0,
          codeAdditions: 0,
          codeDeletions: 0,
          lastActiveDate: new Date(pr.created_at || Date.now()),
          engagement: 'moderate'
        });
      }
      const contributor = contributorMap.get(login)!;
      contributor.prsOpened++;
      
      const prDate = new Date(pr.created_at || Date.now());
      if (prDate > contributor.lastActiveDate) {
        contributor.lastActiveDate = prDate;
      }
    }

    // Process PR reviews
    const reviews = data.reviews || [];
    for (const review of reviews) {
      const login = review.user?.login || 'Unknown';
      if (!contributorMap.has(login)) {
        contributorMap.set(login, {
          login,
          commits: 0,
          prsOpened: 0,
          prsReviewed: 0,
          issuesTrialed: 0,
          codeAdditions: 0,
          codeDeletions: 0,
          lastActiveDate: new Date(review.submitted_at || Date.now()),
          engagement: 'moderate'
        });
      }
      const contributor = contributorMap.get(login)!;
      contributor.prsReviewed++;
      
      const reviewDate = new Date(review.submitted_at || Date.now());
      if (reviewDate > contributor.lastActiveDate) {
        contributor.lastActiveDate = reviewDate;
      }
    }

    // Process issues
    const issues = data.issues || [];
    for (const issue of issues) {
      const login = issue.user?.login || 'Unknown';
      if (!contributorMap.has(login)) {
        contributorMap.set(login, {
          login,
          commits: 0,
          prsOpened: 0,
          prsReviewed: 0,
          issuesTrialed: 0,
          codeAdditions: 0,
          codeDeletions: 0,
          lastActiveDate: new Date(issue.created_at || Date.now()),
          engagement: 'moderate'
        });
      }
      const contributor = contributorMap.get(login)!;
      contributor.issuesTrialed++;
      
      const issueDate = new Date(issue.created_at || Date.now());
      if (issueDate > contributor.lastActiveDate) {
        contributor.lastActiveDate = issueDate;
      }
    }

    // Determine engagement level
    for (const contributor of contributorMap.values()) {
      contributor.engagement = this.determineEngagement(contributor);
    }

    return Array.from(contributorMap.values());
  }

  private determineEngagement(contributor: ContributorActivity): 'core' | 'active' | 'moderate' | 'declining' {
    const score = 
      (contributor.commits * 2) +
      (contributor.prsOpened * 3) +
      (contributor.prsReviewed * 2) +
      (contributor.issuesTrialed);

    const daysSinceLastActive = (Date.now() - contributor.lastActiveDate.getTime()) / (1000 * 60 * 60 * 24);

    if (score >= 100 && daysSinceLastActive < 30) return 'core';
    if (score >= 50 && daysSinceLastActive < 60) return 'active';
    if (score >= 10 && daysSinceLastActive < 90) return 'moderate';
    return 'declining';
  }

  private generateLeaderboard(contributors: ContributorActivity[]): any[] {
    return contributors
      .map(c => ({
        login: c.login,
        score: (c.commits * 2) + (c.prsOpened * 3) + (c.prsReviewed * 2) + c.issuesTrialed,
        commits: c.commits,
        prsOpened: c.prsOpened,
        prsReviewed: c.prsReviewed
      }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 10);
  }

  private identifyCoreMaintainers(contributors: ContributorActivity[]): ContributorActivity[] {
    return contributors
      .filter(c => c.engagement === 'core')
      .sort((a, b) => b.commits - a.commits);
  }

  private detectDecliningEngagement(contributors: ContributorActivity[]): ContributorActivity[] {
    return contributors
      .filter(c => c.engagement === 'declining')
      .sort((a, b) => a.lastActiveDate.getTime() - b.lastActiveDate.getTime());
  }

  private generateInsights(contributors: ContributorActivity[]): string[] {
    const insights: string[] = [];
    
    const totalContributors = contributors.length;
    const coreMaintainers = contributors.filter(c => c.engagement === 'core').length;
    const activeContributors = contributors.filter(c => c.engagement === 'active').length;
    const decliningContributors = contributors.filter(c => c.engagement === 'declining').length;

    const totalCommits = contributors.reduce((sum, c) => sum + c.commits, 0);
    const totalPRs = contributors.reduce((sum, c) => sum + c.prsOpened, 0);
    const totalReviews = contributors.reduce((sum, c) => sum + c.prsReviewed, 0);

    insights.push(`${totalContributors} total contributors over the past year`);
    insights.push(`${coreMaintainers} core maintainers identified (${((coreMaintainers / totalContributors) * 100).toFixed(1)}%)`);
    insights.push(`${activeContributors} active contributors`);
    insights.push(`${decliningContributors} contributors showing declining engagement`);
    insights.push(`${totalCommits} total commits, ${totalPRs} PRs opened, ${totalReviews} PRs reviewed`);
    insights.push(`Average ${Math.round(totalCommits / totalContributors)} commits per contributor`);

    const topContributor = contributors.reduce((max, c) => c.commits > max.commits ? c : max, contributors[0]);
    if (topContributor) {
      insights.push(`Top contributor: ${topContributor.login} with ${topContributor.commits} commits`);
    }

    return insights;
  }

  private generateRecommendations(contributors: ContributorActivity[], declining: ContributorActivity[]): Recommendation[] {
    const recommendations: Recommendation[] = [];

    const decliningCount = declining.length;
    const total = contributors.length;
    const decliningPercentage = (decliningCount / total) * 100;

    if (decliningCount > 0 && decliningPercentage > 10) {
      recommendations.push({
        category: 'engagement',
        priority: 'high',
        description: `${decliningCount} contributors (${decliningPercentage.toFixed(1)}%) showing declining engagement`,
        actionable: true,
        estimatedEffort: '2-4 hours per contributor'
      });
    }

    const coreMaintainers = contributors.filter(c => c.engagement === 'core');
    if (coreMaintainers.length < 3) {
      recommendations.push({
        category: 'sustainability',
        priority: 'high',
        description: 'Only ' + coreMaintainers.length + ' core maintainers - consider recruiting more',
        actionable: true,
        estimatedEffort: '1-2 weeks'
      });
    }

    recommendations.push({
      category: 'onboarding',
      priority: 'medium',
      description: 'Improve onboarding process to retain new contributors',
      actionable: true,
      estimatedEffort: '1-2 days'
    });

    recommendations.push({
      category: 'recognition',
      priority: 'low',
      description: 'Implement contributor recognition program',
      actionable: true,
      estimatedEffort: '2-4 hours'
    });

    return recommendations;
  }
}