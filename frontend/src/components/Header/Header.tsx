import Models from './Models'

const Header = () => {
  return (
    <header className="w-full shrink-0 border-b border-[var(--color-border)]">
      <div className="mx-auto flex w-full max-w-4xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <h1 className="font-[family-name:var(--font-display)] text-xl font-bold sm:text-2xl">
          Chatbot Title
        </h1>
        <Models />
      </div>
    </header>
  )
}

export default Header
