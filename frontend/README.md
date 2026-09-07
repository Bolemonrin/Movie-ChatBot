# frontend

The React interface for [Movie ChatBot](../README.md). Setup and run
instructions live in the root README — this file covers only what is specific
to working inside this directory.

React 19 · Vite 8 · Tailwind 4 · Headless UI · zustand

```
src/
├── App.tsx                    layout shell: header + main
├── main.tsx                   react root
├── index.css                  the global reset, inside @layer base (see below)
├── vars.css                   design tokens — colours, radii, fonts, spacing
├── lib/
│   ├── store.ts               zustand: messages, threadId, sendMessage
│   └── cn.ts                  clsx + tailwind-merge
└── components/
    ├── Header/                title bar and the model dropdown
    └── Body/                  message list, bubbles, input box
```

## Two traps worth knowing

Both of these fail **silently** — no error, no warning, just the wrong result.

**1. Global CSS must live inside `@layer base`.**

Tailwind 4 emits its utilities into a `utilities` cascade layer, and the CSS
spec says unlayered styles beat layered ones regardless of specificity. So an
unlayered `* { margin: 0; padding: 0 }` in `index.css` silently kills every
`px-*`, `py-*`, `m-*` and `mx-auto` in the app. The reset is wrapped in
`@layer base` for exactly this reason — keep it there.

**2. Tailwind defines some of the same CSS variable names you do.**

`vars.css` sets `--radius-bubble`, `--radius-sm` and `--radius-pill`. Tailwind
ships its own `--radius-md`, `--radius-lg` and friends. Writing
`rounded-[var(--radius-md)]` resolves to Tailwind's 6px instead of failing, so
a typo in a token name looks like it works. Check the name exists in `vars.css`
before using it.

## Talking to the backend

`lib/store.ts` posts to a relative `/api/chat` with `{thread_id, content}` and
expects `{content}` back. The `thread_id` is generated once per browser session
and is what gives the agent its memory — it maps to langgraph's
`configurable.thread_id`.

`vite.config.ts` proxies `/api` to `http://localhost:8000` in development. The
relative URL means the same code works unchanged when FastAPI serves the built
files directly.
