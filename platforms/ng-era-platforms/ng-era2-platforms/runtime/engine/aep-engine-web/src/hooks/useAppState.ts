/**
 * @ECO-governed
 * @ECO-layer: aep-engine-web
 * @ECO-semantic: hooks-useAppState
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

import { useState } from 'react';
import {
  mockAuditSummary,
  mockRecentEvents,
  mockProblems,
  mockSeverityDistribution,
  mockProblemTypes,
  mockRecommendations,
  mockETLStages,
  mockFiles,
  mockLogs,
} from '@/data/mock';

export function useAppState() {
  const [currentTab, setCurrentTab] = useState<'home' | 'audit' | 'results' | 'report' | 'settings'>('home');
  const [selectedSeverity, setSelectedSeverity] = useState<string | null>(null);
  const [isAuditRunning, setIsAuditRunning] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  const auditSummary = mockAuditSummary;
  const recentEvents = mockRecentEvents;
  const problems = selectedSeverity
    ? mockProblems.filter((p) => p.severity === selectedSeverity)
    : mockProblems;
  const severityDistribution = mockSeverityDistribution;
  const problemTypes = mockProblemTypes;
  const recommendations = mockRecommendations;
  const etlStages = mockETLStages;
  const files = mockFiles;
  const logs = mockLogs;

  return {
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
  };
}
