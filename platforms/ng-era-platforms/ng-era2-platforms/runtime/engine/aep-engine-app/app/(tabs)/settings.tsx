/**
 * @ECO-governed
 * @ECO-layer: aep-engine-app
 * @ECO-semantic: (tabs)-settings
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

import { ScrollView, Text, View, TouchableOpacity, TextInput, Switch } from "react-native";
import { useState } from "react";
import { ScreenContainer } from "@/components/screen-container";

/**
 * Settings Screen - 應用設定
 *
 * 管理連接設定、治理規則和通知偏好
 */
export default function SettingsScreen() {
  const [esHost, setEsHost] = useState("localhost");
  const [esPort, setEsPort] = useState("9200");
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  return (
    <ScreenContainer className="p-0">
      <ScrollView className="flex-1">
        {/* Header */}
        <View className="bg-primary px-6 pt-6 pb-8">
          <Text className="text-3xl font-bold text-white mb-2">Settings</Text>
          <Text className="text-sm text-white opacity-80">Configure your application</Text>
        </View>

        {/* Content */}
        <View className="flex-1 px-6 py-6 gap-6">
          {/* Connection Settings */}
          <View className="gap-3">
            <Text className="text-lg font-semibold text-foreground">Connection Settings</Text>
            <View className="bg-surface rounded-xl p-4 border border-border gap-4">
              <View className="gap-2">
                <Text className="text-sm font-medium text-foreground">Elasticsearch Host</Text>
                <TextInput
                  value={esHost}
                  onChangeText={setEsHost}
                  placeholder="localhost"
                  className="bg-background border border-border rounded-lg px-3 py-2 text-foreground text-sm"
                  placeholderTextColor="#9BA1A6"
                />
              </View>
              <View className="gap-2">
                <Text className="text-sm font-medium text-foreground">Elasticsearch Port</Text>
                <TextInput
                  value={esPort}
                  onChangeText={setEsPort}
                  placeholder="9200"
                  keyboardType="number-pad"
                  className="bg-background border border-border rounded-lg px-3 py-2 text-foreground text-sm"
                  placeholderTextColor="#9BA1A6"
                />
              </View>
            </View>
          </View>

          {/* Governance Rules */}
          <View className="gap-3">
            <Text className="text-lg font-semibold text-foreground">Governance Rules</Text>
            <View className="bg-surface rounded-xl p-4 border border-border gap-3">
              {[
                { label: "Enforce Schema Validation", enabled: true },
                { label: "Require Metadata", enabled: true },
                { label: "Check Naming Convention", enabled: true },
                { label: "Validate GL Markers", enabled: false },
              ].map((rule, index) => (
                <View
                  key={index}
                  className="flex-row justify-between items-center py-2 border-b border-border last:border-b-0"
                >
                  <Text className="text-sm text-foreground">{rule.label}</Text>
                  <Switch value={rule.enabled} />
                </View>
              ))}
            </View>
          </View>

          {/* Notification Settings */}
          <View className="gap-3">
            <Text className="text-lg font-semibold text-foreground">Notifications</Text>
            <View className="bg-surface rounded-xl p-4 border border-border gap-3">
              <View className="flex-row justify-between items-center">
                <Text className="text-sm text-foreground">Enable Notifications</Text>
                <Switch
                  value={notificationsEnabled}
                  onValueChange={setNotificationsEnabled}
                />
              </View>
              {notificationsEnabled && (
                <>
                  <View className="border-t border-border pt-3">
                    <View className="flex-row justify-between items-center py-2">
                      <Text className="text-sm text-foreground">Audit Completion</Text>
                      <Switch value={true} />
                    </View>
                    <View className="flex-row justify-between items-center py-2">
                      <Text className="text-sm text-foreground">Critical Issues</Text>
                      <Switch value={true} />
                    </View>
                    <View className="flex-row justify-between items-center py-2">
                      <Text className="text-sm text-foreground">Daily Summary</Text>
                      <Switch value={false} />
                    </View>
                  </View>
                </>
              )}
            </View>
          </View>

          {/* About */}
          <View className="gap-3">
            <Text className="text-lg font-semibold text-foreground">About</Text>
            <View className="bg-surface rounded-xl p-4 border border-border gap-3">
              <View className="flex-row justify-between items-center py-2 border-b border-border">
                <Text className="text-sm text-muted">App Version</Text>
                <Text className="text-sm font-medium text-foreground">1.0.0</Text>
              </View>
              <View className="flex-row justify-between items-center py-2 border-b border-border">
                <Text className="text-sm text-muted">Build Number</Text>
                <Text className="text-sm font-medium text-foreground">20260126</Text>
              </View>
              <View className="flex-row justify-between items-center py-2">
                <Text className="text-sm text-muted">Last Updated</Text>
                <Text className="text-sm font-medium text-foreground">2026-01-26</Text>
              </View>
            </View>
          </View>

          {/* Action Buttons */}
          <View className="gap-3 pb-6">
            <TouchableOpacity className="bg-primary rounded-xl p-4 active:opacity-80">
              <Text className="text-white font-semibold text-center">Save Settings</Text>
            </TouchableOpacity>
            <TouchableOpacity className="bg-surface rounded-xl p-4 border border-border active:opacity-70">
              <Text className="text-foreground font-semibold text-center">Reset to Defaults</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}
