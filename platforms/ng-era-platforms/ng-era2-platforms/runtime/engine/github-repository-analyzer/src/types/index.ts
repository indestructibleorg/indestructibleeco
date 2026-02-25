// @ECO-governed
// @ECO-layer: GL20-29
// @ECO-semantic: github-analysis-types
// @ECO-audit-trail: ../../governance/GL_SEMANTIC_ANCHOR.json

export interface RepositoryConfig {
  owner: string;
  repo: string;
  branch?: string;
  token?: string;
}

export interface TechStack {
  languages: LanguageStats[];
  frameworks: Framework[];
  buildTools: string[];
  packageManagers: string[];
}

export interface LanguageStats {
  name: string;
  files: number;
  linesOfCode: number;
  percentage: number;
}

export interface Framework {
  name: string;
  version?: string;
  detectionFiles: string[];
}

export interface Dependency {
  name: string;
  version: string;
  type: 'npm' | 'pip' | 'maven' | 'gradle' | 'cargo' | 'go' | 'composer';
  vulnerabilities: Vulnerability[];
  outdated: boolean;
  latestVersion?: string;
}

export interface Vulnerability {
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  patchedIn?: string;
}

export interface CodeComplexityMetrics {
  cyclomaticComplexity: number;
  linesOfCode: number;
  functionLength: number;
  nestingDepth: number;
  duplication: number;
}

export interface FileComplexity {
  filePath: string;
  language: string;
  complexity: CodeComplexityMetrics;
  priority: 'low' | 'medium' | 'high' | 'critical';
}

export interface LicenseInfo {
  type: string;
  compatible: boolean;
  gplOrCopyleft: boolean;
  risk: 'low' | 'medium' | 'high' | 'critical';
  description: string;
}

export interface PerformanceIssue {
  type: string;
  location: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  recommendation: string;
}

export interface PRReview {
  prNumber: number;
  title: string;
  author: string;
  changes: number;
  filesChanged: number;
  bugsFound: number;
  securityIssues: number;
  qualityIssues: number;
  suggestions: string[];
  testCoverage: number;
  overallAssessment: 'excellent' | 'good' | 'acceptable' | 'needs-improvement';
}

export interface ContributorActivity {
  login: string;
  commits: number;
  prsOpened: number;
  prsReviewed: number;
  issuesTrialed: number;
  codeAdditions: number;
  codeDeletions: number;
  lastActiveDate: Date;
  engagement: 'core' | 'active' | 'moderate' | 'declining';
}

export interface IssueTrackerMetrics {
  openIssues: number;
  closedIssues: number;
  openPRs: number;
  mergedPRs: number;
  avgResolutionTime: number;
  commonLabels: LabelStat[];
  staleIssues: number;
  mergeRate: number;
}

export interface LabelStat {
  name: string;
  count: number;
  percentage: number;
}

export interface MigrationPlan {
  sourceFramework: string;
  targetFramework: string;
  filesToChange: string[];
  estimatedEffort: 'low' | 'medium' | 'high' | 'very-high';
  breakingChanges: string[];
  steps: MigrationStep[];
}

export interface MigrationStep {
  step: number;
  description: string;
  files: string[];
  codeExample?: string;
  estimatedTime: string;
}

export interface RepositoryAnalysis {
  repository: RepositoryConfig;
  techStack: TechStack;
  dependencies: Dependency[];
  codeComplexity: FileComplexity[];
  licenses: LicenseInfo[];
  performanceIssues: PerformanceIssue[];
  documentation: DocumentationQuality;
  testCoverage: TestCoverage;
  contributors: ContributorActivity[];
  issueMetrics: IssueTrackerMetrics;
  recommendations: Recommendation[];
  generatedAt: Date;
}

export interface DocumentationQuality {
  readmeExists: boolean;
  apiDocumentationExists: boolean;
  contributionGuidesExist: boolean;
  architectureDocsExist: boolean;
  setupInstructions: boolean;
  codeExamples: boolean;
  score: number;
}

export interface TestCoverage {
  overall: number;
  unitTests: number;
  integrationTests: number;
  e2eTests: number;
  frameworks: string[];
}

export interface Recommendation {
  category: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  actionable: boolean;
  estimatedEffort: string;
}

export interface AnalysisResult {
  type: 'structure' | 'complexity' | 'documentation' | 'dependencies' | 'licenses' | 'performance' | 'pr-review' | 'contributors' | 'issues' | 'migration';
  summary: string;
  data: any;
  insights: string[];
  recommendations: Recommendation[];
  generatedAt: Date;
}