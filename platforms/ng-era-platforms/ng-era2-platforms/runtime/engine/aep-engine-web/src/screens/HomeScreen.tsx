/**
 * @ECO-governed
 * @ECO-layer: aep-engine-web
 * @ECO-semantic: screens-HomeScreen
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

import { StatisticCard } from '@/components/StatisticCard';
import { EventCard } from '@/components/EventCard';

interface HomeScreenProps {
  auditSummary: any;
  recentEvents: any[];
  onStartAudit: () => void;
}

export function HomeScreen({ auditSummary, recentEvents, onStartAudit }: HomeScreenProps) {
  return (
    <div className="min-h-screen bg-white dark:bg-slate-950">
      {/* Header */}
      <div className="bg-primary text-white px-6 pt-6 pb-8">
        <h1 className="text-3xl font-bold mb-2">AEP Engine</h1>
        <p className="text-sm opacity-80">Governance & Audit</p>
      </div>

      {/* Content */}
      <div className="px-6 py-6 max-w-6xl mx-auto space-y-6">
        {/* Statistics Cards */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground dark:text-foreground-dark">
            Latest Audit Summary
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

        {/* Recent Events */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground dark:text-foreground-dark">
            Recent Events
          </h2>
          <div className="space-y-2">
            {recentEvents.map((event) => (
              <EventCard
                key={event.id}
                type={event.type}
                time={event.time}
                status={event.status}
              />
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground dark:text-foreground-dark">
            Quick Actions
          </h2>
          <button
            onClick={onStartAudit}
            className="w-full bg-primary text-white rounded-xl p-4 hover:opacity-90 transition-opacity font-semibold"
          >
            Start New Audit
          </button>
          <div className="grid grid-cols-2 gap-3">
            <button className="bg-white dark:bg-slate-800 text-foreground dark:text-foreground-dark rounded-xl p-4 border border-border dark:border-border-dark hover:shadow-md transition-shadow font-medium">
              View Report
            </button>
            <button className="bg-white dark:bg-slate-800 text-foreground dark:text-foreground-dark rounded-xl p-4 border border-border dark:border-border-dark hover:shadow-md transition-shadow font-medium">
              Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
