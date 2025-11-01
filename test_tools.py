from langchain.tools import tool
from TMDB import *

@tool("find_media", return_direct=True)
def find_media(media_name: str, media_type: str="movie", sort_by: str=None):
    media_name = media_name.lower()
    
    results = search_for_media(media_name, media_type)
    
    if not results:
        return []
    
    sorted_results = sorted(results, key=lambda x: x.get(sort_by, 0), reverse=True)
    return sorted_results

@tool("get_summary", return_direct=True)
def get_media_summary(media_id: int, media_type: str):
    media_details = get_details(media_type, media_id) or {}
    media_overview = media_details.get("overview", "")
    
    return media_overview