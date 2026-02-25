/**
 * @ECO-governed
 * @ECO-layer: aep-engine-app
 * @ECO-semantic: ui-statistic-card
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

import { View, Text } from "react-native";
import { cn } from "@/lib/utils";

export interface StatisticCardProps {
  label: string;
  value: string | number;
  icon?: string;
  variant?: "default" | "success" | "warning" | "error";
  className?: string;
}

/**
 * StatisticCard - 顯示統計數據的卡片元件
 *
 * 用於首頁和報告螢幕中的統計資訊展示
 */
export function StatisticCard({
  label,
  value,
  icon = "📊",
  variant = "default",
  className,
}: StatisticCardProps) {
  const variantStyles = {
    default: "bg-primary bg-opacity-10",
    success: "bg-success bg-opacity-10",
    warning: "bg-warning bg-opacity-10",
    error: "bg-error bg-opacity-10",
  };

  const valueColorStyles = {
    default: "text-foreground",
    success: "text-success",
    warning: "text-warning",
    error: "text-error",
  };

  return (
    <View
      className={cn(
        "bg-surface rounded-xl p-4 border border-border flex-row justify-between items-center",
        className
      )}
    >
      <View>
        <Text className="text-sm text-muted mb-1">{label}</Text>
        <Text className={cn("text-3xl font-bold", valueColorStyles[variant])}>
          {value}
        </Text>
      </View>
      <View className={cn("rounded-lg p-3", variantStyles[variant])}>
        <Text className="text-2xl">{icon}</Text>
      </View>
    </View>
  );
}
