/**
 * @ECO-governed
 * @ECO-layer: aep-engine-app
 * @ECO-semantic: (tabs)-index
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

import { ScrollView, Text, View, TouchableOpacity, RefreshControl } from "react-native";
import { useState } from "react";
import { ScreenContainer } from "@/components/screen-container";

/**
 * Home Screen - AEP Engine Governance & Audit App
 *
 * Displays governance audit summary with statistics, recent events, and quick actions.
 */
export default function HomeScreen() {
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = async () => {
    setRefreshing(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setRefreshing(false);
  };

  return (
    <ScreenContainer className="p-0">
      <ScrollView
        contentContainerStyle={{ flexGrow: 1 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {/* Header Section */}
        <View className="bg-primary px-6 pt-6 pb-8">
          <Text className="text-3xl font-bold text-white mb-2">AEP Engine</Text>
          <Text className="text-sm text-white opacity-80">Governance & Audit</Text>
        </View>

        {/* Content Section */}
        <View className="flex-1 px-6 py-6 gap-6">
          {/* Statistics Cards */}
          <View className="gap-3">
            <Text className="text-lg font-semibold text-foreground">Latest Audit Summary</Text>
            <View className="gap-3">
              {/* Total Detections Card */}
              <View className="bg-surface rounded-xl p-4 border border-border flex-row justify-between items-center">
                <View>
                  <Text className="text-sm text-muted mb-1">Total Detections</Text>
                  <Text className="text-3xl font-bold text-foreground">24</Text>
                </View>
                <View className="bg-primary bg-opacity-10 rounded-lg p-3">
                  <Text className="text-2xl">📊</Text>
                </View>
              </View>

              {/* Issues Found Card */}
              <View className="bg-surface rounded-xl p-4 border border-border flex-row justify-between items-center">
                <View>
                  <Text className="text-sm text-muted mb-1">Issues Found</Text>
                  <Text className="text-3xl font-bold text-error">8</Text>
                </View>
                <View className="bg-error bg-opacity-10 rounded-lg p-3">
                  <Text className="text-2xl">⚠️</Text>
                </View>
              </View>

              {/* Pass Rate Card */}
              <View className="bg-surface rounded-xl p-4 border border-border flex-row justify-between items-center">
                <View>
                  <Text className="text-sm text-muted mb-1">Pass Rate</Text>
                  <Text className="text-3xl font-bold text-success">67%</Text>
                </View>
                <View className="bg-success bg-opacity-10 rounded-lg p-3">
                  <Text className="text-2xl">✓</Text>
                </View>
              </View>
            </View>
          </View>

          {/* Recent Events */}
          <View className="gap-3">
            <Text className="text-lg font-semibold text-foreground">Recent Events</Text>
            <View className="gap-2">
              {[
                { type: "Execution", time: "2 min ago", status: "success" },
                { type: "Detection", time: "5 min ago", status: "warning" },
                { type: "Rollback", time: "10 min ago", status: "info" },
              ].map((event, index) => (
                <TouchableOpacity
                  key={index}
                  className="bg-surface rounded-lg p-4 border border-border flex-row items-center gap-3 active:opacity-70"
                >
                  <View
                    className={`w-2 h-2 rounded-full ${
                      event.status === "success"
                        ? "bg-success"
                        : event.status === "warning"
                          ? "bg-warning"
                          : "bg-primary"
                    }`}
                  />
                  <View className="flex-1">
                    <Text className="text-sm font-medium text-foreground">{event.type}</Text>
                    <Text className="text-xs text-muted">{event.time}</Text>
                  </View>
                  <Text className="text-lg">→</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Quick Actions */}
          <View className="gap-3">
            <Text className="text-lg font-semibold text-foreground">Quick Actions</Text>
            <TouchableOpacity className="bg-primary rounded-xl p-4 active:opacity-80">
              <Text className="text-white font-semibold text-center">Start New Audit</Text>
            </TouchableOpacity>
            <View className="flex-row gap-3">
              <TouchableOpacity className="flex-1 bg-surface rounded-xl p-4 border border-border active:opacity-70">
                <Text className="text-foreground font-medium text-center">View Report</Text>
              </TouchableOpacity>
              <TouchableOpacity className="flex-1 bg-surface rounded-xl p-4 border border-border active:opacity-70">
                <Text className="text-foreground font-medium text-center">Settings</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}
