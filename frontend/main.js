// ~/neura-os/frontend/main.js

const { app, BrowserWindow, globalShortcut, systemPreferences, ipcMain, shell } = require('electron');
const { exec } = require('child_process'); // For launching apps
const fs = require('fs');                 // For checking if apps are installed
const os = require('os');                 // For real RAM stats
const path = require('path');

async function askForPermissions() {
  try {
    const micPermission = await systemPreferences.askForMediaAccess('microphone');
    console.log(`Microphone access granted: ${micPermission}`);
    
    if (!micPermission) {
        console.error("FATAL: Microphone permission was not granted. Voice commands will fail.");
    }
    return micPermission;

  } catch (e) {
    console.error("Error asking for media access:", e);
    return false;
  }
}

async function createWindow() {
  // --- ASK FOR PERMISSION ON STARTUP ---
  await askForPermissions();

  const win = new BrowserWindow({
    width: 1600,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false,
      webviewTag: true 
    },
    title: "Neura OS"
  });

  // --- [MOVED HERE] HANDLE THE ACTUAL DOWNLOAD PROCESS ---
  // This must be inside createWindow to have access to 'win'
  win.webContents.session.on('will-download', (event, item, webContents) => {
    // We'll just save it to the User's Downloads folder
    const downloadPath = path.join(app.getPath('downloads'), item.getFilename());
    item.setSavePath(downloadPath);
    console.log(`Saving download to: ${downloadPath}`);

    item.on('done', (event, state) => {
      if (state === 'completed') {
        console.log('Download complete!');
        // 4. Automatically open the installer (.dmg file)!
        shell.openPath(downloadPath); 
        
        // 5. Tell the frontend the download is done
        // --- [FIXED SYNTAX ERROR] ---
        win.webContents.send('app-download-complete', { 
            success: true, 
            filename: item.getFilename() 
        });
      } else {
        console.log(`Download failed: ${state}`);
      }
    });
  });
  // --- END DOWNLOAD HANDLER ---


  win.loadFile('index.html');
  win.webContents.openDevTools(); 
  
  // --- WAKE WORD SHORTCUT ---
  globalShortcut.register('CommandOrControl+N', () => {
    console.log('Shortcut Registered! Sending "start-listening" to window.');
    win.webContents.send('start-listening');
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  globalShortcut.unregisterAll();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
});

// --- LISTENER FOR SYSTEM STATS ---
ipcMain.handle('get-system-stats', async () => {
  const totalMem = os.totalmem(); // Total RAM in bytes
  const freeMem = os.freemem();   // Free RAM in bytes
  const usedMem = totalMem - freeMem;
  return {
    cpu: os.cpus()[0].model, // Get CPU model
    totalMem: (totalMem / 1024 / 1024 / 1024).toFixed(1), // Convert to GB
    usedMem: (usedMem / 1024 / 1024 / 1024).toFixed(1),   // Convert to GB
    usedMemPercent: (usedMem / totalMem) * 100
  };
});

// --- LISTENER FOR APP STORE ---
ipcMain.handle('app-install', async (event, appToInstall) => {
  console.log(`Received install request for: ${appToInstall.name}`);
  
  const downloadUrl = appToInstall.download_url_macos; 
  if (!downloadUrl) {
    return { success: false, message: 'No download link for this OS.' };
  }
  
  // Need to find the window to start the download
  const win = BrowserWindow.getFocusedWindow();
  if (win) {
    win.webContents.downloadURL(downloadUrl);
    return { success: true, message: 'Download started...' };
  }
  
  return { success: false, message: 'Could not find window to start download.' };
});

ipcMain.handle('app-launch', async (event, appToLaunch) => {
  const launchPath = appToLaunch.launch_path_macos; 
  
  if (fs.existsSync(launchPath)) {
    exec(`open "${launchPath}"`, (err) => {
      if (err) return { success: false, message: 'Failed to launch app.' };
    });
    return { success: true, message: 'App is launching!' };
  } else {
    console.warn(`Launch failed: App not found at ${launchPath}`);
    return { success: false, message: `App not found at ${launchPath}. Have you installed it?` };
  }
});
// ... (at the end of the file)

// --- [NEW] REAL FILE SYSTEM HANDLERS ---
const userHomeDir = os.homedir(); // Gets your /Users/astrodingra directory

// Handler to read a directory
ipcMain.handle('browse-directory', async (event, subPath) => {
  const requestedPath = path.join(userHomeDir, subPath);

  // SECURITY CHECK: Don't allow browsing outside the home directory
  if (!requestedPath.startsWith(userHomeDir)) {
    return { success: false, error: 'Access Denied.' };
  }

  try {
    const items = await fs.promises.readdir(requestedPath, { withFileTypes: true });
    
    // Convert the items to a simple list
    const files = items
      .filter(item => !item.name.startsWith('.')) // Filter out hidden files
      .map(item => ({
        name: item.name,
        type: item.isDirectory() ? 'folder' : 'file'
      }));
      
    return { success: true, files: files };
  } catch (err) {
    return { success: false, error: err.message };
  }
});

// Handler to create a new folder
ipcMain.handle('create-folder', async (event, folderPath) => {
  const newPath = path.join(userHomeDir, folderPath);
  
  if (!newPath.startsWith(userHomeDir)) {
    return { success: false, error: 'Access Denied.' };
  }
  
  try {
    await fs.promises.mkdir(newPath);
    return { success: true };
  } catch (err) {
    return { success: false, error: err.message };
  }
});

// Handler for the "BIN" - it moves items to the system trash
ipcMain.handle('delete-item', async (event, itemPath) => {
  const fullPath = path.join(userHomeDir, itemPath);

  if (!fullPath.startsWith(userHomeDir)) {
    return { success: false, error: 'Access Denied.' };
  }

  try {
    await shell.trashItem(fullPath); // <-- THIS IS THE "BIN"
    return { success: true };
  } catch (err) {
    return { success: false, error: err.message };
  }
});
// ... (at the end of your main.js)

// --- [NEW] BROWSER CONTROLS ---
// Helper to get the browser <webview>
function getBrowserView(win) {
    if (!win) return null;
    // This is a bit of a hack, but it's the simplest way
    // We tell the renderer to find the webview and give us its ID
    return win.webContents; 
}

ipcMain.handle('open-file', async (event, itemPath) => {
  const fullPath = path.join(userHomeDir, itemPath);

  if (!fullPath.startsWith(userHomeDir)) {
    return { success: false, error: 'Access Denied.' };
  }

  try {
    // This tells your Mac to open the file with its default app
    await shell.openPath(fullPath); 
    return { success: true };
  } catch (err) {
    return { success: false, error: err.message };
  }
});
ipcMain.handle('check-app-installed', async (event, appPath) => {
  return fs.existsSync(appPath);
});