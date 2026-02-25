/**
 * @ECO-governed
 * @ECO-layer: aep-engine-app
 * @ECO-semantic: (tabs)-audit
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

import { ScrollView, Text, View, TouchableOpacity, FlatList } from "react-native";
import { useState } from "react";
import { ScreenContainer } from "@/components/screen-container";

/**
 * Audit Execution Screen - 稽核執行與監控
 *
 * 顯示 ETL Pipeline 進度、逐文件執行狀態、沙箱資訊和即時日誌
 */
export default function AuditScreen() {
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);

  const etlStages = [
    { name: "Extract", progress: 100, status: "completed" },
    { name: "Transform", progress: 65, status: "running" },
    { name: "Load", progress: 0, status: "pending" },
  ];

  const files = [
    { id: "1", name: "etl_pipeline.py", status: "completed", time: "2.3s" },
    { id: "2", name: "schema_validator.py", status: "running", time: "1.2s" },
    { id: "3", name: "metadata_checker.py", status: "pending", time: "-" },
    { id: "4", name: "naming_validator.py", status: "pending", time: "-" },
  ];

  const logs = [
    "[INFO] Starting ETL Pipeline execution",
    "[INFO] Initializing sandbox: sandbox-2026-01-26-001",
    "[INFO] Extracting data from source...",
    "[SUCCESS] Data extraction completed (1,234 records)",
    "[INFO] Starting transformation phase...",
    "[INFO] Applying schema validation...",
    "[WARNING] Found 2 schema mismatches in field 'timestamp'",
  ];

  return (
    <ScreenContainer className="p-0">
      <ScrollView className="flex-1">
        {/* Header */}
        <View className="bg-primary px-6 pt-6 pb-8">
          <Text className="text-3xl font-bold text-white mb-2">Audit Execution</Text>
          <Text className="text-sm text-white opacity-80">
            {isRunning ? "Running..." : "Ready to start"}
          </Text>
        </View>

        {/* Content */}
        <View className="flex-1 px-6 py-6 gap-6">
          {/* ETL Pipeline Progress */}
          <View className="gap-3">
            <Text className="text-lg font-semibold text-foreground">ETL Pipeline</Text>
            {etlStages.map((stage, index) => (
              <View key={index} className="gap-1">
                <View className="flex-row justify-between items-center">
                  <Text className="text-sm font-medium text-foreground">{stage.name}</Text>
                  <Text className="text-xs text-muted">{stage.progress}%</Text>
                </View>
                <View className="h-2 bg-surface rounded-full overflow-hidden border border-border">
                  <View
                    className={`h-full rounded-full ${
                      stage.status === "completed"
                        ? "bg-success"
                        : stage.status === "running"
                          ? "bg-primary"
                          : "bg-muted"
                    }`}
                    style={{ width: `${stage.progress}%` }}
                  />
                </View>
              </View>
            ))}
          </View>

          {/* Sandbox Info */}
          <View className="bg-surface rounded-xl p-4 border border-border gap-2">
            <Text className="text-sm font-semibold text-foreground mb-2">Sandbox Info</Text>
            <View className="flex-row justify-between">
              <Text className="text-xs text-muted">ID</Text>
              <Text className="text-xs text-foreground font-mono">sandbox-2026-01-26-001</Text>
            </View>
            <View className="flex-row justify-between">
              <Text className="text-xs text-muted">CPU</Text>
              <Text className="text-xs text-foreground">45%</Text>
            </View>
            <View className="flex-row justify-between">
              <Text className="text-xs text-muted">Memory</Text>
              <Text className="text-xs text-foreground">256 MB / 512 MB</Text>
            </View>
            <View className="flex-row justify-between">
              <Text className="text-xs text-muted">Disk</Text>
              <Text className="text-xs text-foreground">1.2 GB / 2 GB</Text>
            </View>
          </View>

          {/* File Execution Status */}
          <View className="gap-3">
            <Text className="text-lg font-semibold text-foreground">File Execution</Text>
            <View className="gap-2">
              {files.map((file) => (
                <TouchableOpacity
                  key={file.id}
                  className="bg-surface rounded-lg p-3 border border-border flex-row items-center justify-between active:opacity-70"
                >
                  <View className="flex-1">
                    <Text className="text-sm font-medium text-foreground">{file.name}</Text>
                    <Text className="text-xs text-muted mt-1">{file.time}</Text>
                  </View>
                  <View
                    className={`px-2 py-1 rounded ${
                      file.status === "completed"
                        ? "bg-success bg-opacity-20"
                        : file.status === "running"
                          ? "bg-primary bg-opacity-20"
                          : "bg-muted bg-opacity-20"
                    }`}
                  >
                    <Text
                      className={`text-xs font-medium ${
                        file.status === "completed"
                          ? "text-success"
                          : file.status === "running"
                            ? "text-primary"
                            : "text-muted"
                      }`}
                    >
                      {file.status.charAt(0).toUpperCase() + file.status.slice(1)}
                    </Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Logs */}
          <View className="gap-3">
            <Text className="text-lg font-semibold text-foreground">Logs</Text>
            <View className="bg-surface rounded-lg p-3 border border-border max-h-40">
              <FlatList
                data={logs}
                keyExtractor={(_, index) => index.toString()}
                scrollEnabled={false}
                renderItem={({ item }) => (
                  <Text className="text-xs text-muted font-mono mb-1">{item}</Text>
                )}
              />
            </View>
          </View>

          {/* Action Buttons */}
          <View className="gap-3 pb-6">
            {!isRunning ? (
              <TouchableOpacity
                onPress={() => setIsRunning(true)}
                className="bg-primary rounded-xl p-4 active:opacity-80"
              >
                <Text className="text-white font-semibold text-center">Start Execution</Text>
              </TouchableOpacity>
            ) : (
              <TouchableOpacity
                onPress={() => setIsRunning(false)}
                className="bg-error rounded-xl p-4 active:opacity-80"
              >
                <Text className="text-white font-semibold text-center">Stop Execution</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}
