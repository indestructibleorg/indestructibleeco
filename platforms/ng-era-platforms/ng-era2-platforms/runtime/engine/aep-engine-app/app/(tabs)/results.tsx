/**
 * @ECO-governed
 * @ECO-layer: aep-engine-app
 * @ECO-semantic: (tabs)-results
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

import { ScrollView, Text, View, TouchableOpacity } from "react-native";
import { useState } from "react";
import { ScreenContainer } from "@/components/screen-container";
import { ProblemCard } from "@/components/ui/problem-card";

/**
 * Detection Results Screen - 檢測結果與分析
 *
 * 顯示按嚴重度分類的問題、詳細資訊和修復建議
 */
export default function ResultsScreen() {
  const [selectedSeverity, setSelectedSeverity] = useState<string | null>(null);

  const problems = [
    {
      id: "1",
      type: "Schema Mismatch",
      severity: "critical" as const,
      description: "Field 'timestamp' type mismatch: expected datetime, got string",
      location: "etl_pipeline.py:45",
      suggestion: "Convert timestamp field to ISO 8601 format",
    },
    {
      id: "2",
      type: "Metadata Missing",
      severity: "high" as const,
      description: "Missing required metadata: owner, created_at",
      location: "schema_validator.py:12",
      suggestion: "Add missing metadata fields to schema definition",
    },
    {
      id: "3",
      type: "Naming Inconsistency",
      severity: "medium" as const,
      description: "File naming does not follow snake_case convention",
      location: "naming_validator.py:8",
      suggestion: "Rename file to follow naming convention",
    },
    {
      id: "4",
      type: "Directory Structure",
      severity: "medium" as const,
      description: "Directory structure does not match best practices",
      location: "./workspace",
      suggestion: "Reorganize directory structure according to template",
    },
    {
      id: "5",
      type: "GL Marker Missing",
      severity: "low" as const,
      description: "Missing GL Root Semantic Anchor tag",
      location: "metadata_checker.py:20",
      suggestion: "Add GL layer marker to file header",
    },
  ];

  const severityStats = {
    critical: problems.filter((p) => p.severity === "critical").length,
    high: problems.filter((p) => p.severity === "high").length,
    medium: problems.filter((p) => p.severity === "medium").length,
    low: problems.filter((p) => p.severity === "low").length,
  };

  const filteredProblems = selectedSeverity
    ? problems.filter((p) => p.severity === selectedSeverity)
    : problems;

  return (
    <ScreenContainer className="p-0">
      <ScrollView className="flex-1">
        {/* Header */}
        <View className="bg-primary px-6 pt-6 pb-8">
          <Text className="text-3xl font-bold text-white mb-2">Detection Results</Text>
          <Text className="text-sm text-white opacity-80">
            {filteredProblems.length} issue{filteredProblems.length !== 1 ? "s" : ""} found
          </Text>
        </View>

        {/* Content */}
        <View className="flex-1 px-6 py-6 gap-6">
          {/* Severity Filter */}
          <View className="gap-3">
            <Text className="text-lg font-semibold text-foreground">Filter by Severity</Text>
            <View className="flex-row gap-2 flex-wrap">
              {[
                { label: "Critical", value: "critical", color: "bg-red-600" },
                { label: "High", value: "high", color: "bg-orange-600" },
                { label: "Medium", value: "medium", color: "bg-yellow-600" },
                { label: "Low", value: "low", color: "bg-blue-600" },
              ].map((severity) => (
                <TouchableOpacity
                  key={severity.value}
                  onPress={() =>
                    setSelectedSeverity(
                      selectedSeverity === severity.value ? null : severity.value
                    )
                  }
                  className={`px-3 py-2 rounded-lg border ${
                    selectedSeverity === severity.value
                      ? `${severity.color} border-transparent`
                      : "border-border bg-surface"
                  }`}
                >
                  <Text
                    className={`text-xs font-medium ${
                      selectedSeverity === severity.value
                        ? "text-white"
                        : "text-foreground"
                    }`}
                  >
                    {severity.label} ({severityStats[severity.value as keyof typeof severityStats]})
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Problems List */}
          <View className="gap-3">
            <Text className="text-lg font-semibold text-foreground">Issues</Text>
            <View className="gap-2">
              {filteredProblems.map((problem) => (
                <TouchableOpacity
                  key={problem.id}
                  className="active:opacity-70"
                >
                  <ProblemCard
                    type={problem.type}
                    severity={problem.severity}
                    description={problem.description}
                    location={problem.location}
                  />
                  <View className="bg-surface rounded-b-lg p-3 border border-t-0 border-border">
                    <Text className="text-xs text-muted mb-2">Suggestion:</Text>
                    <Text className="text-sm text-foreground">{problem.suggestion}</Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Export Button */}
          <View className="gap-3 pb-6">
            <TouchableOpacity className="bg-primary rounded-xl p-4 active:opacity-80">
              <Text className="text-white font-semibold text-center">Export Report</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}
