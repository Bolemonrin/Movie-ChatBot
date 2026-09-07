"""Search tool: find a title on TMDB."""
from typing import Literal, Optional

from langchain.tools import tool

from ..media_lookup import normalize_media_type
from ..tmdb_client import search_for_media

MAX_RESULTS = 10


@tool
def find_media(
    media_name: str,
    media_type: Literal["movie", "tv"] = "movie",
    sort_by: Optional[Literal["vote_average", "popularity"]] = None,
) -> str:
    """Search TMDB for a movie or TV show by name.

    Args:
        media_name: The title to search for.
        media_type: Exactly "movie" or "tv". Use "tv" for shows and series.
        sort_by: Optionally re-rank results by "vote_average" or "popularity".

    Returns:
        A newline-separated list of matches, each with ID, Type, Title, Year, Rating.
        Pass the Title and the Type to any follow-up tool.
    """
    # [Claude Code] Fixed the docstring above: it said "Pass both the ID and the Type to
    # any follow-up tool", but every follow-up tool takes a media_name — the model obeyed
    # the docstring and sent media_id, causing the pydantic "media_name Field required"
    # ValidationError.
    mt = normalize_media_type(media_type)
    if mt not in ("movie", "tv"):
        return f"Invalid media_type '{media_type}'. Use 'movie' or 'tv'."

    try:
        results = search_for_media(media_name, mt)
    except Exception as e:
        return f"TMDB search failed: {e}"

    if not results:
        return f"No {mt} results found for '{media_name}'."

    if sort_by:
        results = sorted(results, key=lambda x: x.get(sort_by) or 0, reverse=True)

    lines = []
    for item in results[:MAX_RESULTS]:
        title = item.get("title") or item.get("name") or "unknown"
        year = (item.get("release_date") or item.get("first_air_date") or "")[:4] or "Unknown"
        rating = item.get("vote_average", "N/A")
        lines.append(f"ID: {item['id']} | Type: {mt} | Title: {title} | Year: {year} | Rating: {rating}")

    return "\n".join(lines)
