/**
 * @ECO-governed
 * @ECO-layer: aep-engine-web
 * @ECO-semantic: screens-ReportScreen
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

import { StatisticCard } from '@/components/StatisticCard';

interface ReportScreenProps {
  auditSummary: any;
  problemTypes: any[];
  recommendations: any[];
}

export function ReportScreen({
  auditSummary,
  problemTypes,
  recommendations,
}: ReportScreenProps) {
  return (
    <div className="min-h-screen bg-white dark:bg-slate-950">
      {/* Header */}
      <div className="bg-primary text-white px-6 pt-6 pb-8">
        <h1 className="text-2xl font-bold mb-2">Global Report</h1>
        <p className="text-sm opacity-80">Comprehensive governance audit summary</p>
      </div>

      {/* Content */}
      <div className="px-6 py-6 max-w-6xl mx-auto space-y-6">
        {/* Summary Statistics */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground dark:text-foreground-dark">
            Report Summary
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <StatisticCard
              label="Total Detections"
              value={auditSummary.totalDetections}
              icon="📊"
              variant="default"
            />
            <StatisticCard
              label="Issues Found"
              value={auditSummary.failedChecks}
              icon="⚠️"
              variant="error"
            />
            <StatisticCard
              label="Pass Rate"
              value={`${auditSummary.passRate}%`}
              icon="✓"
              variant="success"
            />
          </div>
        </div>

        {/* Problem Types Distribution */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground dark:text-foreground-dark">
            Problem Types Distribution
          </h2>
          <div className="space-y-2">
            {problemTypes.map((type) => (
              <div
                key={type.type}
                className="bg-white dark:bg-slate-800 rounded-lg p-3 border border-border dark:border-border-dark"
              >
                <div className="flex justify-between items-center mb-2">
                  <p className="text-sm font-medium text-foreground dark:text-foreground-dark">
                    {type.type}
                  </p>
                  <p className="text-sm font-semibold text-primary">{type.count}</p>
                </div>
                <div className="w-full bg-surface dark:bg-surface-dark rounded-full h-2">
                  <div
                    className="bg-primary rounded-full h-2"
                    style={{ width: `${(type.count / Math.max(...problemTypes.map((t) => t.count))) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground dark:text-foreground-dark">
            Recommendations
          </h2>
          <div className="space-y-3">
            {recommendations.map((rec) => (
              <div
                key={rec.id}
                className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-border dark:border-border-dark"
              >
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-sm font-semibold text-foreground dark:text-foreground-dark">
                    {rec.title}
                  </h3>
                  <span className={`text-xs font-semibold px-2 py-1 rounded ${
                    rec.impact === 'High'
                      ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                      : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
                  }`}>
                    {rec.impact} Impact
                  </span>
                </div>
                <p className="text-sm text-muted dark:text-muted-dark">{rec.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Export Actions */}
        <div className="flex gap-3">
          <button className="flex-1 bg-primary text-white rounded-xl p-3 hover:opacity-90 transition-opacity font-semibold">
            Export as JSON
          </button>
          <button className="flex-1 bg-white dark:bg-slate-800 text-foreground dark:text-foreground-dark rounded-xl p-3 border border-border dark:border-border-dark hover:shadow-md transition-shadow font-semibold">
            Export as PDF
          </button>
        </div>
      </div>
    </div>
  );
}
