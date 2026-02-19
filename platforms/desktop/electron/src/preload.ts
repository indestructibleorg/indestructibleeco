import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("electronAPI", {
  // ── App Info ────────────────────────────────────────────────
  getVersion: (): Promise<string> => ipcRenderer.invoke("app:version"),
  getPlatform: (): Promise<string> => ipcRenderer.invoke("app:platform"),
  isDev: (): Promise<boolean> => ipcRenderer.invoke("app:isdev"),

  // ── Auto-Updater ───────────────────────────────────────────
  onUpdateAvailable: (callback: () => void): void => {
    ipcRenderer.on("update:available", callback);
  },
  onUpdateDownloaded: (callback: () => void): void => {
    ipcRenderer.on("update:downloaded", callback);
  },

  // ── Window Controls ────────────────────────────────────────
  minimize: (): void => {
    ipcRenderer.send("window:minimize");
  },
  maximize: (): void => {
    ipcRenderer.send("window:maximize");
  },
  close: (): void => {
    ipcRenderer.send("window:close");
  },
});