import React, { useEffect } from "react";
import { useAI } from "../hooks/useAI";

export function ModelSelector() {
  const { models, selectedModel, setSelectedModel, fetchModels } = useAI();

  useEffect(() => { fetchModels(); }, [fetchModels]);

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <label style={{ fontSize: "0.875rem", color: "#64748b" }}>Model:</label>
      <select
        value={selectedModel}
        onChange={(e) => setSelectedModel(e.target.value)}
        style={{ padding: "4px 8px", border: "1px solid #cbd5e1", borderRadius: 4, background: "#fff" }}
      >
        <option value="default">Default</option>
        {models.map((m) => (
          <option key={m.id} value={m.id}>
            {m.name} ({m.provider}) — {m.status}
          </option>
        ))}
      </select>
    </div>
  );
}
