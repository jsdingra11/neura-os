const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // --- Voice Command API ---
  onStartListening: (callback) => ipcRenderer.on('start-listening', (event, ...args) => callback(...args)),

  // --- REAL System Monitor API ---
  getSystemStats: () => ipcRenderer.invoke('get-system-stats'),

  // --- REAL App Store API ---
 installApp: (appManifest) => ipcRenderer.invoke('app-install', appManifest),
  launchApp: (appManifest) => ipcRenderer.invoke('app-launch', appManifest),
  onDownloadComplete: (callback) => ipcRenderer.on('app-download-complete', (event, value) => callback(value)),
  checkAppInstalled: (appPath) => ipcRenderer.invoke('check-app-installed', appPath), // <-- ADD THIS
  
  // --- REAL File System API ---
  browseDirectory: (subPath) => ipcRenderer.invoke('browse-directory', subPath),
  createFolder: (folderPath) => ipcRenderer.invoke('create-folder', folderPath),
  deleteItem: (itemPath) => ipcRenderer.invoke('delete-item', itemPath),
  openFile: (itemPath) => ipcRenderer.invoke('open-file', itemPath)
});