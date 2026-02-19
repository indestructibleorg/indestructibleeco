import { app, BrowserWindow } from "electron";
import { autoUpdater } from "electron-updater";
import path from "path";
const isDev = process.env.NODE_ENV === "development";
function createWindow() {
  const win = new BrowserWindow({ width: 1280, height: 800, webPreferences: { preload: path.join(__dirname, "preload.js"), contextIsolation: true, nodeIntegration: false } });
  if (isDev) { win.loadURL("http://localhost:5174"); } else { win.loadFile(path.join(__dirname, "../../renderer/index.html")); autoUpdater.checkForUpdatesAndNotify(); }
}
app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
