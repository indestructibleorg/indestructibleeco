const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  getVersion: () => ipcRenderer.invoke("app:version"),
  getPlatform: () => ipcRenderer.invoke("app:platform"),
  installUpdate: () => ipcRenderer.invoke("update:install"),
  onUpdateAvailable: (cb) => ipcRenderer.on("update:available", (_e, info) => cb(info)),
  onUpdateDownloaded: (cb) => ipcRenderer.on("update:downloaded", (_e, info) => cb(info)),
});