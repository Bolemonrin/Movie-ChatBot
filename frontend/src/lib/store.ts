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
  addMessage: (role: 'user' | 'ai', content: string) => void
  sendMessage: (content: string) => Promise<void>
}

export const useChatStore = create<ChatStore>()((set, get) => ({
  // One thread per browser session. The backend passes this to langgraph as
  // configurable.thread_id, which is what makes the agent remember the turn.
  threadId: crypto.randomUUID(),
  messages: [],
  isStreaming: false,
  error: null,

  addMessage: (role, content) =>
    set((state) => ({
      messages: [...state.messages, { id: crypto.randomUUID(), role, content }],
    })),

  // Takes only the text: the user role is implied, and the 'ai' reply role is
  // decided by the response below.
  sendMessage: async (content) => {
    const text = content.trim()
    // Guard here as well as in the UI, so a second Enter mid-request cannot
    // start an overlapping run whose reply could land out of order.
    if (!text || get().isStreaming) return

    const { threadId, addMessage } = get()
    addMessage('user', text)
    set({ isStreaming: true, error: null })

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

      const data: unknown = await response.json()
      if (
        typeof data !== 'object' ||
        data === null ||
        !('content' in data) ||
        typeof data.content !== 'string'
      ) {
        throw new Error('Invalid response from server')
      }

      addMessage('ai', data.content)
    } catch (err) {
      // Never rethrow: nothing above this can catch it, and an unhandled
      // rejection would leave the user staring at their own message forever.
      set({ error: err instanceof Error ? err.message : 'Something went wrong' })
    } finally {
      set({ isStreaming: false })
    }
  },
}))
