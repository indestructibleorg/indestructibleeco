/**
 * @ECO-governed
 * @ECO-layer: aep-engine-web
 * @ECO-semantic: src-App
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

import { useState } from 'react';
import { useAppState } from '@/hooks/useAppState';
import { HomeScreen } from '@/screens/HomeScreen';
import { AuditScreen } from '@/screens/AuditScreen';
import { ResultsScreen } from '@/screens/ResultsScreen';
import { ReportScreen } from '@/screens/ReportScreen';
import { SettingsScreen } from '@/screens/SettingsScreen';

export function App() {
  const {
    currentTab,
    setCurrentTab,
    selectedSeverity,
    setSelectedSeverity,
    isAuditRunning,
    setIsAuditRunning,
    darkMode,
    setDarkMode,
    auditSummary,
    recentEvents,
    problems,
    severityDistribution,
    problemTypes,
    recommendations,
    etlStages,
    files,
    logs,
  } = useAppState();

  const handleStartAudit = () => {
    setIsAuditRunning(true);
    setCurrentTab('audit');
  };

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="min-h-screen bg-white dark:bg-slate-950">
        {/* Main Content */}
        {currentTab === 'home' && (
          <HomeScreen
            auditSummary={auditSummary}
            recentEvents={recentEvents}
            onStartAudit={handleStartAudit}
          />
        )}
        {currentTab === 'audit' && (
          <AuditScreen
            etlStages={etlStages}
            files={files}
            logs={logs}
            isRunning={isAuditRunning}
          />
        )}
        {currentTab === 'results' && (
          <ResultsScreen
            problems={problems}
            severityDistribution={severityDistribution}
            selectedSeverity={selectedSeverity}
            onSeverityChange={setSelectedSeverity}
          />
        )}
        {currentTab === 'report' && (
          <ReportScreen
            auditSummary={auditSummary}
            problemTypes={problemTypes}
            recommendations={recommendations}
          />
        )}
        {currentTab === 'settings' && (
          <SettingsScreen
            darkMode={darkMode}
            onDarkModeChange={setDarkMode}
          />
        )}

        {/* Bottom Navigation */}
        <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-slate-800 border-t border-border dark:border-border-dark flex justify-around">
          {[
            { id: 'home', label: 'Home', icon: '🏠' },
            { id: 'audit', label: 'Audit', icon: '▶️' },
            { id: 'results', label: 'Results', icon: '🔍' },
            { id: 'report', label: 'Report', icon: '📄' },
            { id: 'settings', label: 'Settings', icon: '⚙️' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setCurrentTab(tab.id as any)}
              className={`flex-1 py-3 px-2 text-center text-xs font-medium transition-colors ${
                currentTab === tab.id
                  ? 'text-primary border-t-2 border-primary'
                  : 'text-muted dark:text-muted-dark hover:text-foreground dark:hover:text-foreground-dark'
              }`}
            >
              <div className="text-lg mb-1">{tab.icon}</div>
              <div>{tab.label}</div>
            </button>
          ))}
        </div>

        {/* Bottom Padding */}
        <div className="h-20" />
      </div>
    </div>
  );
}
