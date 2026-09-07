"""Discovery tools: "what else would I like?" and "what is this one like?".

Both walk a list of TMDB results and render them with the shared
format_media_line helper; they differ only in which endpoint they hit and in
how many results they keep.
"""
from typing import Literal

from langchain.tools import tool

from ..formatters import format_media_line, media_title
from ..media_lookup import resolve_media_id
from ..summarizer import summarize_overview
from ..tmdb_client import get_recommendations, get_similar

MAX_RECOMMENDATIONS = 10
MAX_SIMILAR = 5


@tool
def get_media_recommendations(
    media_name: str,
    media_type: Literal['movie', 'tv'] = 'movie',
    page: int = 1
) -> str:
    """Get personalized recommendations based on what audiences who liked this media also enjoyed.

    Args:
        media_name (str): The name of the media.
        media_type (str): The type of the media.
        page (int, optional): The page number for recommendations. Defaults to 1.

    Returns:
        str: A list of recommended media.
    """
    try:
        # Get the media ID
        media_id = resolve_media_id(media_name, media_type=media_type)

        # Fetch recommendations for the specified media
        recommendations = get_recommendations(media_type, media_id, page=page)
        results = recommendations.get('results', [])[:MAX_RECOMMENDATIONS]

        output = []
        for res in results:
            overview = summarize_overview(res.get('overview', 'No overview available.'))
            output.append(format_media_line(res, overview))

        return "\n".join(output)
    except Exception as e:
        print(f"[get_media_recommendations] error: {e}")
        return f"Unable to retrieve recommendations.\nReason: {e}"


@tool
def get_similar_media(
    media_name: str,
    # [Claude Code] Was plain str: the tool schema didn't constrain the value, so the
    # model could pass e.g. "tv_show" and 404 the TMDB URL. Literal puts an enum in the
    # schema so the model must pick a valid value. Same fix on get_cast and get_crew.
    media_type: Literal['movie', 'tv'],
    page: int = 1,
) -> str:
    """Find movies/TV shows that are similar in genre, themes, and style to a specific title.

    Args:
        media_name (str): The name of the media.
        media_type (str): The type of the media.
        page (int, optional): The page number for similar media. Defaults to 1.

    Returns:
        str: A list of similar media.
    """
    try:
        # Get the media ID
        media_id = resolve_media_id(media_name, media_type)

        # Fetch similar media for the specified media
        similar = get_similar(media_type, media_id, page=page)
        results = similar.get('results', [])

        seen_titles = set()
        output = []
        for res in results:
            title = media_title(res)
            if title.lower() in seen_titles:
                continue
            seen_titles.add(title.lower())

            overview = summarize_overview(res.get('overview', 'No overview available.'))
            output.append(format_media_line(res, overview))

            if len(output) >= MAX_SIMILAR:
                break

        return "\n".join(output)
    except Exception as e:
        print(f"[get_similar_media] error: {e}")
        return f"Unable to retrieve similar media.\nReason: {e}"
