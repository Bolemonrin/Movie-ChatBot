import { useState, type KeyboardEvent } from 'react'
import TextareaAutosize from 'react-textarea-autosize'

// custom modules
import { useChatStore } from '../../lib/store'

const MessageBox = () => {
  const [value, setValue] = useState('')
  const sendMessage = useChatStore((state) => state.sendMessage)
  const isStreaming = useChatStore((state) => state.isStreaming)
  const error = useChatStore((state) => state.error)

  const handleSend = () => {
    const text = value.trim()
    if (!text || isStreaming) return
    // Clear before firing: this used to sit after the await, so a failed
    // request left the text sitting in the box.
    setValue('')
    // The store owns the error handling, so nothing can reject up here.
    void sendMessage(text)
  }

  // On the textarea rather than on document: a global listener sent a message
  // whenever Enter was pressed anywhere, including while operating the header
  // dropdown. Shift+Enter stays free for newlines, since the box is multi-line.
  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col gap-1">
      {error && (
        <p role="alert" className="px-2 text-xs text-[var(--color-error)]">
          {error}
        </p>
      )}

      <div className="flex items-end gap-2 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface)] p-2">
        <TextareaAutosize
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about a movie or show…"
          minRows={1}
          maxRows={6}
          className="flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none"
        />
        <button
          onClick={handleSend}
          type="button"
          disabled={!value.trim() || isStreaming}
          className="shrink-0 rounded-[var(--radius-pill)] bg-[var(--color-primary)] px-4 py-1.5 text-sm font-medium text-white disabled:opacity-40"
        >
          {isStreaming ? 'Sending…' : 'Send'}
        </button>
      </div>
    </div>
  )
}

export default MessageBox
