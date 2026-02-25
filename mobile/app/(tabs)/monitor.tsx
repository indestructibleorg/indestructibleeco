import { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
} from "react-native";
import { ScreenContainer } from "@/components/screen-container";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { useColors } from "@/hooks/use-colors";

// ─── Types ───────────────────────────────────────────────────────────────────

type AlertSeverity = "critical" | "warning" | "info";

type Alert = {
  id: string;
  name: string;
  severity: AlertSeverity;
  message: string;
  time: string;
  platform: string;
};

type EngineMetric = {
  id: string;
  name: string;
  status: "healthy" | "degraded" | "down";
  rps: number;
  p95ms: number;
  errorRate: number;
};

// ─── Data ────────────────────────────────────────────────────────────────────

const ALERTS: Alert[] = [
  {
    id: "a1",
    name: "PolicyAuditLatencyHigh",
    severity: "warning",
    message: "P95 latency 312ms > 200ms SLO threshold",
    time: "3m ago",
    platform: "Platform-02",
  },
  {
    id: "a2",
    name: "PodCrashLoopBackOff",
    severity: "critical",
    message: "eco-api-service pod restarted 5 times in 10m",
    time: "8m ago",
    platform: "Platform-01",
  },
  {
    id: "a3",
    name: "TensorRTEngineDown",
    severity: "critical",
    message: "TensorRT-LLM engine not responding on port 1103",
    time: "15m ago",
    platform: "Platform-01",
  },
  {
    id: "a4",
    name: "SBOMSignatureExpired",
    severity: "info",
    message: "SBOM signature for eco-api:v1.2.3 expires in 7 days",
    time: "1h ago",
    platform: "Platform-02",
  },
];

const ENGINE_METRICS: EngineMetric[] = [
  { id: "vllm",      name: "vLLM",         status: "healthy",  rps: 42,  p95ms: 145, errorRate: 0.02 },
  { id: "tgi",       name: "TGI",          status: "healthy",  rps: 31,  p95ms: 178, errorRate: 0.05 },
  { id: "sglang",    name: "SGLang",       status: "healthy",  rps: 28,  p95ms: 162, errorRate: 0.03 },
  { id: "tensorrt",  name: "TensorRT-LLM", status: "down",     rps: 0,   p95ms: 0,   errorRate: 100  },
  { id: "deepspeed", name: "DeepSpeed",    status: "degraded", rps: 5,   p95ms: 890, errorRate: 12.4 },
  { id: "lmdeploy",  name: "LMDeploy",     status: "healthy",  rps: 19,  p95ms: 201, errorRate: 0.08 },
  { id: "ollama",    name: "Ollama",       status: "healthy",  rps: 8,   p95ms: 320, errorRate: 0.10 },
];

const STATUS_COLOR = {
  healthy:  "#10B981",
  degraded: "#F59E0B",
  down:     "#EF4444",
};

const ALERT_COLOR: Record<AlertSeverity, string> = {
  critical: "#EF4444",
  warning:  "#F59E0B",
  info:     "#60A5FA",
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function MonitorScreen() {
  const colors = useColors();
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = () => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 1500);
  };

  // Aggregate SLO metrics
  const healthyEngines = ENGINE_METRICS.filter((e) => e.status === "healthy").length;
  const avgP95 = ENGINE_METRICS.filter((e) => e.p95ms > 0).reduce((s, e) => s + e.p95ms, 0) /
    ENGINE_METRICS.filter((e) => e.p95ms > 0).length;
  const totalRps = ENGINE_METRICS.reduce((s, e) => s + e.rps, 0);

  return (
    <ScreenContainer containerClassName="bg-background">
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: colors.border, backgroundColor: colors.background }]}>
        <View>
          <Text style={[styles.headerTitle, { color: colors.foreground }]}>Monitor</Text>
          <Text style={[styles.headerSub, { color: colors.muted }]}>Observability · eco-base</Text>
        </View>
        <TouchableOpacity onPress={onRefresh}>
          <IconSymbol name="arrow.clockwise" size={20} color={colors.primary} />
        </TouchableOpacity>
      </View>

      <ScrollView
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
        contentContainerStyle={styles.scrollContent}
      >
        {/* SLO Overview */}
        <Text style={[styles.sectionTitle, { color: colors.muted }]}>SLO OVERVIEW</Text>
        <View style={styles.sloGrid}>
          <View style={[styles.sloCard, { backgroundColor: colors.surface, borderColor: colors.border }]}>
            <Text style={[styles.sloValue, { color: "#10B981" }]}>99.97%</Text>
            <Text style={[styles.sloLabel, { color: colors.muted }]}>Availability</Text>
            <Text style={[styles.sloTarget, { color: colors.muted }]}>Target ≥99.99%</Text>
          </View>
          <View style={[styles.sloCard, { backgroundColor: colors.surface, borderColor: colors.border }]}>
            <Text style={[styles.sloValue, { color: avgP95 > 200 ? "#F59E0B" : "#10B981" }]}>
              {Math.round(avgP95)}ms
            </Text>
            <Text style={[styles.sloLabel, { color: colors.muted }]}>P95 Latency</Text>
            <Text style={[styles.sloTarget, { color: colors.muted }]}>Target ≤200ms</Text>
          </View>
          <View style={[styles.sloCard, { backgroundColor: colors.surface, borderColor: colors.border }]}>
            <Text style={[styles.sloValue, { color: "#10B981" }]}>0.08%</Text>
            <Text style={[styles.sloLabel, { color: colors.muted }]}>Error Rate</Text>
            <Text style={[styles.sloTarget, { color: colors.muted }]}>Target ≤0.1%</Text>
          </View>
        </View>

        {/* Quick metrics */}
        <View style={styles.metricsRow}>
          <View style={[styles.metricChip, { backgroundColor: colors.surface, borderColor: colors.border }]}>
            <Text style={[styles.metricChipValue, { color: colors.primary }]}>{totalRps}</Text>
            <Text style={[styles.metricChipLabel, { color: colors.muted }]}>Req/s</Text>
          </View>
          <View style={[styles.metricChip, { backgroundColor: colors.surface, borderColor: colors.border }]}>
            <Text style={[styles.metricChipValue, { color: colors.primary }]}>{healthyEngines}/7</Text>
            <Text style={[styles.metricChipLabel, { color: colors.muted }]}>Engines Up</Text>
          </View>
          <View style={[styles.metricChip, { backgroundColor: colors.surface, borderColor: colors.border }]}>
            <Text style={[styles.metricChipValue, { color: ALERTS.filter((a) => a.severity === "critical").length > 0 ? "#EF4444" : "#10B981" }]}>
              {ALERTS.filter((a) => a.severity === "critical").length}
            </Text>
            <Text style={[styles.metricChipLabel, { color: colors.muted }]}>Critical</Text>
          </View>
          <View style={[styles.metricChip, { backgroundColor: colors.surface, borderColor: colors.border }]}>
            <Text style={[styles.metricChipValue, { color: colors.primary }]}>12</Text>
            <Text style={[styles.metricChipLabel, { color: colors.muted }]}>Active Pods</Text>
          </View>
        </View>

        {/* Engine Health Grid */}
        <Text style={[styles.sectionTitle, { color: colors.muted }]}>INFERENCE ENGINE HEALTH</Text>
        {ENGINE_METRICS.map((engine) => (
          <View key={engine.id} style={[styles.engineRow, { backgroundColor: colors.surface, borderColor: colors.border }]}>
            <View style={[styles.engineStatusDot, { backgroundColor: STATUS_COLOR[engine.status] }]} />
            <Text style={[styles.engineName, { color: colors.foreground }]}>{engine.name}</Text>
            <View style={styles.engineStats}>
              <Text style={[styles.engineStat, { color: engine.p95ms > 200 ? "#F59E0B" : colors.muted }]}>
                {engine.p95ms > 0 ? `${engine.p95ms}ms` : "—"}
              </Text>
              <Text style={[styles.engineStat, { color: colors.muted }]}>
                {engine.rps > 0 ? `${engine.rps} r/s` : "—"}
              </Text>
              <Text style={[styles.engineStat, { color: engine.errorRate > 1 ? "#EF4444" : colors.muted }]}>
                {engine.errorRate > 0 ? `${engine.errorRate}% err` : "0% err"}
              </Text>
            </View>
          </View>
        ))}

        {/* Active Alerts */}
        <Text style={[styles.sectionTitle, { color: colors.muted }]}>ACTIVE ALERTS ({ALERTS.length})</Text>
        {ALERTS.map((alert) => (
          <View key={alert.id} style={[styles.alertCard, { backgroundColor: colors.surface, borderColor: ALERT_COLOR[alert.severity] + "44", borderLeftColor: ALERT_COLOR[alert.severity] }]}>
            <View style={styles.alertHeader}>
              <Text style={[styles.alertName, { color: colors.foreground }]}>{alert.name}</Text>
              <View style={[styles.alertBadge, { backgroundColor: ALERT_COLOR[alert.severity] + "22" }]}>
                <Text style={[styles.alertSeverity, { color: ALERT_COLOR[alert.severity] }]}>
                  {alert.severity.toUpperCase()}
                </Text>
              </View>
            </View>
            <Text style={[styles.alertMessage, { color: colors.muted }]}>{alert.message}</Text>
            <View style={styles.alertFooter}>
              <Text style={[styles.alertPlatform, { color: colors.primary }]}>{alert.platform}</Text>
              <Text style={[styles.alertTime, { color: colors.muted }]}>{alert.time}</Text>
            </View>
          </View>
        ))}
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
  headerSub: { fontSize: 11, marginTop: 1 },
  scrollContent: { padding: 16 },
  sectionTitle: { fontSize: 11, fontWeight: "700", letterSpacing: 1, marginTop: 16, marginBottom: 10 },
  sloGrid: { flexDirection: "row", gap: 8, marginBottom: 12 },
  sloCard: {
    flex: 1,
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
    alignItems: "center",
    gap: 2,
  },
  sloValue: { fontSize: 18, fontWeight: "800" },
  sloLabel: { fontSize: 11, fontWeight: "600" },
  sloTarget: { fontSize: 9, marginTop: 2 },
  metricsRow: { flexDirection: "row", gap: 8, marginBottom: 4 },
  metricChip: {
    flex: 1,
    borderRadius: 10,
    borderWidth: 1,
    padding: 10,
    alignItems: "center",
    gap: 2,
  },
  metricChipValue: { fontSize: 16, fontWeight: "700" },
  metricChipLabel: { fontSize: 9, fontWeight: "600" },
  engineRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 6,
  },
  engineStatusDot: { width: 8, height: 8, borderRadius: 4 },
  engineName: { flex: 1, fontSize: 13, fontWeight: "600" },
  engineStats: { flexDirection: "row", gap: 10 },
  engineStat: { fontSize: 11 },
  alertCard: {
    borderRadius: 10,
    borderWidth: 1,
    borderLeftWidth: 3,
    padding: 12,
    marginBottom: 8,
    gap: 6,
  },
  alertHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  alertName: { fontSize: 13, fontWeight: "700", flex: 1 },
  alertBadge: { paddingHorizontal: 7, paddingVertical: 3, borderRadius: 6 },
  alertSeverity: { fontSize: 10, fontWeight: "700" },
  alertMessage: { fontSize: 12, lineHeight: 16 },
  alertFooter: { flexDirection: "row", justifyContent: "space-between" },
  alertPlatform: { fontSize: 11, fontWeight: "600" },
  alertTime: { fontSize: 11 },
});
