import { useEffect } from "react";
import { useAI } from "../hooks/useAI";

export function ModelSelector() {
  const { models, selectedModel, setSelectedModel, fetchModels } = useAI();

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="model-selector" className="text-xs text-muted">Model:</label>
      <select
        id="model-selector"
        className="select"
        value={selectedModel}
        onChange={(e) => setSelectedModel(e.target.value)}
      >
        <option value="default">Default</option>
        {models.map((m) => (
          <option key={m.id} value={m.id}>
            {m.name || m.id} ({m.provider}) — {m.status}
          </option>
        ))}
      </select>
    </div>
  );
}