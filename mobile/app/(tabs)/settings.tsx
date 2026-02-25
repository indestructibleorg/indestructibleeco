import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Switch,
  StyleSheet,
  Alert,
} from "react-native";
import { ScreenContainer } from "@/components/screen-container";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { useColors } from "@/hooks/use-colors";
import { useColorScheme } from "@/hooks/use-color-scheme";

// ─── Component ───────────────────────────────────────────────────────────────

export default function SettingsScreen() {
  const colors = useColors();
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";

  const [apiGateway, setApiGateway] = useState("https://api.autoecoops.io");
  const [authToken, setAuthToken] = useState("••••••••••••••••");
  const [defaultEngine, setDefaultEngine] = useState("vllm");
  const [streamingEnabled, setStreamingEnabled] = useState(true);
  const [traceEnabled, setTraceEnabled] = useState(true);
  const [auditEnabled, setAuditEnabled] = useState(true);
  const [editingToken, setEditingToken] = useState(false);

  const ENGINES = ["vllm", "tgi", "sglang", "tensorrt", "deepspeed", "lmdeploy", "ollama"];

  const handleSave = () => {
    Alert.alert("Settings Saved", "Configuration updated successfully.", [{ text: "OK" }]);
  };

  const handleClearCache = () => {
    Alert.alert("Clear Cache", "This will clear all cached data. Continue?", [
      { text: "Cancel", style: "cancel" },
      { text: "Clear", style: "destructive", onPress: () => {} },
    ]);
  };

  return (
    <ScreenContainer containerClassName="bg-background">
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: colors.border, backgroundColor: colors.background }]}>
        <Text style={[styles.headerTitle, { color: colors.foreground }]}>Settings</Text>
        <TouchableOpacity
          style={[styles.saveBtn, { backgroundColor: colors.primary }]}
          onPress={handleSave}
        >
          <Text style={styles.saveBtnText}>Save</Text>
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* API Configuration */}
        <Text style={[styles.sectionTitle, { color: colors.muted }]}>API CONFIGURATION</Text>
        <View style={[styles.group, { backgroundColor: colors.surface, borderColor: colors.border }]}>
          <View style={styles.settingRow}>
            <Text style={[styles.settingLabel, { color: colors.foreground }]}>API Gateway URL</Text>
            <TextInput
              style={[styles.settingInput, { color: colors.foreground, borderColor: colors.border, backgroundColor: colors.background }]}
              value={apiGateway}
              onChangeText={setApiGateway}
              placeholder="https://api.autoecoops.io"
              placeholderTextColor={colors.muted}
              autoCapitalize="none"
              keyboardType="url"
            />
          </View>
          <View style={[styles.divider, { backgroundColor: colors.border }]} />
          <View style={styles.settingRow}>
            <Text style={[styles.settingLabel, { color: colors.foreground }]}>Auth Token (JWT)</Text>
            <View style={styles.tokenRow}>
              <TextInput
                style={[styles.settingInput, { flex: 1, color: colors.foreground, borderColor: colors.border, backgroundColor: colors.background }]}
                value={editingToken ? authToken : "••••••••••••••••"}
                onChangeText={setAuthToken}
                placeholder="Bearer token"
                placeholderTextColor={colors.muted}
                secureTextEntry={!editingToken}
                autoCapitalize="none"
              />
              <TouchableOpacity onPress={() => setEditingToken(!editingToken)} style={styles.tokenToggle}>
                <IconSymbol name="eye" size={16} color={colors.muted} />
              </TouchableOpacity>
            </View>
          </View>
        </View>

        {/* Inference Engine */}
        <Text style={[styles.sectionTitle, { color: colors.muted }]}>INFERENCE ENGINE</Text>
        <View style={[styles.group, { backgroundColor: colors.surface, borderColor: colors.border }]}>
          <Text style={[styles.groupLabel, { color: colors.muted }]}>Default Engine</Text>
          <View style={styles.engineGrid}>
            {ENGINES.map((engine) => (
              <TouchableOpacity
                key={engine}
                style={[
                  styles.engineChip,
                  { borderColor: defaultEngine === engine ? colors.primary : colors.border },
                  defaultEngine === engine && { backgroundColor: colors.primary + "22" },
                ]}
                onPress={() => setDefaultEngine(engine)}
              >
                <Text style={[styles.engineChipText, { color: defaultEngine === engine ? colors.primary : colors.muted }]}>
                  {engine}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          <View style={[styles.divider, { backgroundColor: colors.border }]} />
          <View style={styles.toggleRow}>
            <View>
              <Text style={[styles.settingLabel, { color: colors.foreground }]}>Streaming Response</Text>
              <Text style={[styles.settingDesc, { color: colors.muted }]}>Enable token-by-token streaming</Text>
            </View>
            <Switch
              value={streamingEnabled}
              onValueChange={setStreamingEnabled}
              trackColor={{ false: colors.border, true: colors.primary + "88" }}
              thumbColor={streamingEnabled ? colors.primary : colors.muted}
            />
          </View>
        </View>

        {/* Observability */}
        <Text style={[styles.sectionTitle, { color: colors.muted }]}>OBSERVABILITY</Text>
        <View style={[styles.group, { backgroundColor: colors.surface, borderColor: colors.border }]}>
          <View style={styles.toggleRow}>
            <View>
              <Text style={[styles.settingLabel, { color: colors.foreground }]}>Distributed Tracing</Text>
              <Text style={[styles.settingDesc, { color: colors.muted }]}>100% sampling on critical paths</Text>
            </View>
            <Switch
              value={traceEnabled}
              onValueChange={setTraceEnabled}
              trackColor={{ false: colors.border, true: colors.primary + "88" }}
              thumbColor={traceEnabled ? colors.primary : colors.muted}
            />
          </View>
          <View style={[styles.divider, { backgroundColor: colors.border }]} />
          <View style={styles.toggleRow}>
            <View>
              <Text style={[styles.settingLabel, { color: colors.foreground }]}>Audit Logging</Text>
              <Text style={[styles.settingDesc, { color: colors.muted }]}>Immutable audit trail (SOC2/ISO27001)</Text>
            </View>
            <Switch
              value={auditEnabled}
              onValueChange={setAuditEnabled}
              trackColor={{ false: colors.border, true: colors.primary + "88" }}
              thumbColor={auditEnabled ? colors.primary : colors.muted}
            />
          </View>
        </View>

        {/* Danger Zone */}
        <Text style={[styles.sectionTitle, { color: colors.muted }]}>DATA</Text>
        <View style={[styles.group, { backgroundColor: colors.surface, borderColor: colors.border }]}>
          <TouchableOpacity style={styles.dangerRow} onPress={handleClearCache}>
            <IconSymbol name="trash" size={16} color={colors.error} />
            <Text style={[styles.dangerText, { color: colors.error }]}>Clear Cache</Text>
          </TouchableOpacity>
        </View>

        {/* About */}
        <Text style={[styles.sectionTitle, { color: colors.muted }]}>ABOUT</Text>
        <View style={[styles.group, { backgroundColor: colors.surface, borderColor: colors.border }]}>
          <View style={styles.aboutRow}>
            <Text style={[styles.aboutKey, { color: colors.muted }]}>App Version</Text>
            <Text style={[styles.aboutValue, { color: colors.foreground }]}>1.0.0</Text>
          </View>
          <View style={[styles.divider, { backgroundColor: colors.border }]} />
          <View style={styles.aboutRow}>
            <Text style={[styles.aboutKey, { color: colors.muted }]}>Platform</Text>
            <Text style={[styles.aboutValue, { color: colors.foreground }]}>KUBE-1.0 ULTRA</Text>
          </View>
          <View style={[styles.divider, { backgroundColor: colors.border }]} />
          <View style={styles.aboutRow}>
            <Text style={[styles.aboutKey, { color: colors.muted }]}>Cluster</Text>
            <Text style={[styles.aboutValue, { color: colors.foreground }]}>GKE asia-east1</Text>
          </View>
          <View style={[styles.divider, { backgroundColor: colors.border }]} />
          <View style={styles.aboutRow}>
            <Text style={[styles.aboutKey, { color: colors.muted }]}>Repository</Text>
            <Text style={[styles.aboutValue, { color: colors.primary }]}>indestructibleorg/eco-base</Text>
          </View>
          <View style={[styles.divider, { backgroundColor: colors.border }]} />
          <View style={styles.aboutRow}>
            <Text style={[styles.aboutKey, { color: colors.muted }]}>SLO Target</Text>
            <Text style={[styles.aboutValue, { color: colors.foreground }]}>99.99% · P95 ≤200ms</Text>
          </View>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 0.5,
  },
  headerTitle: { fontSize: 18, fontWeight: "700" },
  saveBtn: { paddingHorizontal: 16, paddingVertical: 7, borderRadius: 20 },
  saveBtnText: { color: "#fff", fontSize: 14, fontWeight: "600" },
  scrollContent: { padding: 16 },
  sectionTitle: { fontSize: 11, fontWeight: "700", letterSpacing: 1, marginTop: 16, marginBottom: 8 },
  group: { borderRadius: 14, borderWidth: 1, overflow: "hidden", marginBottom: 4 },
  groupLabel: { fontSize: 12, fontWeight: "600", paddingHorizontal: 14, paddingTop: 12, paddingBottom: 8 },
  divider: { height: 0.5, marginHorizontal: 14 },
  settingRow: { paddingHorizontal: 14, paddingVertical: 12, gap: 6 },
  settingLabel: { fontSize: 14, fontWeight: "600" },
  settingDesc: { fontSize: 11, marginTop: 1 },
  settingInput: {
    borderRadius: 8,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 7,
    fontSize: 13,
  },
  tokenRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  tokenToggle: { padding: 4 },
  engineGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    paddingHorizontal: 14,
    paddingBottom: 12,
  },
  engineChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
  },
  engineChipText: { fontSize: 12, fontWeight: "600" },
  toggleRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  dangerRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingHorizontal: 14,
    paddingVertical: 14,
  },
  dangerText: { fontSize: 14, fontWeight: "600" },
  aboutRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 14,
    paddingVertical: 11,
  },
  aboutKey: { fontSize: 13 },
  aboutValue: { fontSize: 13, fontWeight: "600" },
});
