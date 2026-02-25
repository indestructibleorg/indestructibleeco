import { useState } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  RefreshControl,
} from "react-native";
import { ScreenContainer } from "@/components/screen-container";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { useColors } from "@/hooks/use-colors";

// ─── Types ───────────────────────────────────────────────────────────────────

type ServiceStatus = "running" | "degraded" | "stopped";

type Platform = {
  id: string;
  name: string;
  subtitle: string;
  namespace: string;
  pods: { running: number; total: number };
  status: ServiceStatus;
  lastSync: string;
  description: string;
};

type SharedService = {
  id: string;
  name: string;
  component: string;
  status: ServiceStatus;
  endpoint: string;
};

// ─── Data ────────────────────────────────────────────────────────────────────

const PLATFORMS: Platform[] = [
  {
    id: "p01",
    name: "Platform-01",
    subtitle: "IndestructibleAutoOps",
    namespace: "eco-production",
    pods: { running: 3, total: 3 },
    status: "running",
    lastSync: "2m ago",
    description: "Observability · Self-healing · Repair orchestration",
  },
  {
    id: "p02",
    name: "Platform-02",
    subtitle: "IAOps",
    namespace: "eco-production",
    pods: { running: 2, total: 3 },
    status: "degraded",
    lastSync: "5m ago",
    description: "IaC · GitOps · Supply chain compliance",
  },
  {
    id: "p03",
    name: "Platform-03",
    subtitle: "MachineNativeOps",
    namespace: "eco-production",
    pods: { running: 0, total: 2 },
    status: "stopped",
    lastSync: "1h ago",
    description: "Node baseline · Hardware management · Edge agents",
  },
];

const SHARED_SERVICES: SharedService[] = [
  { id: "auth",   name: "Auth Service",   component: "Keycloak/Supabase", status: "running",  endpoint: "http://auth-svc:8080" },
  { id: "memory", name: "Memory Hub",     component: "pgvector + Embeddings", status: "running",  endpoint: "http://memory-svc:8082" },
  { id: "event",  name: "Event Bus",      component: "Kafka/Redis Streams", status: "running",  endpoint: "http://event-svc:9092" },
  { id: "policy", name: "Policy & Audit", component: "OPA/Kyverno",        status: "degraded", endpoint: "http://policy-svc:8181" },
  { id: "infra",  name: "Infra Manager",  component: "ArgoCD/Helm",         status: "running",  endpoint: "http://infra-svc:8083" },
];

const STATUS_CONFIG: Record<ServiceStatus, { color: string; label: string }> = {
  running:  { color: "#10B981", label: "Running" },
  degraded: { color: "#F59E0B", label: "Degraded" },
  stopped:  { color: "#EF4444", label: "Stopped" },
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function PlatformsScreen() {
  const colors = useColors();
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = () => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 1500);
  };

  const renderPlatformCard = ({ item }: { item: Platform }) => {
    const statusCfg = STATUS_CONFIG[item.status];
    return (
      <View style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }]}>
        {/* Card header */}
        <View style={styles.cardHeader}>
          <View>
            <Text style={[styles.platformName, { color: colors.foreground }]}>{item.name}</Text>
            <Text style={[styles.platformSubtitle, { color: colors.primary }]}>{item.subtitle}</Text>
          </View>
          <View style={[styles.statusBadge, { backgroundColor: statusCfg.color + "22", borderColor: statusCfg.color + "44" }]}>
            <View style={[styles.statusDot, { backgroundColor: statusCfg.color }]} />
            <Text style={[styles.statusLabel, { color: statusCfg.color }]}>{statusCfg.label}</Text>
          </View>
        </View>

        {/* Namespace & pods */}
        <View style={styles.metaRow}>
          <View style={styles.metaItem}>
            <Text style={[styles.metaKey, { color: colors.muted }]}>Namespace</Text>
            <Text style={[styles.metaValue, { color: colors.foreground }]}>{item.namespace}</Text>
          </View>
          <View style={styles.metaItem}>
            <Text style={[styles.metaKey, { color: colors.muted }]}>Pods</Text>
            <Text style={[styles.metaValue, { color: item.pods.running === item.pods.total ? "#10B981" : "#F59E0B" }]}>
              {item.pods.running}/{item.pods.total}
            </Text>
          </View>
          <View style={styles.metaItem}>
            <Text style={[styles.metaKey, { color: colors.muted }]}>Last Sync</Text>
            <Text style={[styles.metaValue, { color: colors.foreground }]}>{item.lastSync}</Text>
          </View>
        </View>

        {/* Description */}
        <Text style={[styles.description, { color: colors.muted }]}>{item.description}</Text>

        {/* Actions */}
        <View style={styles.actions}>
          <TouchableOpacity style={[styles.actionBtn, { borderColor: colors.border }]}>
            <IconSymbol name="terminal.fill" size={14} color={colors.primary} />
            <Text style={[styles.actionText, { color: colors.primary }]}>Logs</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.actionBtn, { borderColor: colors.border }]}>
            <IconSymbol name="arrow.clockwise" size={14} color={colors.success} />
            <Text style={[styles.actionText, { color: colors.success }]}>Sync</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.actionBtn, { borderColor: colors.border }]}>
            <IconSymbol name="arrow.counterclockwise" size={14} color={colors.warning} />
            <Text style={[styles.actionText, { color: colors.warning }]}>Rollback</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  return (
    <ScreenContainer containerClassName="bg-background">
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: colors.border, backgroundColor: colors.background }]}>
        <View>
          <Text style={[styles.headerTitle, { color: colors.foreground }]}>Platforms</Text>
          <Text style={[styles.headerSub, { color: colors.muted }]}>eco-base · GKE asia-east1</Text>
        </View>
        <TouchableOpacity onPress={onRefresh}>
          <IconSymbol name="arrow.clockwise" size={20} color={colors.primary} />
        </TouchableOpacity>
      </View>

      <ScrollView
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
        contentContainerStyle={styles.scrollContent}
      >
        {/* Platform cards */}
        <Text style={[styles.sectionTitle, { color: colors.muted }]}>BUSINESS DOMAINS</Text>
        {PLATFORMS.map((item) => (
          <View key={item.id}>{renderPlatformCard({ item })}</View>
        ))}

        {/* Shared Kernel */}
        <Text style={[styles.sectionTitle, { color: colors.muted }]}>SHARED KERNEL (CONTROL PLANE)</Text>
        {SHARED_SERVICES.map((svc) => {
          const statusCfg = STATUS_CONFIG[svc.status];
          return (
            <View key={svc.id} style={[styles.serviceRow, { backgroundColor: colors.surface, borderColor: colors.border }]}>
              <View style={[styles.statusDot, { backgroundColor: statusCfg.color }]} />
              <View style={styles.serviceInfo}>
                <Text style={[styles.serviceName, { color: colors.foreground }]}>{svc.name}</Text>
                <Text style={[styles.serviceComponent, { color: colors.muted }]}>{svc.component}</Text>
              </View>
              <Text style={[styles.serviceEndpoint, { color: colors.muted }]}>{svc.endpoint.replace("http://", "")}</Text>
            </View>
          );
        })}
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
  scrollContent: { padding: 16, gap: 8 },
  sectionTitle: { fontSize: 11, fontWeight: "700", letterSpacing: 1, marginTop: 8, marginBottom: 8 },
  card: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
    marginBottom: 10,
    gap: 10,
  },
  cardHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" },
  platformName: { fontSize: 16, fontWeight: "700" },
  platformSubtitle: { fontSize: 12, fontWeight: "600", marginTop: 2 },
  statusBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
  },
  statusDot: { width: 7, height: 7, borderRadius: 4 },
  statusLabel: { fontSize: 11, fontWeight: "600" },
  metaRow: { flexDirection: "row", gap: 16 },
  metaItem: { gap: 2 },
  metaKey: { fontSize: 10, fontWeight: "600", letterSpacing: 0.5 },
  metaValue: { fontSize: 13, fontWeight: "600" },
  description: { fontSize: 12, lineHeight: 16 },
  actions: { flexDirection: "row", gap: 8 },
  actionBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
  },
  actionText: { fontSize: 12, fontWeight: "600" },
  serviceRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 6,
  },
  serviceInfo: { flex: 1 },
  serviceName: { fontSize: 14, fontWeight: "600" },
  serviceComponent: { fontSize: 11, marginTop: 1 },
  serviceEndpoint: { fontSize: 10, fontFamily: "monospace" },
});
