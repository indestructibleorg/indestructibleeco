import React from "react";
import { cn } from "../utils/cn";

export interface StatusIndicatorProps {
  status: "healthy" | "degraded" | "unhealthy" | "unknown" | "active" | "inactive" | "deploying" | "error" | "maintenance";
  label?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const statusColors: Record<string, string> = {
  healthy: "bg-green-500",
  active: "bg-green-500",
  degraded: "bg-yellow-500",
  deploying: "bg-blue-500 animate-pulse",
  maintenance: "bg-yellow-500",
  unhealthy: "bg-red-500",
  error: "bg-red-500",
  inactive: "bg-gray-400",
  unknown: "bg-gray-400",
};

const sizeMap = {
  sm: "h-2 w-2",
  md: "h-3 w-3",
  lg: "h-4 w-4",
};

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  size = "md",
  className,
}) => (
  <span className={cn("inline-flex items-center gap-2", className)}>
    <span className={cn("rounded-full", sizeMap[size], statusColors[status] || statusColors.unknown)} />
    {label && <span className="text-sm text-gray-700">{label || status}</span>}
  </span>
);