import { atom } from 'nanostores'

import type { SonicGateway } from '@/sonic'

// The active gateway instance, exposed for inline message-stream components
// (e.g. inline ClarifyTool) that need to call gateway methods without having
// the instance threaded down through props from `ChatView`.
export const $gateway = atom<SonicGateway | null>(null)

export function setGateway(gateway: SonicGateway | null): void {
  if ($gateway.get() === gateway) {
    return
  }

  $gateway.set(gateway)
}
