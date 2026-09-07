import MessageBubble from './MessageBubble'
import { useChatStore } from '../../lib/store'

const Chatbot = () => {
  const messages = useChatStore((state) => state.messages)
  return (
    <div className="flex flex-1 flex-col gap-2 overflow-y-auto">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} role={msg.role} content={msg.content} />
      ))}
      {/* <div>Chatbot</div> */}
    </div>
  )
}

export default Chatbot
