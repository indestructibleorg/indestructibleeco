import { create } from "zustand";

interface AiMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
  model?: string;
  engine?: string;
  latency_ms?: number;
}

interface AiState {
  messages: AiMessage[];
  selectedModel: string;
  isGenerating: boolean;
  models: { id: string; name: string; provider: string; status: string }[];
  addMessage: (msg: AiMessage) => void;
  clearMessages: () => void;
  setSelectedModel: (model: string) => void;
  setGenerating: (v: boolean) => void;
  setModels: (models: AiState["models"]) => void;
}

export const useAiStore = create<AiState>((set) => ({
  messages: [],
  selectedModel: "default",
  isGenerating: false,
  models: [],
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  clearMessages: () => set({ messages: [] }),
  setSelectedModel: (model) => set({ selectedModel: model }),
  setGenerating: (v) => set({ isGenerating: v }),
  setModels: (models) => set({ models }),
}));
