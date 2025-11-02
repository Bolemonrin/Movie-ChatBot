from langchain.tools import tool
from TMDB import *

@tool
def find_media(media_name: str, media_type: str="movie", sort_by: str=None) -> list:
    """Find media files matching query and return their paths.
    
    Args:
        media_name: The name of the media to find.
        media_type: The type of media to find. Defaults to "movie".
        sort_by: The field to sort by. Defaults to None.
    """
    
    
    media_name = media_name.lower()
    
    results = search_for_media(media_name, media_type)
    
    if not results:
        return []
    
    sorted_results = sorted(results, key=lambda x: x.get(sort_by, 0), reverse=True)
    return sorted_results

@tool
def get_media_summary(media_id: int, media_type: str) -> str:
    """Find media summary matching query.
    
    Args:
        media_id: The id of the media to find.
        media_type: The type of media to find.
    """
    
    
    media_details = get_details(media_type, media_id) or {}
    media_overview = media_details.get("overview", "")
    
    return media_overview

@tool
def get_media_id(results: list, media_name: str, media_year: int = None):
    """Get the ID for media type to pass to other tools
    
    Args:
        media_id: The id of the media to find.
        media_name: The name of the media to find.
        media_year: The year of the media to find.
    """
    
    if not results:
        return None
    
    media_name = media_name.lower()
    
    for item in results:
        title = (item['title'] or item['name'] or '').lower()
        if title == media_name:
            # check if year is specified, if so check release date
            if media_year:
                release_date = item['release_date'] or item['first_air_date']
                if release_date.startswith(str(media_year)):
                    return item['id']
            return item['id']
    
    return results[0]['id'] if results else None 