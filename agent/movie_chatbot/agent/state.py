"""The shape of the agent's memory: what LangGraph carries between nodes."""
import operator
from typing import Annotated, List

from langchain_core.messages import AnyMessage
from typing_extensions import NotRequired, TypedDict


class MediaQuery(TypedDict):
    # conversation history
    messages: Annotated[List[AnyMessage], operator.add]

    # persistent context
    # [Claude Code] NotRequired lets the REPL invoke with just {"messages": [...]}. The
    # old loop passed last_media_name=None etc. on every turn, which overwrote whatever
    # the checkpointer had remembered with None — one of the reasons follow-up questions
    # forgot the movie being discussed.
    last_media_name: NotRequired[str | None]
    last_media_type: NotRequired[str | None]
    llm_calls: NotRequired[int]
