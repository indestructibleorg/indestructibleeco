/**
 * @ECO-governed
 * @ECO-layer: aep-engine-app
 * @ECO-semantic: ui-problem-card
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

import { View, Text, TouchableOpacity } from "react-native";
import { cn } from "@/lib/utils";

export type ProblemSeverity = "critical" | "high" | "medium" | "low";

export interface ProblemCardProps {
  type: string;
  severity: ProblemSeverity;
  description: string;
  location?: string;
  onPress?: () => void;
  className?: string;
}

/**
 * ProblemCard - 顯示檢測到的問題的卡片元件
 *
 * 用於檢測結果螢幕中的問題展示
 */
export function ProblemCard({
  type,
  severity,
  description,
  location,
  onPress,
  className,
}: ProblemCardProps) {
  const severityConfig = {
    critical: { color: "bg-red-600", label: "Critical", icon: "🔴" },
    high: { color: "bg-orange-600", label: "High", icon: "🟠" },
    medium: { color: "bg-yellow-600", label: "Medium", icon: "🟡" },
    low: { color: "bg-blue-600", label: "Low", icon: "🔵" },
  };

  const config = severityConfig[severity];

  return (
    <TouchableOpacity
      onPress={onPress}
      className={cn(
        "bg-surface rounded-lg p-4 border border-border active:opacity-70",
        className
      )}
    >
      <View className="flex-row items-start justify-between mb-2">
        <View className="flex-row items-center gap-2 flex-1">
          <Text className="text-lg">{config.icon}</Text>
          <View className="flex-1">
            <Text className="text-sm font-medium text-foreground">{type}</Text>
            <Text className={cn("text-xs font-semibold", config.color === "bg-red-600" ? "text-red-600" : config.color === "bg-orange-600" ? "text-orange-600" : config.color === "bg-yellow-600" ? "text-yellow-600" : "text-blue-600")}>
              {config.label}
            </Text>
          </View>
        </View>
        <Text className="text-lg text-muted">→</Text>
      </View>

      <Text className="text-sm text-foreground mb-2">{description}</Text>

      {location && (
        <Text className="text-xs text-muted">{location}</Text>
      )}
    </TouchableOpacity>
  );
}
