/**
 * @ECO-governed
 * @ECO-layer: aep-engine-web
 * @ECO-semantic: components-ProblemCard
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

import clsx from 'clsx';

type ProblemSeverity = 'critical' | 'high' | 'medium' | 'low';

interface ProblemCardProps {
  type: string;
  severity: ProblemSeverity;
  description: string;
  location?: string;
  suggestion?: string;
}

export function ProblemCard({
  type,
  severity,
  description,
  location,
  suggestion,
}: ProblemCardProps) {
  const severityConfig = {
    critical: { color: 'bg-red-600', label: 'Critical', icon: '🔴' },
    high: { color: 'bg-orange-600', label: 'High', icon: '🟠' },
    medium: { color: 'bg-yellow-600', label: 'Medium', icon: '🟡' },
    low: { color: 'bg-blue-600', label: 'Low', icon: '🔵' },
  };

  const config = severityConfig[severity];

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-border dark:border-border-dark hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2 flex-1">
          <span className="text-lg">{config.icon}</span>
          <div>
            <p className="text-sm font-medium text-foreground dark:text-foreground-dark">{type}</p>
            <p className={clsx('text-xs font-semibold', {
              'text-red-600': severity === 'critical',
              'text-orange-600': severity === 'high',
              'text-yellow-600': severity === 'medium',
              'text-blue-600': severity === 'low',
            })}>
              {config.label}
            </p>
          </div>
        </div>
        <span className="text-lg text-muted dark:text-muted-dark">→</span>
      </div>

      <p className="text-sm text-foreground dark:text-foreground-dark mb-2">{description}</p>

      {location && (
        <p className="text-xs text-muted dark:text-muted-dark mb-2">{location}</p>
      )}

      {suggestion && (
        <div className="mt-3 pt-3 border-t border-border dark:border-border-dark">
          <p className="text-xs text-muted dark:text-muted-dark mb-1">Suggestion:</p>
          <p className="text-sm text-foreground dark:text-foreground-dark">{suggestion}</p>
        </div>
      )}
    </div>
  );
}
