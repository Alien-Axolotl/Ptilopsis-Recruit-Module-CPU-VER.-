const { app, BrowserWindow, ipcMain, screen } = require('electron');
const { spawn } = require('child_process');
const net = require('net');
const path = require('path');

const OVERLAY_WIDTH = 320;
const OVERLAY_HEIGHT = 130;

let apiBase = process.env.VITE_API_BASE;
let backendProcess = null;
let overlayWin = null;
let overlayResult = null;

function findFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      server.close(() => resolve(port));
    });
  });
}

async function startBackend() {
  const port = await findFreePort();
  const backendExe = path.join(process.resourcesPath, 'backend', 'backend.exe');

  backendProcess = spawn(backendExe, [String(port)], { windowsHide: true, stdio: 'ignore' });
  apiBase = `http://127.0.0.1:${port}`;

  for (let attempt = 0; attempt < 60; attempt += 1) {
    const response = await fetch(`${apiBase}/health`).catch(() => null);
    if (response?.ok) return;
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
}

function stopBackend() {
  if (!backendProcess) return;

  backendProcess.kill();
  backendProcess = null;
}

function createOverlay() {
  const { x, y, width } = screen.getPrimaryDisplay().workArea;

  const win = new BrowserWindow({
    x: x + width - OVERLAY_WIDTH,
    y,
    width: OVERLAY_WIDTH,
    height: OVERLAY_HEIGHT,
    show: false,
    frame: false,
    transparent: true,
    backgroundColor: '#00000000',
    hasShadow: false,
    resizable: false,
    movable: false,
    focusable: false,
    skipTaskbar: true,
    alwaysOnTop: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  win.setIgnoreMouseEvents(true);
  win.setAlwaysOnTop(true, 'screen-saver');
  win.setContentProtection(true);

  win.webContents.on('did-finish-load', () => {
    win.webContents.send('overlay:result', overlayResult);
    win.showInactive();
  });

  win.on('closed', () => {
    if (overlayWin === win) overlayWin = null;
  });

  win.loadFile(path.join(__dirname, 'overlay.html'));
  overlayWin = win;
}

function closeOverlay() {
  overlayResult = null;
  if (!overlayWin) return;

  const win = overlayWin;
  overlayWin = null;
  win.destroy();
}

function createWindow() {
  const win = new BrowserWindow({
    width: 600,
    height: 700,
    resizable: false,
    maximizable: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      additionalArguments: apiBase ? [`--api-base=${apiBase}`] : [],
    },
  });

  win.webContents.on('did-start-loading', closeOverlay);
  win.on('closed', closeOverlay);

  if (app.isPackaged) {
    win.loadFile(path.join(process.resourcesPath, 'frontend', 'index.html'));
  } else {
    win.loadURL(process.env.FRONTEND_URL || 'http://localhost:5173');
  }
}

ipcMain.on('overlay:update', (_event, result) => {
  overlayResult = result;

  if (!overlayWin) {
    createOverlay();
    return;
  }

  if (!overlayWin.webContents.isLoading()) {
    overlayWin.webContents.send('overlay:result', result);
    overlayWin.setAlwaysOnTop(true, 'screen-saver');
    overlayWin.moveTop();
  }
});

ipcMain.on('overlay:close', closeOverlay);

app.whenReady().then(async () => {
  if (app.isPackaged) await startBackend();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('will-quit', stopBackend);
