import { app, BrowserWindow, ipcMain, Menu, Tray } from "electron";
import { autoUpdater } from "electron-updater";
import path from "path";

const isDev = process.env.NODE_ENV === "development";
let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
    titleBarStyle: "hiddenInset",
    show: false,
  });

  mainWindow.once("ready-to-show", () => {
    mainWindow?.show();
  });

  if (isDev) {
    mainWindow.loadURL("http://localhost:5173");
    mainWindow.webContents.openDevTools({ mode: "detach" });
  } else {
    mainWindow.loadFile(path.join(__dirname, "../../renderer/index.html"));
    autoUpdater.checkForUpdatesAndNotify();
  }

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// ── IPC Handlers ────────────────────────────────────────────
ipcMain.handle("app:version", () => app.getVersion());
ipcMain.handle("app:platform", () => process.platform);
ipcMain.handle("app:isdev", () => isDev);

// ── System Tray ─────────────────────────────────────────────
function createTray(): void {
  const iconPath = path.join(__dirname, "../../resources/icon.png");
  try {
    tray = new Tray(iconPath);
    const contextMenu = Menu.buildFromTemplate([
      { label: "Show", click: () => mainWindow?.show() },
      { label: "Quit", click: () => app.quit() },
    ]);
    tray.setToolTip("IndestructibleEco");
    tray.setContextMenu(contextMenu);
  } catch {
    // Tray icon not available in CI/headless — skip silently
  }
}

// ── Auto-Updater Events ─────────────────────────────────────
autoUpdater.on("update-available", () => {
  mainWindow?.webContents.send("update:available");
});

autoUpdater.on("update-downloaded", () => {
  mainWindow?.webContents.send("update:downloaded");
});

// ── App Lifecycle ───────────────────────────────────────────
app.whenReady().then(() => {
  createWindow();
  createTray();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});