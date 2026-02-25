/**
 * @ECO-governed
 * @ECO-layer: aep-engine-app
 * @ECO-semantic: (tabs)-report
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

import { ScrollView, Text, View, TouchableOpacity } from "react-native";
import { ScreenContainer } from "@/components/screen-container";
import { StatisticCard } from "@/components/ui/statistic-card";

/**
 * Global Report Screen - 全局治理稽核報告
 *
 * 顯示報告摘要、統計圖表、修復建議和導出功能
 */
export default function ReportScreen() {
  const reportData = {
    totalDetections: 24,
    passedChecks: 16,
    failedChecks: 8,
    timestamp: "2026-01-26 14:35:22",
  };

  const severityDistribution = [
    { severity: "Critical", count: 1, percentage: 12.5 },
    { severity: "High", count: 2, percentage: 25 },
    { severity: "Medium", count: 3, percentage: 37.5 },
    { severity: "Low", count: 2, percentage: 25 },
  ];

  const problemTypes = [
    { type: "Schema Mismatch", count: 3 },
    { type: "Metadata Missing", count: 2 },
    { type: "Naming Inconsistency", count: 1 },
    { type: "Directory Structure", count: 1 },
    { type: "GL Marker Missing", count: 1 },
  ];

  const recommendations = [
    {
      id: "1",
      title: "Fix Schema Validation",
      description: "Update timestamp field to ISO 8601 format across all ETL scripts",
      impact: "High",
    },
    {
      id: "2",
      title: "Add Missing Metadata",
      description: "Add owner and created_at fields to all schema definitions",
      impact: "High",
    },
    {
      id: "3",
      title: "Standardize Naming",
      description: "Rename files to follow snake_case convention",
      impact: "Medium",
    },
    {
      id: "4",
      title: "Reorganize Directory",
      description: "Migrate to recommended directory structure with etl/, es/, schemas/ folders",
      impact: "Medium",
    },
  ];

  return (
    <ScreenContainer className="p-0">
      <ScrollView className="flex-1">
        {/* Header */}
        <View className="bg-primary px-6 pt-6 pb-8">
          <Text className="text-3xl font-bold text-white mb-2">Global Report</Text>
          <Text className="text-sm text-white opacity-80">{reportData.timestamp}</Text>
        </View>

        {/* Content */}
        <View className="flex-1 px-6 py-6 gap-6">
          {/* Summary Statistics */}
          <View className="gap-3">
            <Text className="text-lg font-semibold text-foreground">Summary</Text>
            <StatisticCard
              label="Total Detections"
              value={reportData.totalDetections}
              icon="📊"
              variant="default"
            />
            <StatisticCard
              label="Passed Checks"
              value={reportData.passedChecks}
              icon="✓"
              variant="success"
            />
            <StatisticCard
              label="Failed Checks"
              value={reportData.failedChecks}
              icon="✗"
              variant="error"
            />
          </View>

          {/* Severity Distribution */}
          <View className="gap-3">
            <Text className="text-lg font-semibold text-foreground">Severity Distribution</Text>
            <View className="bg-surface rounded-xl p-4 border border-border gap-3">
              {severityDistribution.map((item, index) => (
                <View key={index} className="gap-1">
                  <View className="flex-row justify-between items-center">
                    <Text className="text-sm font-medium text-foreground">{item.severity}</Text>
                    <Text className="text-sm font-semibold text-foreground">{item.count}</Text>
                  </View>
                  <View className="h-2 bg-muted bg-opacity-20 rounded-full overflow-hidden">
                    <View
                      className={`h-full rounded-full ${
                        item.severity === "Critical"
                          ? "bg-red-600"
                          : item.severity === "High"
                            ? "bg-orange-600"
                            : item.severity === "Medium"
                              ? "bg-yellow-600"
                              : "bg-blue-600"
                      }`}
                      style={{ width: `${item.percentage}%` }}
                    />
                  </View>
                </View>
              ))}
            </View>
          </View>

          {/* Problem Types */}
          <View className="gap-3">
            <Text className="text-lg font-semibold text-foreground">Problem Types</Text>
            <View className="bg-surface rounded-xl p-4 border border-border gap-2">
              {problemTypes.map((item, index) => (
                <View key={index} className="flex-row justify-between items-center py-2 border-b border-border last:border-b-0">
                  <Text className="text-sm text-foreground">{item.type}</Text>
                  <View className="bg-primary bg-opacity-10 px-2 py-1 rounded">
                    <Text className="text-sm font-semibold text-primary">{item.count}</Text>
                  </View>
                </View>
              ))}
            </View>
          </View>

          {/* Recommendations */}
          <View className="gap-3">
            <Text className="text-lg font-semibold text-foreground">Recommendations</Text>
            <View className="gap-2">
              {recommendations.map((rec) => (
                <TouchableOpacity
                  key={rec.id}
                  className="bg-surface rounded-lg p-4 border border-border active:opacity-70"
                >
                  <View className="flex-row justify-between items-start mb-2">
                    <Text className="text-sm font-semibold text-foreground flex-1">{rec.title}</Text>
                    <View
                      className={`px-2 py-1 rounded ${
                        rec.impact === "High"
                          ? "bg-error bg-opacity-20"
                          : "bg-warning bg-opacity-20"
                      }`}
                    >
                      <Text
                        className={`text-xs font-medium ${
                          rec.impact === "High" ? "text-error" : "text-warning"
                        }`}
                      >
                        {rec.impact}
                      </Text>
                    </View>
                  </View>
                  <Text className="text-sm text-muted">{rec.description}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Action Buttons */}
          <View className="gap-3 pb-6">
            <TouchableOpacity className="bg-primary rounded-xl p-4 active:opacity-80">
              <Text className="text-white font-semibold text-center">Export Report</Text>
            </TouchableOpacity>
            <TouchableOpacity className="bg-surface rounded-xl p-4 border border-border active:opacity-70">
              <Text className="text-foreground font-semibold text-center">Share Report</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}
