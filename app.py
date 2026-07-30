"""Gradio chat UI for the Movie-ChatBot langgraph agent.

Run with:  uv run python app.py   (then open http://localhost:7860)

What this template gives you:
- Chat with per-browser-session memory (each session gets its own langgraph thread_id,
  so the checkpointer in main.py keeps the conversation context).
- A collapsible "Thinking" panel per turn — qwen3 emits <think>...</think> blocks,
  which are split out of the visible answer and shown in their own panel.
- A collapsible panel for every tool call (name + args) and every tool result, driven
  live from langgraph's stream_mode="updates" events as each node runs.
- Poster URLs in tool results are rendered as clickable images.

This is the throwaway-able prototype layer: when you move to React + FastAPI, the
agent (main.media_agent) carries over unchanged and only this file is replaced.
"""
import re
import uuid

import gradio as gr
from langchain_core.messages import HumanMessage

from main import media_agent

# qwen3 wraps its chain-of-thought in <think>...</think> inside the message content.
THINK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL)


def split_thinking(text: str) -> tuple[str, str]:
    """Separate <think> blocks from the user-facing answer."""
    thinking = "\n\n".join(m.strip() for m in THINK_RE.findall(text))
    visible = THINK_RE.sub("", text).strip()
    return thinking, visible


def linkify_posters(text: str) -> str:
    """Turn 'Poster: <url>' lines from the tools into clickable inline images."""
    return re.sub(
        r"Poster: (https?://\S+)",
        r'Poster: [<img src="\1" width="120">](\1)',
        text,
    )


def format_args(args: dict) -> str:
    return ", ".join(f"{k}={v!r}" for k, v in args.items())


def respond(message: str, history: list, thread_id: str | None):
    """Stream one user turn through the agent, yielding UI updates as nodes finish.

    A generator: each `yield` repaints the chat, so panels appear one by one while
    the graph is still running instead of everything arriving at the end.
    """
    message = (message or "").strip()
    if not message:
        yield history, "", thread_id
        return

    # One thread per browser session = one remembered conversation (see the
    # checkpointer in main.py). None on the first turn, then reused.
    thread_id = thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    history = history + [gr.ChatMessage(role="user", content=message)]
    yield history, "", thread_id  # show the user's message and clear the textbox

    try:
        # stream_mode="updates" emits {node_name: state_delta} as each node completes.
        for update in media_agent.stream(
            {"messages": [HumanMessage(content=message)]},
            config=config,
            stream_mode="updates",
        ):
            for node, delta in update.items():
                if not delta or "messages" not in delta:
                    continue  # update_context returns no messages

                for msg in delta["messages"]:
                    if node == "llm_call":
                        raw = msg.content if isinstance(msg.content, str) else str(msg.content)
                        thinking, visible = split_thinking(raw)
                        # Some langchain-ollama versions put reasoning here instead
                        thinking = msg.additional_kwargs.get("reasoning_content") or thinking

                        if thinking:
                            history.append(gr.ChatMessage(
                                role="assistant",
                                content=thinking,
                                metadata={"title": "🧠 Thinking", "status": "done"},
                            ))
                        for tc in getattr(msg, "tool_calls", []):
                            history.append(gr.ChatMessage(
                                role="assistant",
                                content=f"`{tc['name']}({format_args(tc['args'])})`",
                                metadata={"title": f"🔧 Calling {tc['name']}", "status": "pending"},
                            ))
                        if visible:  # the final user-facing answer
                            history.append(gr.ChatMessage(role="assistant", content=visible))

                    elif node == "tool_node":
                        # The pending 🔧 panel's tool has now returned — mark it done
                        for m in history:
                            if m.metadata and m.metadata.get("status") == "pending":
                                m.metadata["status"] = "done"
                        history.append(gr.ChatMessage(
                            role="assistant",
                            content=linkify_posters(str(msg.content)),
                            metadata={"title": f"📄 {msg.name} result", "status": "done"},
                        ))

                    yield history, "", thread_id
    except Exception as e:
        history.append(gr.ChatMessage(
            role="assistant",
            content=f"⚠️ Something went wrong: {e}",
        ))

    yield history, "", thread_id


def new_conversation():
    """Clear the chat and drop the thread_id so the next turn starts a fresh thread."""
    return [], None


with gr.Blocks(title="🎬 Movie ChatBot") as demo:
    gr.Markdown(
        "# 🎬 Movie ChatBot\n"
        "Ask about movies and TV shows — summaries, cast, crew, recommendations. "
        "Expand the 🧠/🔧 panels to see how the agent got its answer."
    )

    thread_state = gr.State(None)
    chatbot = gr.Chatbot(height=520, show_label=False)

    with gr.Row():
        msg_box = gr.Textbox(
            placeholder="e.g. what's the summary of Finding Nemo?",
            show_label=False,
            scale=5,
        )
        send_btn = gr.Button("Send", variant="primary", scale=1)
        clear_btn = gr.Button("New chat", scale=1)

    # Enter key and Send button do the same thing
    msg_box.submit(respond, [msg_box, chatbot, thread_state], [chatbot, msg_box, thread_state])
    send_btn.click(respond, [msg_box, chatbot, thread_state], [chatbot, msg_box, thread_state])
    clear_btn.click(new_conversation, None, [chatbot, thread_state])


if __name__ == "__main__":
    demo.launch()
