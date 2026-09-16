// import SidePanel from './SidePanel'
import Chatbot from './Chatbot'
import MessageBox from './MessageBox'

const Main = () => {
  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-row px-4 py-6 sm:px-6 gap-4">
      {/* <SidePanel /> */}
      <div className="flex flex-1 flex-col gap-4">
        <div className="flex flex-1 flex-col rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
          <Chatbot />
        </div>
        <MessageBox />
      </div>
    </main>
  )
}

export default Main
