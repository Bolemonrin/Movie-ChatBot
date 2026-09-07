import { useState } from 'react'
import TextareaAutosize from 'react-textarea-autosize'

{
  /* custome modules */
}
import { useChatStore } from '../../lib/store'

const MessageBox = () => {
  const [value, setValue] = useState('')
  const addMessage = useChatStore((state) => state.addMessage)

  const handleSend = () => {
    if (!value.trim()) return
    addMessage('user', value)
    setValue('')
  }

  return (
    <div className="flex items-end gap-2 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface)] p-2">
      <TextareaAutosize
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Ask about a movie or show…"
        minRows={1}
        maxRows={6}
        className="flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none"
      />
      <button
        onClick={handleSend}
        type="button"
        disabled={!value.trim()}
        className="shrink-0 rounded-[var(--radius-pill)] bg-[var(--color-primary)] px-4 py-1.5 text-sm font-medium text-white disabled:opacity-40"
      >
        Send
      </button>
    </div>
  )
}

export default MessageBox
