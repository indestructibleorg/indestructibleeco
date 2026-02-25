/**
 * @ECO-governed
 * @ECO-layer: aep-engine-web
 * @ECO-semantic: screens-ResultsScreen
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

import { ProblemCard } from '@/components/ProblemCard';

interface ResultsScreenProps {
  problems: any[];
  severityDistribution: any[];
  selectedSeverity: string | null;
  onSeverityChange: (severity: string | null) => void;
}

export function ResultsScreen({
  problems,
  severityDistribution,
  selectedSeverity,
  onSeverityChange,
}: ResultsScreenProps) {
  return (
    <div className="min-h-screen bg-white dark:bg-slate-950">
      {/* Header */}
      <div className="bg-primary text-white px-6 pt-6 pb-8">
        <h1 className="text-2xl font-bold mb-2">Detection Results</h1>
        <p className="text-sm opacity-80">Review governance issues and recommendations</p>
      </div>

      {/* Content */}
      <div className="px-6 py-6 max-w-6xl mx-auto space-y-6">
        {/* Severity Filter */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground dark:text-foreground-dark">
            Severity Distribution
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <button
              onClick={() => onSeverityChange(null)}
              className={`rounded-lg p-3 text-sm font-medium transition-all ${
                selectedSeverity === null
                  ? 'bg-primary text-white'
                  : 'bg-white dark:bg-slate-800 text-foreground dark:text-foreground-dark border border-border dark:border-border-dark'
              }`}
            >
              All ({problems.length})
            </button>
            {severityDistribution.map((dist) => (
              <button
                key={dist.severity}
                onClick={() => onSeverityChange(dist.severity.toLowerCase())}
                className={`rounded-lg p-3 text-sm font-medium transition-all ${
                  selectedSeverity === dist.severity.toLowerCase()
                    ? 'bg-primary text-white'
                    : 'bg-white dark:bg-slate-800 text-foreground dark:text-foreground-dark border border-border dark:border-border-dark'
                }`}
              >
                {dist.severity} ({dist.count})
              </button>
            ))}
          </div>
        </div>

        {/* Problems List */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground dark:text-foreground-dark">
            Issues
          </h2>
          <div className="space-y-3">
            {problems.length > 0 ? (
              problems.map((problem) => (
                <ProblemCard
                  key={problem.id}
                  type={problem.type}
                  severity={problem.severity}
                  description={problem.description}
                  location={problem.location}
                  suggestion={problem.suggestion}
                />
              ))
            ) : (
              <div className="text-center py-8">
                <p className="text-muted dark:text-muted-dark">No issues found</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
