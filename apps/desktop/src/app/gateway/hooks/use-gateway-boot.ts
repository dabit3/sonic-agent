import { useEffect, useRef } from 'react'

import type { SonicConnection } from '@/global'
import { SonicGateway } from '@/sonic'
import {
  $desktopBoot,
  applyDesktopBootProgress,
  completeDesktopBoot,
  failDesktopBoot,
  setDesktopBootStep
} from '@/store/boot'
import { setGateway } from '@/store/gateway'
import { notify, notifyError } from '@/store/notifications'
import { $connection, setConnection, setGatewayState, setSessionsLoading } from '@/store/session'
import type { RpcEvent } from '@/types/sonic'

interface GatewayBootOptions {
  handleGatewayEvent: (event: RpcEvent) => void
  onConnectionReady: (
    connection: Awaited<ReturnType<NonNullable<typeof window.sonicDesktop>['getConnection']>> | null
  ) => void
  onGatewayReady: (gateway: SonicGateway | null) => void
  refreshSonicConfig: () => Promise<void>
  refreshSessions: () => Promise<void>
}

export function useGatewayBoot({
  handleGatewayEvent,
  onConnectionReady,
  onGatewayReady,
  refreshSonicConfig,
  refreshSessions
}: GatewayBootOptions) {
  const callbacksRef = useRef({
    handleGatewayEvent,
    onConnectionReady,
    onGatewayReady,
    refreshSonicConfig,
    refreshSessions
  })

  callbacksRef.current = {
    handleGatewayEvent,
    onConnectionReady,
    onGatewayReady,
    refreshSonicConfig,
    refreshSessions
  }

  useEffect(() => {
    let cancelled = false
    const desktop = window.sonicDesktop

    const publish = (next: SonicConnection | null) => {
      callbacksRef.current.onConnectionReady(next)
      setConnection(next)
    }

    if (!desktop) {
      failDesktopBoot('Desktop IPC bridge is unavailable.')
      setSessionsLoading(false)

      return () => void (cancelled = true)
    }

    const offBootProgress = desktop.onBootProgress(payload => applyDesktopBootProgress(payload))
    void desktop
      .getBootProgress()
      .then(snapshot => applyDesktopBootProgress(snapshot))
      .catch(() => undefined)

    setDesktopBootStep({
      phase: 'renderer.boot',
      message: 'Starting desktop connection',
      progress: 6
    })

    const gateway = new SonicGateway()
    callbacksRef.current.onGatewayReady(gateway)
    setGateway(gateway)

    const offState = gateway.onState(st => void setGatewayState(st))
    const offEvent = gateway.onEvent(event => callbacksRef.current.handleGatewayEvent(event))

    const offWindowState = desktop.onWindowStateChanged?.(payload => {
      const current = $connection.get()

      if (current) {
        publish({ ...current, ...payload })
      }
    })

    const offExit = desktop.onBackendExit(() => {
      if ($desktopBoot.get().running || $desktopBoot.get().visible) {
        failDesktopBoot('Sonic background process exited during startup.')
      }

      notify({
        kind: 'error',
        title: 'Backend stopped',
        message: 'Sonic background process exited.',
        durationMs: 0
      })
    })

    async function boot() {
      try {
        const conn = await desktop.getConnection()

        if (cancelled) {
          return
        }

        setDesktopBootStep({
          phase: 'renderer.gateway.connect',
          message: 'Connecting live desktop gateway',
          progress: 95
        })
        publish(conn)
        await gateway.connect(conn.wsUrl)

        if (cancelled) {
          return
        }

        setDesktopBootStep({
          phase: 'renderer.config',
          message: 'Loading Sonic settings',
          progress: 97
        })
        await callbacksRef.current.refreshSonicConfig()

        if (cancelled) {
          return
        }

        setDesktopBootStep({
          phase: 'renderer.sessions',
          message: 'Loading recent sessions',
          progress: 99
        })
        await callbacksRef.current.refreshSessions()
        completeDesktopBoot()
      } catch (err) {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : String(err)
          failDesktopBoot(message)
          notifyError(err, 'Desktop boot failed')
          setSessionsLoading(false)
        }
      }
    }

    void boot()

    return () => {
      cancelled = true
      offState()
      offEvent()
      offExit()
      offWindowState?.()
      offBootProgress()
      gateway.close()
      publish(null)
      callbacksRef.current.onGatewayReady(null)
      setGateway(null)
    }
  }, [])
}
