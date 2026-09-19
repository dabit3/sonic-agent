const { contextBridge, ipcRenderer, webUtils } = require('electron')

contextBridge.exposeInMainWorld('sonicDesktop', {
  getConnection: profile => ipcRenderer.invoke('sonic:connection', profile),
  revalidateConnection: () => ipcRenderer.invoke('sonic:connection:revalidate'),
  touchBackend: profile => ipcRenderer.invoke('sonic:backend:touch', profile),
  getGatewayWsUrl: profile => ipcRenderer.invoke('sonic:gateway:ws-url', profile),
  openSessionWindow: (sessionId, opts) => ipcRenderer.invoke('sonic:window:openSession', sessionId, opts),
  openNewSessionWindow: () => ipcRenderer.invoke('sonic:window:openNewSession'),
  petOverlay: {
    // Main renderer → main process: window lifecycle + drag. `request` is
    // `{ bounds, screen }`; resolves with the screen bounds it actually used.
    open: request => ipcRenderer.invoke('sonic:pet-overlay:open', request),
    close: () => ipcRenderer.invoke('sonic:pet-overlay:close'),
    setBounds: bounds => ipcRenderer.send('sonic:pet-overlay:set-bounds', bounds),
    setIgnoreMouse: ignore => ipcRenderer.send('sonic:pet-overlay:ignore-mouse', ignore),
    // Flip the overlay focusable (and focus it) while the composer needs keys.
    setFocusable: focusable => ipcRenderer.send('sonic:pet-overlay:set-focusable', focusable),
    // Main renderer → overlay (forwarded by main): push the latest pet state.
    pushState: payload => ipcRenderer.send('sonic:pet-overlay:state', payload),
    // Overlay → main renderer (forwarded by main): pop back in / composer submit.
    control: payload => ipcRenderer.send('sonic:pet-overlay:control', payload),
    // Overlay subscribes to state pushes.
    onState: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('sonic:pet-overlay:state', listener)
      return () => ipcRenderer.removeListener('sonic:pet-overlay:state', listener)
    },
    // Main renderer subscribes to overlay control messages.
    onControl: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('sonic:pet-overlay:control', listener)
      return () => ipcRenderer.removeListener('sonic:pet-overlay:control', listener)
    }
  },
  getBootProgress: () => ipcRenderer.invoke('sonic:boot-progress:get'),
  getConnectionConfig: profile => ipcRenderer.invoke('sonic:connection-config:get', profile),
  saveConnectionConfig: payload => ipcRenderer.invoke('sonic:connection-config:save', payload),
  applyConnectionConfig: payload => ipcRenderer.invoke('sonic:connection-config:apply', payload),
  testConnectionConfig: payload => ipcRenderer.invoke('sonic:connection-config:test', payload),
  probeConnectionConfig: remoteUrl => ipcRenderer.invoke('sonic:connection-config:probe', remoteUrl),
  oauthLoginConnectionConfig: remoteUrl => ipcRenderer.invoke('sonic:connection-config:oauth-login', remoteUrl),
  oauthLogoutConnectionConfig: remoteUrl => ipcRenderer.invoke('sonic:connection-config:oauth-logout', remoteUrl),
  profile: {
    get: () => ipcRenderer.invoke('sonic:profile:get'),
    set: name => ipcRenderer.invoke('sonic:profile:set', name)
  },
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
  setNativeTheme: mode => ipcRenderer.send('sonic:native-theme', mode),
  setTranslucency: payload => ipcRenderer.send('sonic:translucency', payload),
  setPreviewShortcutActive: active => ipcRenderer.send('sonic:previewShortcutActive', Boolean(active)),
  openExternal: url => ipcRenderer.invoke('sonic:openExternal', url),
  openPreviewInBrowser: url => ipcRenderer.invoke('sonic:openPreviewInBrowser', url),
  fetchLinkTitle: url => ipcRenderer.invoke('sonic:fetchLinkTitle', url),
  sanitizeWorkspaceCwd: cwd => ipcRenderer.invoke('sonic:workspace:sanitize', cwd),
  settings: {
    getDefaultProjectDir: () => ipcRenderer.invoke('sonic:setting:defaultProjectDir:get'),
    setDefaultProjectDir: dir => ipcRenderer.invoke('sonic:setting:defaultProjectDir:set', dir),
    pickDefaultProjectDir: () => ipcRenderer.invoke('sonic:setting:defaultProjectDir:pick')
  },
  revealLogs: () => ipcRenderer.invoke('sonic:logs:reveal'),
  getRecentLogs: () => ipcRenderer.invoke('sonic:logs:recent'),
  readDir: dirPath => ipcRenderer.invoke('sonic:fs:readDir', dirPath),
  gitRoot: startPath => ipcRenderer.invoke('sonic:fs:gitRoot', startPath),
  revealPath: targetPath => ipcRenderer.invoke('sonic:fs:reveal', targetPath),
  renamePath: (targetPath, newName) => ipcRenderer.invoke('sonic:fs:rename', targetPath, newName),
  writeTextFile: (filePath, content) => ipcRenderer.invoke('sonic:fs:writeText', filePath, content),
  trashPath: targetPath => ipcRenderer.invoke('sonic:fs:trash', targetPath),
  git: {
    worktreeList: repoPath => ipcRenderer.invoke('sonic:git:worktreeList', repoPath),
    worktreeAdd: (repoPath, options) => ipcRenderer.invoke('sonic:git:worktreeAdd', repoPath, options),
    worktreeRemove: (repoPath, worktreePath, options) =>
      ipcRenderer.invoke('sonic:git:worktreeRemove', repoPath, worktreePath, options),
    branchSwitch: (repoPath, branch) => ipcRenderer.invoke('sonic:git:branchSwitch', repoPath, branch),
    branchList: repoPath => ipcRenderer.invoke('sonic:git:branchList', repoPath),
    repoStatus: repoPath => ipcRenderer.invoke('sonic:git:repoStatus', repoPath),
    fileDiff: (repoPath, filePath) => ipcRenderer.invoke('sonic:git:fileDiff', repoPath, filePath),
    scanRepos: (roots, options) => ipcRenderer.invoke('sonic:git:scanRepos', roots, options),
    review: {
      list: (repoPath, scope, baseRef) => ipcRenderer.invoke('sonic:git:review:list', repoPath, scope, baseRef),
      diff: (repoPath, filePath, scope, baseRef, staged) =>
        ipcRenderer.invoke('sonic:git:review:diff', repoPath, filePath, scope, baseRef, staged),
      stage: (repoPath, filePath) => ipcRenderer.invoke('sonic:git:review:stage', repoPath, filePath),
      unstage: (repoPath, filePath) => ipcRenderer.invoke('sonic:git:review:unstage', repoPath, filePath),
      revert: (repoPath, filePath) => ipcRenderer.invoke('sonic:git:review:revert', repoPath, filePath),
      revParse: (repoPath, ref) => ipcRenderer.invoke('sonic:git:review:revParse', repoPath, ref),
      commit: (repoPath, message, push) => ipcRenderer.invoke('sonic:git:review:commit', repoPath, message, push),
      commitContext: repoPath => ipcRenderer.invoke('sonic:git:review:commitContext', repoPath),
      push: repoPath => ipcRenderer.invoke('sonic:git:review:push', repoPath),
      shipInfo: repoPath => ipcRenderer.invoke('sonic:git:review:shipInfo', repoPath),
      createPr: repoPath => ipcRenderer.invoke('sonic:git:review:createPr', repoPath)
    }
  },
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
  onDeepLink: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('sonic:deep-link', listener)
    return () => ipcRenderer.removeListener('sonic:deep-link', listener)
  },
  signalDeepLinkReady: () => ipcRenderer.invoke('sonic:deep-link-ready'),
  onWindowStateChanged: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('sonic:window-state-changed', listener)
    return () => ipcRenderer.removeListener('sonic:window-state-changed', listener)
  },
  onFocusSession: callback => {
    const listener = (_event, sessionId) => callback(sessionId)
    ipcRenderer.on('sonic:focus-session', listener)
    return () => ipcRenderer.removeListener('sonic:focus-session', listener)
  },
  onNotificationAction: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('sonic:notification-action', listener)
    return () => ipcRenderer.removeListener('sonic:notification-action', listener)
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
  getRemoteDisplayReason: () => ipcRenderer.invoke('sonic:get-remote-display-reason'),
  uninstall: {
    summary: () => ipcRenderer.invoke('sonic:uninstall:summary'),
    run: mode => ipcRenderer.invoke('sonic:uninstall:run', { mode })
  },
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
  },
  themes: {
    fetchMarketplace: id => ipcRenderer.invoke('sonic:vscode-theme:fetch', id),
    searchMarketplace: query => ipcRenderer.invoke('sonic:vscode-theme:search', query)
  }
})
