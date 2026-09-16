import { create } from 'zustand'

interface Message {
  id: string
  role: 'user' | 'ai'
  content: string
}

interface ChatStore {
  threadId: string
  messages: Message[]
  isStreaming: boolean
  error: string | null
  /** Transient label while a node runs, e.g. while tools are executing. */
  status: string | null
  addMessage: (role: 'user' | 'ai', content: string) => void
  appendToLast: (chunk: string) => void
  sendMessage: (content: string) => Promise<void>
}

/** One server-sent event, as emitted by api/movie_api/agent_client.py. */
type AgentEvent = { type: 'token'; content: string } | { type: 'tool_call'; node: string }

function parseEvent(payload: string): AgentEvent | null {
  try {
    const data: unknown = JSON.parse(payload)
    if (typeof data !== 'object' || data === null || !('type' in data)) return null
    const { type } = data
    if (type === 'token' && 'content' in data && typeof data.content === 'string') {
      return { type: 'token', content: data.content }
    }
    if (type === 'tool_call' && 'node' in data && typeof data.node === 'string') {
      return { type: 'tool_call', node: data.node }
    }
    // An event shape we do not know about yet is skipped rather than thrown on,
    // so adding a new one on the server cannot break an older client.
    return null
  } catch {
    return null
  }
}

export const useChatStore = create<ChatStore>()((set, get) => ({
  // One thread per browser session. The backend passes this to langgraph as
  // configurable.thread_id, which is what makes the agent remember the turn.
  threadId: crypto.randomUUID(),
  messages: [],
  isStreaming: false,
  error: null,
  status: null,

  addMessage: (role, content) =>
    set((state) => ({
      messages: [...state.messages, { id: crypto.randomUUID(), role, content }],
    })),

  // Streamed text arrives in fragments, so the reply is grown in place rather
  // than pushed as a new message per token.
  appendToLast: (chunk) =>
    set((state) => {
      const last = state.messages.at(-1)
      if (!last) return state
      return {
        messages: [...state.messages.slice(0, -1), { ...last, content: last.content + chunk }],
      }
    }),

  // Takes only the text: the user role is implied, and the reply is always 'ai'.
  sendMessage: async (content) => {
    const text = content.trim()
    // Guard here as well as in the UI, so a second Enter mid-request cannot
    // start an overlapping run whose reply could land out of order.
    if (!text || get().isStreaming) return

    const { threadId, addMessage, appendToLast } = get()
    addMessage('user', text)
    set({ isStreaming: true, error: null, status: null })

    try {
      // Relative path: vite.config.ts proxies /api to the FastAPI server, so the
      // browser sees one origin and no CORS preflight. The same URL works in
      // production behind a reverse proxy.
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thread_id: threadId, content: text }),
      })

      if (!response.ok) throw new Error(`Server responded ${String(response.status)}`)
      if (!response.body) throw new Error('Server sent no response body')

      // The endpoint streams text/event-stream, so the body is read as it
      // arrives. EventSource cannot be used here: it only issues GETs and
      // cannot carry a JSON body.
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let started = false

      for (;;) {
        const { done, value } = await reader.read()
        if (done) break

        // stream: true keeps a multi-byte character split across two chunks
        // from being mangled.
        buffer += decoder.decode(value, { stream: true })

        // SSE frames end with a blank line. Whatever trails the last delimiter
        // is a partial frame, so it stays in the buffer for the next read --
        // network chunks do not respect frame boundaries.
        const frames = buffer.split('\n\n')
        buffer = frames.pop() ?? ''

        for (const frame of frames) {
          for (const line of frame.split('\n')) {
            if (!line.startsWith('data:')) continue
            const event = parseEvent(line.slice(5).trim())
            if (!event) continue

            if (event.type === 'token') {
              // The empty placeholder is only created once the first token
              // actually arrives, so a failed run leaves no stray bubble.
              if (!started) {
                addMessage('ai', '')
                started = true
                set({ status: null })
              }
              appendToLast(event.content)
            } else {
              set({ status: 'Running tools…' })
            }
          }
        }
      }

      if (!started) throw new Error('The agent returned no response')
    } catch (err) {
      // Never rethrow: nothing above this can catch it, and an unhandled
      // rejection would leave the user staring at their own message forever.
      set({ error: err instanceof Error ? err.message : 'Something went wrong' })
    } finally {
      set({ isStreaming: false, status: null })
    }
  },
}))
