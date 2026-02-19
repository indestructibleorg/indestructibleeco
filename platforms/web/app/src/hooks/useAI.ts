import { useCallback } from "react";
import { useAiStore } from "../store/ai";
import { api } from "../lib/api";

export function useAI() {
  const { messages, selectedModel, isGenerating, models, addMessage, clearMessages, setSelectedModel, setGenerating, setModels } = useAiStore();

  const generate = useCallback(async (prompt: string) => {
    const id = crypto.randomUUID();
    addMessage({ id, role: "user", content: prompt, timestamp: Date.now() });
    setGenerating(true);
    try {
      const resp = await api.generate(prompt, selectedModel);
      addMessage({
        id: resp.request_id,
        role: "assistant",
        content: resp.content,
        timestamp: Date.now(),
        model: selectedModel,
        engine: resp.engine,
        latency_ms: resp.latency_ms,
      });
    } catch (err: any) {
      addMessage({ id: crypto.randomUUID(), role: "assistant", content: `Error: ${err.message}`, timestamp: Date.now() });
    } finally {
      setGenerating(false);
    }
  }, [selectedModel, addMessage, setGenerating]);

  const fetchModels = useCallback(async () => {
    try {
      const resp = await api.models();
      setModels(resp as any);
    } catch {}
  }, [setModels]);

  return { messages, selectedModel, isGenerating, models, generate, clearMessages, setSelectedModel, fetchModels };
}
