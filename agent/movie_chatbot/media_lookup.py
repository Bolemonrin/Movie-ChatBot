"""Turning a human-typed title into a TMDB id.

Not tools -- these are the plumbing every tool needs before it can call an
endpoint, since the model speaks in titles ("Django Unchained") and TMDB speaks
in ids (68718). Kept out of the tool modules so the @tool functions stay short
and so this logic can be tested on its own.
"""
from typing import Optional

from .tmdb_client import search_for_media

# Loose spellings the model (or a direct caller) might use for a media type.
# Note that the @tool signatures use Literal["movie", "tv"], so the tool schema
# rejects these before the function body runs -- this map only rescues direct
# Python calls.
MEDIA_ALIASES = {
    "tv_show": "tv", "tvshow": "tv", "tv_series": "tv", "series": "tv",
    "show": "tv", "television": "tv",
    "film": "movie", "movies": "movie", "feature": "movie",
}


def normalize_media_type(media_type: str) -> str:
    """Fold an alias like 'film' or 'series' down to 'movie' / 'tv'.

    Returns the cleaned-up input unchanged when it isn't a known alias, so the
    caller can decide how to report an invalid value.
    """
    cleaned = media_type.lower().strip()
    return MEDIA_ALIASES.get(cleaned, cleaned)


def get_media_id(
        media_name: str,
        media_year: Optional[int] = None,
        media_type: str = "movie"
    ) -> Optional[int]:
    """
    Fetches the media ID from TMDB.

    Args:
        media_name (str): The name of the media to search for.
        media_year (int, optional): The year of the media release. Defaults to None.
        media_type (str, optional): The type of media (e.g., "movie", "tv"). Defaults to "movie".

    Returns:
        str: The media ID if found, otherwise None.
    """
    try:
        # [Claude Code] Fixed case-sensitive comparison: the titles below are lowercased
        # but media_name wasn't, so "Django Unchained" never matched "django unchained"
        # and the exact-match loop (and the year filter with it) effectively never ran.
        media_name_lower = media_name.lower().strip()

        # Search for media in TMDB
        results = search_for_media(media_name, media_type)

        if not results:
            return None

        # Iterate through search results to find a match
        for item in results:
            title = (item.get('title') or item.get('name') or '').lower()
            if title == media_name_lower:
                # Check if year is specified and matches the release date
                if media_year:
                    release_date = item.get(
                        'release_date') or item.get('first_air_date')
                    if release_date and release_date.startswith(str(media_year)):
                        return item['id']
                else:
                    return item['id']

        # No exact title match -- fall back to TMDB's most relevant result.
        return results[0]['id']
    except Exception as e:
        print(f"[get_media_id] error: {e}")
        return None


def resolve_media_id(
        media_name: str,
        media_type: str,
    ) -> int:
    """Same as get_media_id, but raises instead of returning None.

    Every tool calls this one. [Claude Code] It was print + return 0: the model
    never sees console prints, and ID 0 produced confusing TMDB 404s downstream.
    Raising instead lets each tool's except block return a readable "not found"
    message as the tool result.
    """
    media_id = get_media_id(media_name, media_type=media_type)
    if not media_id:
        raise ValueError(f"No {media_type} found named '{media_name}'.")

    return media_id
