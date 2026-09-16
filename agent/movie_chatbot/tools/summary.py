"""Detail tool: the plot summary for one title."""
from typing import Literal

from langchain.tools import tool

from ..media_lookup import resolve_media_id
from ..summarizer import summarize_overview
from ..tmdb_client import get_details


@tool
def get_media_summary(media_name: str, media_type: Literal['movie', 'tv']) -> str:
    # [Claude Code] Fixed the description below: it said "by its ID and type" — this
    # headline is sent to the model as the tool description, and mentioning an ID
    # encouraged it to pass media_id instead of media_name.
    """Get a summary of the media by its name and type.

    Args:
        media_name (str): The name of the media.
        media_type (str): The type of the media.

    Returns:
        str: A summary of the media.
    """
    try:
        media_id = resolve_media_id(media_name, media_type)

        # Get details for the specified media
        media_details = get_details(media_type, media_id)

        if not media_details:
            return f"No details available for {media_type} with ID {media_id}."

        # Extract overview and title from details
        media_overview = media_details.get("overview", "No overview available.")
        title = media_details.get('title') or media_details.get('name', 'unknown')
        summary = summarize_overview(media_overview)

        # Return the formatted summary
        return f"Title: {title}\nOverview: {summary}"
    except Exception as e:
        print(f"[get_media_summary] error: {e}")
        return f"Unable to retrieve summary.\nReason: {e}"
