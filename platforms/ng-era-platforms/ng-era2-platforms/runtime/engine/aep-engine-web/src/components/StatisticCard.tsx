/**
 * @ECO-governed
 * @ECO-layer: aep-engine-web
 * @ECO-semantic: components-StatisticCard
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

import clsx from 'clsx';

interface StatisticCardProps {
  label: string;
  value: string | number;
  icon?: string;
  variant?: 'default' | 'success' | 'warning' | 'error';
}

export function StatisticCard({
  label,
  value,
  icon = '📊',
  variant = 'default',
}: StatisticCardProps) {
  const variantStyles = {
    default: 'bg-blue-100 dark:bg-blue-900',
    success: 'bg-green-100 dark:bg-green-900',
    warning: 'bg-yellow-100 dark:bg-yellow-900',
    error: 'bg-red-100 dark:bg-red-900',
  };

  const valueColorStyles = {
    default: 'text-foreground dark:text-foreground-dark',
    success: 'text-green-600 dark:text-green-400',
    warning: 'text-yellow-600 dark:text-yellow-400',
    error: 'text-red-600 dark:text-red-400',
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-border dark:border-border-dark flex justify-between items-center shadow-sm hover:shadow-md transition-shadow">
      <div>
        <p className="text-sm text-muted dark:text-muted-dark mb-1">{label}</p>
        <p className={clsx('text-3xl font-bold', valueColorStyles[variant])}>
          {value}
        </p>
      </div>
      <div className={clsx('rounded-lg p-3', variantStyles[variant])}>
        <span className="text-2xl">{icon}</span>
      </div>
    </div>
  );
}
