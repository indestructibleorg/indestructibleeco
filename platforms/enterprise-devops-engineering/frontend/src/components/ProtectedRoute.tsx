import React from "react";
import { Navigate } from "react-router-dom";
import { useAuthStore } from "../store/auth";

export function ProtectedRoute({ children }: Readonly<{ children: React.ReactNode }>) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const token = useAuthStore((s) => s.token);

  if (!isAuthenticated && !token) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}