"""Pure text helpers for the chat UI.

No Gradio, no agent -- just string in, string out, so they can be read and
tested without spinning anything up.
"""
import re

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
    """Render a tool call's arguments for the 🔧 panel."""
    return ", ".join(f"{k}={v!r}" for k, v in args.items())
