/**
 * @ECO-governed
 * @ECO-layer: aep-engine-app
 * @ECO-semantic: ui-event-card
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

import { View, Text, TouchableOpacity } from "react-native";
import { cn } from "@/lib/utils";

export interface EventCardProps {
  type: "Execution" | "Detection" | "Rollback" | "Migration" | "Validation";
  time: string;
  status: "success" | "warning" | "error" | "info";
  onPress?: () => void;
  className?: string;
}

/**
 * EventCard - 顯示單個治理事件的卡片元件
 *
 * 用於首頁和事件流螢幕中的事件展示
 */
export function EventCard({
  type,
  time,
  status,
  onPress,
  className,
}: EventCardProps) {
  const statusColorMap = {
    success: "bg-success",
    warning: "bg-warning",
    error: "bg-error",
    info: "bg-primary",
  };

  const typeIconMap = {
    Execution: "▶️",
    Detection: "🔍",
    Rollback: "↩️",
    Migration: "📦",
    Validation: "✓",
  };

  return (
    <TouchableOpacity
      onPress={onPress}
      className={cn(
        "bg-surface rounded-lg p-4 border border-border flex-row items-center gap-3 active:opacity-70",
        className
      )}
    >
      <View className={cn("w-2 h-2 rounded-full", statusColorMap[status])} />
      <View className="flex-1">
        <View className="flex-row items-center gap-2 mb-1">
          <Text className="text-sm">{typeIconMap[type]}</Text>
          <Text className="text-sm font-medium text-foreground">{type}</Text>
        </View>
        <Text className="text-xs text-muted">{time}</Text>
      </View>
      <Text className="text-lg text-muted">→</Text>
    </TouchableOpacity>
  );
}
