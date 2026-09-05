import { cleanup, render } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { MarkdownTextContent } from './markdown-text'

vi.mock('@assistant-ui/react-streamdown', async () => {
  const { useMessagePartText } = await import('@assistant-ui/react')

  return {
    StreamdownTextPrimitive: () => {
      const { text, status } = useMessagePartText()

      return <div data-status={status.type} data-testid="markdown-output">{text}</div>
    }
  }
})

afterEach(() => {
  cleanup()
  vi.useRealTimers()
})

describe('streaming markdown latency', () => {
  it('publishes a full chunk without animation timers or a character backlog', () => {
    vi.useFakeTimers()
    const text = 'A burst of provider output. '.repeat(200)
    const view = render(<MarkdownTextContent isRunning text={text} />)
    expect(view.getByTestId('markdown-output').textContent).toBe(text)

    const extended = `${text}The next chunk.`
    view.rerender(<MarkdownTextContent isRunning text={extended} />)
    expect(view.getByTestId('markdown-output').textContent).toBe(extended)

    view.rerender(<MarkdownTextContent isRunning={false} text={extended} />)
    expect(view.getByTestId('markdown-output').dataset.status).toBe('complete')
  })

  it('replaces text on session changes without replaying old output', () => {
    vi.useFakeTimers()
    const view = render(<MarkdownTextContent isRunning text="First session" />)
    view.rerender(<MarkdownTextContent isRunning text="Replacement session" />)
    expect(view.getByTestId('markdown-output').textContent).toBe('Replacement session')
    view.rerender(<MarkdownTextContent isRunning={false} text="Restored history" />)
    expect(view.getByTestId('markdown-output').textContent).toBe('Restored history')
  })
})
