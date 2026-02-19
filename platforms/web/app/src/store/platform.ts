import { create } from "zustand";

interface Platform {
  id: string;
  name: string;
  slug: string;
  type: string;
  status: string;
  capabilities: string[];
}

interface PlatformState {
  platforms: Platform[];
  loading: boolean;
  setPlatforms: (p: Platform[]) => void;
  setLoading: (v: boolean) => void;
  addPlatform: (p: Platform) => void;
  removePlatform: (id: string) => void;
}

export const usePlatformStore = create<PlatformState>((set) => ({
  platforms: [],
  loading: false,
  setPlatforms: (platforms) => set({ platforms }),
  setLoading: (loading) => set({ loading }),
  addPlatform: (p) => set((s) => ({ platforms: [...s.platforms, p] })),
  removePlatform: (id) =>
    set((s) => ({ platforms: s.platforms.filter((p) => p.id !== id) })),
}));
