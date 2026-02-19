import React from "react";
import { Link, useLocation, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const NAV_ITEMS = [
  { path: "/", label: "Dashboard", icon: "📊" },
  { path: "/ai", label: "AI Playground", icon: "🤖" },
  { path: "/models", label: "Models", icon: "🧠" },
  { path: "/platforms", label: "Platforms", icon: "🔌" },
  { path: "/settings", label: "Settings", icon: "⚙️" },
];

export function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside style={{ width: 240, background: "#0f172a", color: "#e2e8f0", padding: "1rem", display: "flex", flexDirection: "column" }}>
        <div style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "2rem", color: "#38bdf8" }}>
          IndestructibleEco
        </div>
        <nav style={{ flex: 1 }}>
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "0.5rem 0.75rem",
                marginBottom: 4,
                borderRadius: 6,
                textDecoration: "none",
                color: location.pathname === item.path ? "#38bdf8" : "#94a3b8",
                background: location.pathname === item.path ? "#1e293b" : "transparent",
              }}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
        <div style={{ borderTop: "1px solid #334155", paddingTop: "1rem" }}>
          <div style={{ fontSize: "0.875rem", color: "#94a3b8" }}>{user?.email}</div>
          <button
            onClick={logout}
            style={{ marginTop: 8, background: "none", border: "1px solid #475569", color: "#94a3b8", padding: "4px 12px", borderRadius: 4, cursor: "pointer" }}
          >
            Logout
          </button>
        </div>
      </aside>
      <main style={{ flex: 1, background: "#f8fafc", padding: "1.5rem" }}>
        <Outlet />
      </main>
    </div>
  );
}
