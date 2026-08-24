# 🎬 Movie ChatBot — AI Media Discovery Agent

A conversational movie & TV recommendation agent built with **LangGraph** and **LangChain tool-calling**. Ask it anything about movies or shows in plain English — it autonomously decides which tools to call, queries **TMDB (The Movie Database)** in real time, and remembers context across the conversation.

> **"Find me the plot of Inception."** → *"Who starred in it?"* → *"Suggest something similar."*
> The agent resolves "it" from conversation memory — no need to repeat yourself.

<!-- TODO: Add demo GIF here — record a terminal (or Gradio) session showing a multi-turn conversation -->
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

- **Python 3.11+**
- **LangGraph** — agent orchestration, state, checkpointing
- **LangChain** — tool definitions and model bindings
- **Ollama** (Qwen 2.5) / **OpenAI API** — interchangeable LLM backends
- **TMDB API** — live movie/TV data

---

## Setup

### Prerequisites
- Python 3.11+
- A free [TMDB API token](https://www.themoviedb.org/settings/api)
- (Optional) [Ollama](https://ollama.com) with `qwen2.5` pulled, for local inference

### Install

```bash
git clone https://github.com/Bolemonrin/Movie-ChatBot.git
cd Movie-ChatBot
uv sync            # or: pip install -e .
```

### Configure

Create a `.env` file (never commit this):

```
TMDB_ACCESS_TOKEN=your_tmdb_token_here
OPENAI_API_KEY=your_key_here   # only if using OpenAI models
```

### Run

```bash
uv run python main.py     # terminal chat
uv run python app.py      # Gradio web UI at http://localhost:7860
```

Then chat:

```
User: recommend shows like Breaking Bad
AI: Since you liked the dark tone of Breaking Bad, here are similar crime dramas...
```

---

## Project Structure

```
├── main.py                     # entrypoint: terminal chat
├── app.py                      # entrypoint: Gradio web chat
│
├── movie_chatbot/              # the application, one layer per directory
│   ├── agent/                  # the LangGraph agent
│   │   ├── prompt.py           #   the system prompt (prose only)
│   │   ├── state.py            #   MediaQuery — what the graph carries between nodes
│   │   ├── model.py            #   LLM backend + tool bindings (swap providers here)
│   │   ├── nodes.py            #   llm_call, tool_node, update_context, should_continue
│   │   └── graph.py            #   how the nodes are wired; the compiled media_agent
│   │
│   ├── tools/                  # the @tool functions the LLM may call
│   │   ├── search.py           #   find_media
│   │   ├── summary.py          #   get_media_summary
│   │   ├── discovery.py        #   get_media_recommendations, get_similar_media
│   │   ├── credits.py          #   get_cast, get_crew
│   │   └── __init__.py         #   ALL_TOOLS — the list the agent binds
│   │
│   ├── ui/                     # front ends
│   │   ├── gradio_app.py       #   the web chat
│   │   └── rendering.py        #   pure string helpers (thinking blocks, poster links)
│   ├── cli.py                  # terminal chat loop
│   │
│   ├── media_lookup.py         # title -> TMDB id (used by every tool; not a tool)
│   ├── summarizer.py           # shortening plot overviews (not a tool)
│   ├── formatters.py           # rendering a TMDB result as a tool-output line
│   └── tmdb_client.py          # raw TMDB HTTP — the only module that touches the network
│
├── tests/                      # pytest suite; all network calls mocked
└── experiments/                # scratch and superseded code, imported by nothing
```

Each layer only reaches downwards: LLM knowledge stops at `agent/`, network
knowledge stops at `tmdb_client.py`. Anything that isn't itself a tool lives
outside `tools/`, so opening a tool module shows you tools and nothing else.

---

## Roadmap

- [x] Gradio web UI
- [ ] Genre classification for mood-based discovery
- [ ] Streaming responses

## License

MIT
