const { contextBridge, ipcRenderer } = require('electron');

const API_BASE_ARG = '--api-base=';
const apiBaseArg = process.argv.find((arg) => arg.startsWith(API_BASE_ARG));

contextBridge.exposeInMainWorld('backend', {
  apiBase: apiBaseArg ? apiBaseArg.slice(API_BASE_ARG.length) : null,
});

contextBridge.exposeInMainWorld('overlay', {
  update: (result) => ipcRenderer.send('overlay:update', result),
  close: () => ipcRenderer.send('overlay:close'),
  onResult: (callback) => ipcRenderer.on('overlay:result', (_event, result) => callback(result)),
});
