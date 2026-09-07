import { cn } from '../../lib/cn'

interface MessageBubbleProps {
  role: 'user' | 'ai'
  content: string
  isPending?: boolean
}

const MessageBubble = ({ role, content, isPending }: MessageBubbleProps) => {
  return (
    <div
      className={cn(
        'max-w-[75%] rounded-[var(--radius-bubble)] px-3 py-2 text-sm',
        role === 'user' && 'self-end bg-[var(--color-primary)] text-white',
        role === 'ai' && 'self-start bg-[var(--color-surface-raised)] text-[var(--color-text)]',
        isPending && 'opacity-60',
      )}
    >
      {/* message content */}
      {content}
    </div>
  )
}

export default MessageBubble
