/**
 * @ECO-governed
 * @ECO-layer: aep-engine-web
 * @ECO-semantic: screens-AuditScreen
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

interface AuditScreenProps {
  etlStages: any[];
  files: any[];
  logs: string[];
  isRunning: boolean;
}

export function AuditScreen({ etlStages, files, logs, isRunning }: AuditScreenProps) {
  return (
    <div className="min-h-screen bg-white dark:bg-slate-950">
      {/* Header */}
      <div className="bg-primary text-white px-6 pt-6 pb-8">
        <h1 className="text-2xl font-bold mb-2">Audit Execution</h1>
        <p className="text-sm opacity-80">Monitor ETL Pipeline & File Execution</p>
      </div>

      {/* Content */}
      <div className="px-6 py-6 max-w-6xl mx-auto space-y-6">
        {/* ETL Pipeline Progress */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground dark:text-foreground-dark">
            ETL Pipeline Progress
          </h2>
          <div className="space-y-3">
            {etlStages.map((stage) => (
              <div key={stage.name} className="space-y-1">
                <div className="flex justify-between items-center">
                  <p className="text-sm font-medium text-foreground dark:text-foreground-dark">
                    {stage.name}
                  </p>
                  <p className="text-xs text-muted dark:text-muted-dark">{stage.progress}%</p>
                </div>
                <div className="w-full bg-surface dark:bg-surface-dark rounded-full h-2">
                  <div
                    className="bg-primary rounded-full h-2 transition-all"
                    style={{ width: `${stage.progress}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* File Execution */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground dark:text-foreground-dark">
            File Execution
          </h2>
          <div className="space-y-2">
            {files.map((file) => (
              <div
                key={file.id}
                className="bg-white dark:bg-slate-800 rounded-lg p-3 border border-border dark:border-border-dark flex items-center justify-between"
              >
                <div className="flex items-center gap-2 flex-1">
                  <span className={`text-lg ${
                    file.status === 'completed' ? '✓' :
                    file.status === 'running' ? '⏳' : '⏸'
                  }`}></span>
                  <div>
                    <p className="text-sm font-medium text-foreground dark:text-foreground-dark">
                      {file.name}
                    </p>
                  </div>
                </div>
                <p className="text-xs text-muted dark:text-muted-dark">{file.time}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Logs */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground dark:text-foreground-dark">
            Execution Logs
          </h2>
          <div className="bg-slate-900 dark:bg-slate-950 rounded-lg p-4 font-mono text-xs text-green-400 overflow-auto max-h-64 space-y-1">
            {logs.map((log, idx) => (
              <div key={idx} className="whitespace-pre-wrap">{log}</div>
            ))}
          </div>
        </div>

        {/* Control */}
        <div className="flex gap-3">
          <button className="flex-1 bg-primary text-white rounded-xl p-3 hover:opacity-90 transition-opacity font-semibold">
            {isRunning ? 'Stop Execution' : 'Start Execution'}
          </button>
          <button className="flex-1 bg-white dark:bg-slate-800 text-foreground dark:text-foreground-dark rounded-xl p-3 border border-border dark:border-border-dark hover:shadow-md transition-shadow font-semibold">
            View Details
          </button>
        </div>
      </div>
    </div>
  );
}
