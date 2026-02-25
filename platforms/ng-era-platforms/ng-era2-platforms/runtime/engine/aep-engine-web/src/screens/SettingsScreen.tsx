/**
 * @ECO-governed
 * @ECO-layer: aep-engine-web
 * @ECO-semantic: screens-SettingsScreen
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

interface SettingsScreenProps {
  darkMode: boolean;
  onDarkModeChange: (enabled: boolean) => void;
}

export function SettingsScreen({ darkMode, onDarkModeChange }: SettingsScreenProps) {
  return (
    <div className="min-h-screen bg-white dark:bg-slate-950">
      {/* Header */}
      <div className="bg-primary text-white px-6 pt-6 pb-8">
        <h1 className="text-2xl font-bold mb-2">Settings</h1>
        <p className="text-sm opacity-80">Configure application preferences</p>
      </div>

      {/* Content */}
      <div className="px-6 py-6 max-w-2xl mx-auto space-y-6">
        {/* Connection Settings */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground dark:text-foreground-dark">
            Connection Settings
          </h2>
          <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-border dark:border-border-dark space-y-4">
            <div>
              <label className="text-sm font-medium text-foreground dark:text-foreground-dark block mb-2">
                Elasticsearch Host
              </label>
              <input
                type="text"
                placeholder="localhost"
                className="w-full px-3 py-2 rounded-lg border border-border dark:border-border-dark bg-white dark:bg-slate-700 text-foreground dark:text-foreground-dark"
                disabled
              />
            </div>
            <div>
              <label className="text-sm font-medium text-foreground dark:text-foreground-dark block mb-2">
                Port
              </label>
              <input
                type="number"
                placeholder="9200"
                className="w-full px-3 py-2 rounded-lg border border-border dark:border-border-dark bg-white dark:bg-slate-700 text-foreground dark:text-foreground-dark"
                disabled
              />
            </div>
          </div>
        </div>

        {/* Governance Rules */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground dark:text-foreground-dark">
            Governance Rules
          </h2>
          <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-border dark:border-border-dark space-y-3">
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" defaultChecked className="w-4 h-4" />
              <span className="text-sm text-foreground dark:text-foreground-dark">
                Enable Schema Validation
              </span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" defaultChecked className="w-4 h-4" />
              <span className="text-sm text-foreground dark:text-foreground-dark">
                Check Metadata Completeness
              </span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" defaultChecked className="w-4 h-4" />
              <span className="text-sm text-foreground dark:text-foreground-dark">
                Enforce Naming Conventions
              </span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" defaultChecked className="w-4 h-4" />
              <span className="text-sm text-foreground dark:text-foreground-dark">
                Validate Directory Structure
              </span>
            </label>
          </div>
        </div>

        {/* Notification Preferences */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground dark:text-foreground-dark">
            Notification Preferences
          </h2>
          <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-border dark:border-border-dark space-y-3">
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" defaultChecked className="w-4 h-4" />
              <span className="text-sm text-foreground dark:text-foreground-dark">
                Critical Issues
              </span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" defaultChecked className="w-4 h-4" />
              <span className="text-sm text-foreground dark:text-foreground-dark">
                Audit Completion
              </span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" className="w-4 h-4" />
              <span className="text-sm text-foreground dark:text-foreground-dark">
                Weekly Reports
              </span>
            </label>
          </div>
        </div>

        {/* Appearance */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground dark:text-foreground-dark">
            Appearance
          </h2>
          <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-border dark:border-border-dark">
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-sm text-foreground dark:text-foreground-dark">Dark Mode</span>
              <button
                onClick={() => onDarkModeChange(!darkMode)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  darkMode ? 'bg-primary' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    darkMode ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </label>
          </div>
        </div>

        {/* About */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground dark:text-foreground-dark">
            About
          </h2>
          <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-border dark:border-border-dark space-y-2 text-sm text-muted dark:text-muted-dark">
            <p>
              <span className="font-medium">Application:</span> AEP Engine Governance & Audit
            </p>
            <p>
              <span className="font-medium">Version:</span> 1.0.0
            </p>
            <p>
              <span className="font-medium">Build:</span> Web Application
            </p>
            <p>
              <span className="font-medium">Last Updated:</span> {new Date().toLocaleDateString()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
