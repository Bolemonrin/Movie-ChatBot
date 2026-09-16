"""The @tool functions the agent can call.

One module per job:
    search.py     -- find_media
    summary.py    -- get_media_summary
    discovery.py  -- get_media_recommendations, get_similar_media
    credits.py    -- get_cast, get_crew

Everything that isn't itself a tool lives beside this package instead:
media_lookup (title -> id), summarizer (overview shortening), formatters
(result-line rendering), tmdb_client (HTTP).

ALL_TOOLS is the single list the agent binds to the model -- add a new tool here
and it becomes available to the LLM.
"""
from .credits import get_cast, get_crew
from .discovery import get_media_recommendations, get_similar_media
from .search import find_media
from .summary import get_media_summary

ALL_TOOLS = [
    find_media,
    get_media_summary,
    get_media_recommendations,
    get_similar_media,
    get_cast,
    get_crew,
]

__all__ = [
    "ALL_TOOLS",
    "find_media",
    "get_media_summary",
    "get_media_recommendations",
    "get_similar_media",
    "get_cast",
    "get_crew",
]
