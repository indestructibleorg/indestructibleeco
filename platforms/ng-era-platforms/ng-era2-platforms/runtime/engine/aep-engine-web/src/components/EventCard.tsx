/**
 * @ECO-governed
 * @ECO-layer: aep-engine-web
 * @ECO-semantic: components-EventCard
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

import clsx from 'clsx';

interface EventCardProps {
  type: 'Execution' | 'Detection' | 'Rollback' | 'Migration' | 'Validation';
  time: string;
  status: 'success' | 'warning' | 'error' | 'info';
}

export function EventCard({ type, time, status }: EventCardProps) {
  const statusColorMap = {
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500',
    info: 'bg-blue-500',
  };

  const typeIconMap = {
    Execution: '▶️',
    Detection: '🔍',
    Rollback: '↩️',
    Migration: '📦',
    Validation: '✓',
  };

  return (
    <button className="w-full bg-white dark:bg-slate-800 rounded-lg p-4 border border-border dark:border-border-dark flex items-center gap-3 hover:opacity-70 transition-opacity text-left">
      <div className={clsx('w-2 h-2 rounded-full', statusColorMap[status])} />
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm">{typeIconMap[type]}</span>
          <p className="text-sm font-medium text-foreground dark:text-foreground-dark">{type}</p>
        </div>
        <p className="text-xs text-muted dark:text-muted-dark">{time}</p>
      </div>
      <span className="text-lg text-muted dark:text-muted-dark">→</span>
    </button>
  );
}
