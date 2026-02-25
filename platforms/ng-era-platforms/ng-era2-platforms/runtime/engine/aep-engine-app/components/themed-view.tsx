/**
 * @ECO-governed
 * @ECO-layer: aep-engine-app
 * @ECO-semantic: components-themed-view
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

import { View, type ViewProps } from "react-native";

import { cn } from "@/lib/utils";

export interface ThemedViewProps extends ViewProps {
  className?: string;
}

/**
 * A View component with automatic theme-aware background.
 * Uses NativeWind for styling - pass className for additional styles.
 */
export function ThemedView({ className, ...otherProps }: ThemedViewProps) {
  return <View className={cn("bg-background", className)} {...otherProps} />;
}
