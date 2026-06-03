const { contextBridge, ipcRenderer, webUtils } = require('electron')

contextBridge.exposeInMainWorld('sonicDesktop', {
  getConnection: () => ipcRenderer.invoke('sonic:connection'),
  getGatewayWsUrl: () => ipcRenderer.invoke('sonic:gateway:ws-url'),
  getBootProgress: () => ipcRenderer.invoke('sonic:boot-progress:get'),
  getConnectionConfig: () => ipcRenderer.invoke('sonic:connection-config:get'),
  saveConnectionConfig: payload => ipcRenderer.invoke('sonic:connection-config:save', payload),
  applyConnectionConfig: payload => ipcRenderer.invoke('sonic:connection-config:apply', payload),
  testConnectionConfig: payload => ipcRenderer.invoke('sonic:connection-config:test', payload),
  probeConnectionConfig: remoteUrl => ipcRenderer.invoke('sonic:connection-config:probe', remoteUrl),
  oauthLoginConnectionConfig: remoteUrl => ipcRenderer.invoke('sonic:connection-config:oauth-login', remoteUrl),
  oauthLogoutConnectionConfig: remoteUrl => ipcRenderer.invoke('sonic:connection-config:oauth-logout', remoteUrl),
  api: request => ipcRenderer.invoke('sonic:api', request),
  notify: payload => ipcRenderer.invoke('sonic:notify', payload),
  requestMicrophoneAccess: () => ipcRenderer.invoke('sonic:requestMicrophoneAccess'),
  readFileDataUrl: filePath => ipcRenderer.invoke('sonic:readFileDataUrl', filePath),
  readFileText: filePath => ipcRenderer.invoke('sonic:readFileText', filePath),
  selectPaths: options => ipcRenderer.invoke('sonic:selectPaths', options),
  writeClipboard: text => ipcRenderer.invoke('sonic:writeClipboard', text),
  saveImageFromUrl: url => ipcRenderer.invoke('sonic:saveImageFromUrl', url),
  saveImageBuffer: (data, ext) => ipcRenderer.invoke('sonic:saveImageBuffer', { data, ext }),
  saveClipboardImage: () => ipcRenderer.invoke('sonic:saveClipboardImage'),
  getPathForFile: file => {
    try {
      return webUtils.getPathForFile(file) || ''
    } catch {
      return ''
    }
  },
  normalizePreviewTarget: (target, baseDir) => ipcRenderer.invoke('sonic:normalizePreviewTarget', target, baseDir),
  watchPreviewFile: url => ipcRenderer.invoke('sonic:watchPreviewFile', url),
  stopPreviewFileWatch: id => ipcRenderer.invoke('sonic:stopPreviewFileWatch', id),
  setTitleBarTheme: payload => ipcRenderer.send('sonic:titlebar-theme', payload),
  setPreviewShortcutActive: active => ipcRenderer.send('sonic:previewShortcutActive', Boolean(active)),
  openExternal: url => ipcRenderer.invoke('sonic:openExternal', url),
  fetchLinkTitle: url => ipcRenderer.invoke('sonic:fetchLinkTitle', url),
  settings: {
    getDefaultProjectDir: () => ipcRenderer.invoke('sonic:setting:defaultProjectDir:get'),
    setDefaultProjectDir: dir => ipcRenderer.invoke('sonic:setting:defaultProjectDir:set', dir),
    pickDefaultProjectDir: () => ipcRenderer.invoke('sonic:setting:defaultProjectDir:pick')
  },
  revealLogs: () => ipcRenderer.invoke('sonic:logs:reveal'),
  getRecentLogs: () => ipcRenderer.invoke('sonic:logs:recent'),
  readDir: dirPath => ipcRenderer.invoke('sonic:fs:readDir', dirPath),
  gitRoot: startPath => ipcRenderer.invoke('sonic:fs:gitRoot', startPath),
  terminal: {
    dispose: id => ipcRenderer.invoke('sonic:terminal:dispose', id),
    resize: (id, size) => ipcRenderer.invoke('sonic:terminal:resize', id, size),
    start: options => ipcRenderer.invoke('sonic:terminal:start', options),
    write: (id, data) => ipcRenderer.invoke('sonic:terminal:write', id, data),
    onData: (id, callback) => {
      const channel = `sonic:terminal:${id}:data`
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on(channel, listener)
      return () => ipcRenderer.removeListener(channel, listener)
    },
    onExit: (id, callback) => {
      const channel = `sonic:terminal:${id}:exit`
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on(channel, listener)
      return () => ipcRenderer.removeListener(channel, listener)
    }
  },
  onClosePreviewRequested: callback => {
    const listener = () => callback()
    ipcRenderer.on('sonic:close-preview-requested', listener)
    return () => ipcRenderer.removeListener('sonic:close-preview-requested', listener)
  },
  onOpenUpdatesRequested: callback => {
    const listener = () => callback()
    ipcRenderer.on('sonic:open-updates', listener)
    return () => ipcRenderer.removeListener('sonic:open-updates', listener)
  },
  onWindowStateChanged: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('sonic:window-state-changed', listener)
    return () => ipcRenderer.removeListener('sonic:window-state-changed', listener)
  },
  onPreviewFileChanged: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('sonic:preview-file-changed', listener)
    return () => ipcRenderer.removeListener('sonic:preview-file-changed', listener)
  },
  onBackendExit: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('sonic:backend-exit', listener)
    return () => ipcRenderer.removeListener('sonic:backend-exit', listener)
  },
  onPowerResume: callback => {
    const listener = () => callback()
    ipcRenderer.on('sonic:power-resume', listener)
    return () => ipcRenderer.removeListener('sonic:power-resume', listener)
  },
  onBootProgress: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('sonic:boot-progress', listener)
    return () => ipcRenderer.removeListener('sonic:boot-progress', listener)
  },
  // First-launch bootstrap progress -- emitted by the install.ps1 stage
  // runner in main.cjs (apps/desktop/electron/bootstrap-runner.cjs).
  // Renderer's install overlay subscribes to live events and queries the
  // current snapshot via getBootstrapState() to recover after a devtools
  // reload mid-bootstrap.
  getBootstrapState: () => ipcRenderer.invoke('sonic:bootstrap:get'),
  resetBootstrap: () => ipcRenderer.invoke('sonic:bootstrap:reset'),
  repairBootstrap: () => ipcRenderer.invoke('sonic:bootstrap:repair'),
  cancelBootstrap: () => ipcRenderer.invoke('sonic:bootstrap:cancel'),
  onBootstrapEvent: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('sonic:bootstrap:event', listener)
    return () => ipcRenderer.removeListener('sonic:bootstrap:event', listener)
  },
  getVersion: () => ipcRenderer.invoke('sonic:version'),
  updates: {
    check: () => ipcRenderer.invoke('sonic:updates:check'),
    apply: opts => ipcRenderer.invoke('sonic:updates:apply', opts),
    getBranch: () => ipcRenderer.invoke('sonic:updates:branch:get'),
    setBranch: name => ipcRenderer.invoke('sonic:updates:branch:set', name),
    onProgress: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('sonic:updates:progress', listener)
      return () => ipcRenderer.removeListener('sonic:updates:progress', listener)
    }
  }
})
