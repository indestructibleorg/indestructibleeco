// Fallback for using MaterialIcons on Android and web.

import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { SymbolWeight, SymbolViewProps } from "expo-symbols";
import { ComponentProps } from "react";
import { OpaqueColorValue, type StyleProp, type TextStyle } from "react-native";

type IconMapping = Record<SymbolViewProps["name"], ComponentProps<typeof MaterialIcons>["name"]>;
type IconSymbolName = keyof typeof MAPPING;

/**
 * SF Symbols → Material Icons mapping for eco-base mobile app
 */
const MAPPING = {
  // Tab icons
  "house.fill": "home",
  "cpu.fill": "memory",
  "chart.bar.fill": "bar-chart",
  "gearshape.fill": "settings",
  "bubble.left.fill": "chat",
  "server.rack": "dns",
  "waveform": "show-chart",
  // Navigation
  "chevron.left": "chevron-left",
  "chevron.right": "chevron-right",
  "chevron.left.forwardslash.chevron.right": "code",
  "paperplane.fill": "send",
  // Actions
  "arrow.clockwise": "refresh",
  "arrow.counterclockwise": "history",
  "xmark": "close",
  "checkmark": "check",
  "plus": "add",
  "minus": "remove",
  "trash": "delete",
  "square.and.arrow.up": "share",
  "doc.on.clipboard": "content-copy",
  // Status
  "circle.fill": "circle",
  "exclamationmark.triangle.fill": "warning",
  "checkmark.circle.fill": "check-circle",
  "xmark.circle.fill": "cancel",
  "bolt.fill": "bolt",
  "antenna.radiowaves.left.and.right": "wifi",
  // Engine icons
  "cpu": "memory",
  "network": "account-tree",
  "lock.shield.fill": "security",
  "eye": "visibility",
  "terminal.fill": "terminal",
} as IconMapping;

/**
 * An icon component that uses native SF Symbols on iOS, and Material Icons on Android and web.
 */
export function IconSymbol({
  name,
  size = 24,
  color,
  style,
}: {
  name: IconSymbolName;
  size?: number;
  color: string | OpaqueColorValue;
  style?: StyleProp<TextStyle>;
  weight?: SymbolWeight;
}) {
  return <MaterialIcons color={color} size={size} name={MAPPING[name]} style={style} />;
}
