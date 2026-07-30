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
pip install -r requirements.txt
```

### Configure

Create a `.env` file (never commit this):

```
TMDB_ACCESS_TOKEN=your_tmdb_token_here
OPENAI_API_KEY=your_key_here   # only if using OpenAI models
```

### Run

```bash
python main.py
```

Then chat:

```
User: recommend shows like Breaking Bad
AI: Since you liked the dark tone of Breaking Bad, here are similar crime dramas...
```

---

## Project Structure

```
├── main.py          # LangGraph agent: state, nodes, edges, memory, chat loop
├── test_tools.py    # @tool-decorated TMDB tools (search, summary, cast, crew, recs)
├── TMDB.py          # Raw TMDB API client (requests)
└── requirements.txt
```

---

## Roadmap

- [ ] Gradio web UI
- [ ] Genre classification for mood-based discovery
- [ ] Streaming responses

## License

MIT
