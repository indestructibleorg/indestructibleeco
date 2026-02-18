import React from "react";
import { Routes, Route, Link, useLocation } from "react-router-dom";

const NAV_ITEMS = [
  { path: "/", label: "Dashboard" },
  { path: "/platforms", label: "Platforms" },
  { path: "/ai", label: "AI Engine" },
  { path: "/yaml", label: "YAML Governance" },
  { path: "/ecosystem", label: "Ecosystem" },
];

function NavLink({ to, label }) {
  const { pathname } = useLocation();
  const active = pathname === to;
  return (
    <Link
      to={to}
      className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
        active ? "bg-blue-600 text-white" : "text-gray-300 hover:bg-gray-700 hover:text-white"
      }`}
    >
      {label}
    </Link>
  );
}

function Dashboard() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">IndestructibleEco Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatusCard title="API Service" status="healthy" uri="indestructibleeco://backend/api" />
        <StatusCard title="AI Service" status="healthy" uri="indestructibleeco://backend/ai" />
        <StatusCard title="YAML Toolkit" status="active" uri="indestructibleeco://tools/yaml-toolkit" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <MetricCard title="Active Platforms" value="4" />
        <MetricCard title="Registered Services" value="7" />
      </div>
    </div>
  );
}

function StatusCard({ title, status, uri }) {
  const colors = {
    healthy: "bg-green-500",
    active: "bg-green-500",
    degraded: "bg-yellow-500",
    unhealthy: "bg-red-500",
  };
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-300">{title}</h3>
        <span className={`h-2.5 w-2.5 rounded-full ${colors[status] || "bg-gray-500"}`} />
      </div>
      <p className="text-xs text-gray-500 font-mono truncate">{uri}</p>
    </div>
  );
}

function MetricCard({ title, value }) {
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h3 className="text-sm font-medium text-gray-400">{title}</h3>
      <p className="text-3xl font-bold text-white mt-1">{value}</p>
    </div>
  );
}

function PlatformsPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-white">Platform Modules</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {["web", "desktop", "im-integration", "chrome-extension"].map((p) => (
          <div key={p} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <h3 className="text-lg font-semibold text-white">{p}</h3>
            <p className="text-xs text-gray-500 font-mono mt-1">
              indestructibleeco://platform/module/{p}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

function AIPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-white">AI Engine</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {["vLLM", "Ollama", "TGI", "SGLang", "TensorRT", "DeepSpeed", "LMDeploy"].map((e) => (
          <div key={e} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <h3 className="text-sm font-semibold text-white">{e} Adapter</h3>
            <span className="inline-flex items-center gap-1.5 mt-2">
              <span className="h-2 w-2 rounded-full bg-green-500" />
              <span className="text-xs text-gray-400">Available</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function YAMLPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-white">YAML Governance</h1>
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <h3 className="text-sm font-medium text-gray-300 mb-2">Toolkit v1 — Mandatory Blocks</h3>
        <ul className="space-y-1 text-xs text-gray-400 font-mono">
          <li>✓ document_metadata (UUID v1, URI, URN)</li>
          <li>✓ governance_info (owner, compliance_tags)</li>
          <li>✓ registry_binding (consul, health_check)</li>
          <li>✓ vector_alignment_map (quantum-bert-xxl-v1)</li>
        </ul>
      </div>
    </div>
  );
}

function EcosystemPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-white">Ecosystem</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { name: "Prometheus", desc: "Metrics collection" },
          { name: "Grafana", desc: "Dashboards" },
          { name: "Jaeger", desc: "Distributed tracing" },
          { name: "Consul", desc: "Service discovery" },
          { name: "Loki", desc: "Log aggregation" },
          { name: "Alertmanager", desc: "Alert routing" },
        ].map((s) => (
          <div key={s.name} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <h3 className="text-sm font-semibold text-white">{s.name}</h3>
            <p className="text-xs text-gray-500 mt-1">{s.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-gray-900">
      <nav className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-white">IndestructibleEco</span>
              <span className="text-xs text-gray-500 font-mono">v1.0.0</span>
            </div>
            <div className="flex gap-1">
              {NAV_ITEMS.map((item) => (
                <NavLink key={item.path} to={item.path} label={item.label} />
              ))}
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/platforms" element={<PlatformsPage />} />
          <Route path="/ai" element={<AIPage />} />
          <Route path="/yaml" element={<YAMLPage />} />
          <Route path="/ecosystem" element={<EcosystemPage />} />
        </Routes>
      </main>
    </div>
  );
}