const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const { autoUpdater } = require("electron-updater");

let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 680,
    title: "IndestructibleEco",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  if (process.env.NODE_ENV === "development") {
    mainWindow.loadURL("http://localhost:5173");
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  }

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();

  // Auto-update check (production only)
  if (process.env.NODE_ENV !== "development") {
    autoUpdater.checkForUpdatesAndNotify();
  }

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

// ─── IPC Handlers (typed bridge via electron-trpc pattern) ───

ipcMain.handle("app:version", () => app.getVersion());

ipcMain.handle("app:platform", () => ({
  platform: process.platform,
  arch: process.arch,
  version: process.versions.electron,
  node: process.versions.node,
  chrome: process.versions.chrome,
}));

// ─── Auto-Updater Events ───

autoUpdater.on("update-available", (info) => {
  mainWindow?.webContents.send("update:available", info);
});

autoUpdater.on("update-downloaded", (info) => {
  mainWindow?.webContents.send("update:downloaded", info);
});

ipcMain.handle("update:install", () => {
  autoUpdater.quitAndInstall();
});