import { contextBridge, ipcRenderer } from "electron";
contextBridge.exposeInMainWorld("electronAPI", { getVersion: () => ipcRenderer.invoke("get-version"), minimize: () => ipcRenderer.send("window:minimize"), close: () => ipcRenderer.send("window:close") });
