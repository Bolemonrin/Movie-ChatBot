# 🎬 Movie ChatBot — AI Media Discovery Agent

A conversational movie & TV recommendation agent built with **LangGraph** and **LangChain tool-calling**. Ask it anything about movies or shows in plain English — it autonomously decides which tools to call, queries **TMDB (The Movie Database)** in real time, and remembers context across the conversation.

> **"Find me the plot of Inception."** → *"Who starred in it?"* → *"Suggest something similar."*
> The agent resolves "it" from conversation memory — no need to repeat yourself.

<!-- TODO: Add demo GIF here — record a terminal (or React) session showing a multi-turn conversation -->
<!-- ![Demo](assets/demo.gif) -->

---

## Features

- **Agentic tool-calling** — the LLM decides when and which tools to invoke via a LangGraph state machine
- **Six TMDB tools** — search, plot summaries, cast, crew/directors, recommendations, and similar-title discovery
- **Multi-turn conversational memory** — LangGraph state + checkpointing tracks the last title, cast, and crew discussed, so follow-up questions ("who directed it?") resolve automatically
- **Dual model support** — runs on local models via **Ollama** (Qwen 2.5) or hosted models via the **OpenAI API**
- **Real-time data** — all answers come from live TMDB API calls, not stale training data

---

## How It Works

```
User query
    ↓
llm_call ──(no tool needed)──→ reply
    ↓ (tool call requested)
tool_node → executes TMDB tool(s)
    ↓
update_context → persists media name/type, cast, crew to state
    ↓
back to llm_call (loop until final answer)
```

Built as a **StateGraph** with conditional edges: the model loops between reasoning and tool execution until it has what it needs, with an `InMemorySaver` checkpointer preserving conversation state per thread.

---

## Tech Stack

- **Python 3.12+**
- **LangGraph** — agent orchestration, state, checkpointing
- **LangChain** — tool definitions and model bindings
- **Ollama** (Qwen 2.5) / **OpenAI API** — interchangeable LLM backends
- **TMDB API** — live movie/TV data

---

## Setup

### Prerequisites
- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- A free [TMDB API token](https://www.themoviedb.org/settings/api)
- (Optional) [Ollama](https://ollama.com) with `qwen2.5` pulled, for local inference
- (Optional) [Node.js](https://nodejs.org) 20+, only for the React interface

### Install

One sync at the repo root sets up every interface. Pick the torch build that
matches your machine — the two extras are mutually exclusive:

```bash
git clone https://github.com/Bolemonrin/Movie-ChatBot.git
cd Movie-ChatBot
uv sync --extra cpu      # or: uv sync --extra cu130   (NVIDIA CUDA 13.0)
```

That creates one `.venv` at the root covering both workspace members. Run it
from the repo root; `uv` finds the workspace from any subdirectory.

### Configure

Create a `.env` file (never commit this):

```
TMDB_ACCESS_TOKEN=your_tmdb_token_here
OPENAI_API_KEY=your_key_here   # only if using OpenAI models
```

### Run

There are two ways in. Both talk to the same agent and share the same
conversation database, and every command works from anywhere in the repo.

**Terminal chat**

```bash
uv run movie-chatbot
```

```
User: recommend shows like Breaking Bad
AI: Since you liked the dark tone of Breaking Bad, here are similar crime dramas...
```

**React web UI** — *in progress.* The interface is built; the FastAPI layer
that connects it to the agent is not, so this currently renders the UI without
answers. Needs Node.js.

```bash
uv run movie-chatbot-web
```

It installs `frontend/node_modules` on first run if missing, so there is no
separate `npm install` step.

Once the API layer lands, this becomes a single process: `npm run build` emits
static files into `frontend/dist`, FastAPI serves them alongside `/api` on one
port, and no separate dev server or proxy is involved. Editing the frontend will
still use vite's dev server for hot reload, but running the app will not.

---

## Project Structure

A [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/): two
Python projects sharing one lockfile and one virtualenv, so a single `uv sync`
sets up every interface and no two of them can drift onto different versions.

```
├── pyproject.toml              # workspace root — declares members, pins the torch indexes
├── uv.lock                     # one lockfile for the whole repo
│
├── agent/                      # the agent, and the terminal front end
│   ├── main.py                 #   entrypoint: terminal chat
│   ├── chatbot.db              #   sqlite checkpointer — the conversation memory
│   │
│   └── movie_chatbot/          # the application, one layer per directory
│       ├── agent/              #   the LangGraph agent
│       │   ├── prompt.py       #     the system prompt (prose only)
│       │   ├── state.py        #     MediaQuery — what the graph carries between nodes
│       │   ├── model.py        #     LLM backend + tool bindings (swap providers here)
│       │   ├── nodes.py        #     llm_call, tool_node, update_context, should_continue
│       │   └── graph.py        #     how the nodes are wired; the compiled media_agent
│       │
│       ├── tools/              #   the @tool functions the LLM may call
│       │   ├── search.py       #     find_media
│       │   ├── summary.py      #     get_media_summary
│       │   ├── discovery.py    #     get_media_recommendations, get_similar_media
│       │   ├── credits.py      #     get_cast, get_crew
│       │   └── __init__.py     #     ALL_TOOLS — the list the agent binds
│       │
│       ├── cli.py              #   terminal chat loop
│       ├── rendering.py        #   pure string helpers (thinking blocks, poster links)
│       │
│       ├── media_lookup.py     #   title -> TMDB id (used by every tool; not a tool)
│       ├── summarizer.py       #   shortening plot overviews (not a tool)
│       ├── formatters.py       #   rendering a TMDB result as a tool-output line
│       └── tmdb_client.py      #   raw TMDB HTTP — the only module that touches the network
│
├── api/                        # FastAPI transport layer over the agent
│   └── movie_api/
│       └── dev.py              #   the movie-chatbot-web launcher
│
├── frontend/                   # React + Vite + Tailwind interface, talks to api/
│
├── agent/tests/                # pytest suite; all network calls mocked
└── agent/experiments/          # scratch and superseded code, imported by nothing
```

Each layer only reaches downwards: LLM knowledge stops at `agent/`, network
knowledge stops at `tmdb_client.py`. Anything that isn't itself a tool lives
outside `tools/`, so opening a tool module shows you tools and nothing else.

`api` depends on `agent` as a workspace member, which uv installs editable — so
edits to the agent are live in the API with no reinstall.

---

## Development

The commands above are for *running* the project. If you are changing it:

**Frontend, with hot reload.** Vite's dev server transforms and pushes changes
to the browser in milliseconds, which is worth having when you are iterating on
a component. It serves on http://localhost:5173 and proxies `/api` through to
the FastAPI server on `:8000`, so the browser only ever sees one origin and CORS
never comes up.

```bash
uv run movie-chatbot-web
```

Today this is the only way to run the React UI. Once the API layer lands the
default becomes a single built process, and this stays as the development path
— vite's dev server is for editing the frontend, not for running the app.

**Tests.** All network calls are mocked, so the suite needs no TMDB token.

```bash
uv run pytest
```

**Frontend lint and format.** A husky pre-commit hook runs `eslint --fix` and
`prettier --write` over staged files, so formatting is handled on commit. To run
it by hand:

```bash
npm --prefix frontend run lint
```

**Two things that will surprise you in `frontend/`** are documented in
[frontend/README.md](frontend/README.md) — both are silent failures rather than
errors.

---

## Roadmap

- [x] Gradio web UI (replaced by the React interface)
- [ ] React web UI (in progress — frontend built, FastAPI layer pending)
- [ ] Genre classification for mood-based discovery
- [ ] Streaming responses

## License

MIT
