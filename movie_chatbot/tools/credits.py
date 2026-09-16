"""Credits tools: who acted in it, and who made it.

Both hit the same TMDB credits endpoint, and both have to cope with its two
shapes: movies use /credits (flat "character" and "job" fields) while TV uses
/aggregate_credits (nested "roles" and "jobs" lists).
"""
from typing import Literal

from langchain.tools import tool

from ..media_lookup import resolve_media_id
from ..tmdb_client import get_media_credits

DEFAULT_CAST_LIMIT = 10

# On TV there is no single "Director" credit, so treat the show-runner style
# jobs as the equivalent.
TV_DIRECTOR_JOBS = {"Creator", "Executive Producer", "Series Director"}


@tool
def get_cast(media_name: str, media_type: Literal['movie', 'tv'], limit: int = DEFAULT_CAST_LIMIT) -> str:
    """Get the cast of the media by its name and type.

    Args:
        media_name (str): The name of the media.
        media_type (str): The type of the media.
        limit (int, optional): The number of cast members to return. Defaults to 10.

    Returns:
        str: A list of cast members.
    """
    try:
        # Get the media ID
        media_id = resolve_media_id(media_name, media_type)

        # Fetch cast for the specified media
        cast_members = get_media_credits(media_type, media_id)
        cast_list = cast_members.get('cast', [])

        output = []
        for mem in cast_list[:limit]:
            name = mem.get('name', 'unknown')
            # [Claude Code] TV uses the aggregate_credits endpoint, where characters
            # live in a "roles" list instead of a top-level "character" field — the old
            # code showed every TV character as "unknown".
            if media_type == "tv":
                roles = mem.get('roles') or []
                character = ", ".join(r.get('character') or 'unknown' for r in roles) or 'unknown'
            else:
                character = mem.get('character', 'unknown')
            output.append(f"Actor: {name} | Character: {character}")

        return "\n".join(output)
    except Exception as e:
        print(f"[get_cast] error: {e}")
        # [Claude Code] Was `return ""`: an empty tool result gives the model nothing to
        # reason about, so it would hallucinate a cast. Now matches the other tools.
        return f"Unable to retrieve cast.\nReason: {e}"


@tool
def get_crew(media_name: str, media_type: Literal['movie', 'tv']) -> str:
    """Get the crew of the media by its name and type.

    Args:
        media_name (str): The name of the media.
        media_type (str): The type of the media.

    Returns:
        str: A list of crew members.
    """
    try:
        # Get the media ID
        media_id = resolve_media_id(media_name, media_type)

        # Fetch crew for the specified media
        crew_members = get_media_credits(media_type, media_id)
        crew_list = crew_members.get('crew', [])
        if media_type == "movie":
            directors = [m for m in crew_list if m.get("job") == "Director"]
        else:
            # [Claude Code] TV uses the aggregate_credits endpoint, where crew members
            # carry a "jobs" list instead of a top-level "job" field — the old filter
            # matched nothing, so TV crew results were always empty.
            directors = [
                m for m in crew_list
                if any(j.get("job") in TV_DIRECTOR_JOBS for j in (m.get("jobs") or []))
            ]

        directors = sorted(directors, key=lambda x: x.get('popularity', 0), reverse=True)

        output = [f"Director: {mem.get('name', 'unknown')}" for mem in directors]
        return "\n".join(output)
    except Exception as e:
        print(f"[get_crew] error: {e}")
        return f"Unable to retrieve crew.\nReason: {e}"
