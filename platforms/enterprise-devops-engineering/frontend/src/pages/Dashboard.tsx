import { useState, useEffect } from "react";
import { api } from "../lib/api";

interface HealthData {
  status: string;
  service: string;
  version: string;
  engines?: string[];
  uptime_seconds?: number;
  models_registered?: number;
  timestamp?: string;
}

interface ModelInfo {
  id: string;
  name?: string;
  provider?: string;
  status: string;
  capabilities?: string[];
}

export default function Dashboard() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [_recentJobs, _setRecentJobs] = useState<any[]>([]);

  useEffect(() => {
    api.health()
      .then((d) => setHealth(d as any))
      .catch(() => setHealth({ status: "unreachable", service: "unknown", version: "?" }));

    api.models()
      .then((data: any) => {
        if (Array.isArray(data)) setModels(data);
        else if (data?.models) setModels(data.models);
        else if (data?.data) setModels(data.data);
      })
      .catch(() => {});
  }, []);

  const statusClass = (s: string) =>
    s === "healthy" || s === "available" || s === "ready"
      ? "status-healthy"
      : s === "degraded" || s === "loading"
      ? "status-degraded"
      : "status-error";

  const badgeClass = (s: string) =>
    s === "available" || s === "ready" ? "badge-success"
    : s === "loading" ? "badge-warning"
    : "badge-danger";

  return (
    <div>
      <h1 className="page-title">Dashboard</h1>

      <div className="grid grid-3 gap-4 mb-4">
        {/* Health */}
        <div className="card">
          <div className="text-xs text-muted mb-3">Service Health</div>
          {health ? (
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <span className={`status-dot ${statusClass(health.status)}`} />
                <span className="text-lg font-bold">{health.status}</span>
              </div>
              <div className="text-xs text-muted">
                {health.service} v{health.version}
              </div>
              {health.uptime_seconds !== undefined && (
                <div className="text-xs text-muted">
                  Uptime: {Math.floor(health.uptime_seconds / 3600)}h{" "}
                  {Math.floor((health.uptime_seconds % 3600) / 60)}m
                </div>
              )}
            </div>
          ) : (
            <div className="text-sm text-muted animate-pulse">Loading...</div>
          )}
        </div>

        {/* Models Count */}
        <div className="card">
          <div className="text-xs text-muted mb-3">Models Registered</div>
          <div className="text-xl font-bold">{models.length}</div>
          <div className="text-xs text-muted mt-4">
            {models.filter((m) => m.status === "available").length} available
          </div>
        </div>

        {/* Engines */}
        <div className="card">
          <div className="text-xs text-muted mb-3">Inference Engines</div>
          <div className="text-xl font-bold">{health?.engines?.length ?? 0}</div>
          {health?.engines && (
            <div className="text-xs text-muted mt-4" style={{ wordBreak: "break-word" }}>
              {health.engines.join(", ")}
            </div>
          )}
        </div>
      </div>

      {/* Models Table */}
      <div className="card">
        <div className="text-xs text-muted mb-3">Models ({models.length})</div>
        <div className="flex flex-col gap-2" style={{ maxHeight: 320, overflowY: "auto" }}>
          {models.length === 0 && (
            <div className="text-sm text-muted">No models loaded</div>
          )}
          {models.map((m) => (
            <div key={m.id} className="table-row">
              <div className="flex items-center gap-3">
                <span className="font-mono text-sm">{m.id}</span>
                {m.provider && (
                  <span className="text-xs text-muted">{m.provider}</span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {m.capabilities && m.capabilities.slice(0, 3).map((c) => (
                  <span key={c} className="badge badge-info">{c}</span>
                ))}
                <span className={`badge ${badgeClass(m.status)}`}>{m.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}