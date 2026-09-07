import { create } from 'zustand'

interface Message {
  id: string
  role: 'user' | 'ai'
  content: string
}

interface ChatStore {
  threadId: string
  addMessage: (role: 'user' | 'ai', content: string) => void
  messages: Message[]
}

export const useChatStore = create<ChatStore>()((set) => ({
  threadId: crypto.randomUUID(),
  messages: [],
  addMessage: (role, content) =>
    set((state) => ({
      messages: [...state.messages, { id: crypto.randomUUID(), role, content }],
    })),
}))
