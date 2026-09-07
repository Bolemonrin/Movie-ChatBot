"""Rendering a TMDB result item as the one-line string a tool returns.

The recommendation and similar-media tools produced byte-identical formatting
blocks; both now call format_media_line so the shape of a result line is
defined in exactly one place.
"""
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"


def poster_url(poster_path: str | None) -> str | None:
    """Expand TMDB's relative poster path into a full image URL."""
    return f"{POSTER_BASE_URL}{poster_path}" if poster_path else None


def media_title(item: dict) -> str:
    """Movies carry 'title', TV carries 'name'."""
    return item.get('title') or item.get('name') or 'unknown'


def media_year(item: dict) -> str:
    """Movies carry 'release_date', TV carries 'first_air_date'."""
    return (item.get('release_date') or item.get('first_air_date') or '')[:4]


def format_media_line(item: dict, overview: str | None) -> str:
    """One result line for the discovery tools, with the overview passed in
    already summarized."""
    return (
        f"Title: {media_title(item)} | Overview: {overview} | "
        f"Year: {media_year(item)} | Rating: {item.get('vote_average', 'N/A')} | "
        f"Poster: {poster_url(item.get('poster_path'))}\n"
    )
