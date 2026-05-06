from TMDB import *
from langchain.tools import tool
import json


def get_media_id(media_name: str, media_year: int = None, media_type: str = "movie"):
    try:
        media_name_lower = media_name.lower()
        results = search_for_media(media_name, media_type)

        if not results:
            return None

        for item in results:
            title = (item.get('title') or item.get('name') or '').lower()
            if title == media_name_lower:
                # check if year is specified, if so check release date
                if media_year:
                    release_date = item.get(
                        'release_date') or item.get('first_air_date')
                    if release_date and release_date.startswith(str(media_year)):
                        return str(item['id'])
                return str(item['id'])

        if media_year:
            release_date = item.get('release_date') or item.get('first_air_date')
            if release_date and release_date.startswith(str(media_year)):
                return str(item['id'])

        return str(results[0]['id'])
    except Exception as e:
        print(f"[get_media_id] error: {e}")
        return None


@tool
def find_media(media_name: str, media_type: str="movie", sort_by: str=None) -> list:
    """Search for media by name and return a list of matching media items.
    Args:
        media_name (str): The name of the media to search for.
        media_type (str, optional): The type of media to search for. Defaults to "movie".
        sort_by (str, optional): The field to sort the results by. Defaults to None.
    Returns:
        list: A list of matching media items.
    """
    
    try:
        media_name = media_name.lower()

        results = search_for_media(media_name, media_type)

        if not results:
            return []

        if sort_by:
            results = sorted(results, key=lambda x: x.get(sort_by, 0), reverse=True)

        results_dict = []
        for item in results[:10]:
            title = item.get('title') or item.get('name', 'unknown')
            year = (item.get('release_date') or item.get('first_air_date') or '')[:4]
            rating = item.get('vote_average', 'N/A')
            id = item['id']
            results_dict.append({
                f"ID: {id} | Title: {title} | Year: {year} | Rating: {rating}"
            })

        return "\n".join(results_dict)
    except Exception as e:
        print(f"[find_media] error: {e}")
        return []


@tool
def get_media_summary(media_id: int, media_type: str) -> str:
    """Get a summary of the media by its ID and type.
    Args:
        media_id (int): The ID of the media.
        media_type (str): The type of the media.
    Returns:
        str: A summary of the media.
    """
    
    try:
        media_details = get_details(media_type, media_id)

        if not media_details:
            return f"No details available for {media_type} with ID {media_id}."

        media_overview = media_details.get("overview", "No overview available.")
        title = media_details.get('title') or media_details.get('name', 'unknown')

        return f"Title: {title}\nOverview: {media_overview}"
    except Exception as e:
        print(f"[get_media_summary] error: {e}")
        return ""


@tool
def get_media_recommendations(media_name: str, media_type: str, page: int = 1) -> str:
    """Get personalized recommendations based on what audiences who liked this media also enjoyed.
    
    Args:
        media_name (str): The name of the media.
        media_type (str): The type of the media.
    Returns:
        str: A list of recommended media.
    """
    
    try:
        media_id = get_media_id(media_name, media_type=media_type)

        if not media_id:
            return f"No media found with name {media_name}."

        recommendations = get_recommendations(media_type, int(media_id), page=page)
        results = recommendations.get('results', [])[:10]
        
        output = []
        for res in results:
            title = res.get('title') or res.get('name', 'unknown')
            overview = res.get('overview', 'No overview available.')
            year = (res.get('release_date') or res.get('first_air_date') or '')[:4]
            rating = res.get('vote_average', 'N/A')
            poster_path = res.get('poster_path', None)
            output.append(f"Title: {title} | Overview: {overview} | Year: {year} | Rating: {rating} | Poster: {poster_path}\n")
        
        final_output = "\n".join(output)
        return final_output
    except Exception as e:
        print(f"[get_media_recommendations] error: {e}")
        return ""


@tool
def get_similar_media(media_name: str, media_type: str, page: int = 1) -> str:
    """Find movies/TV shows that are similar in genre, themes, and style to a specific title.
    
    Args:
        media_name (str): The name of the media.
        media_type (str): The type of the media.
    Returns:
        str: A list of similar media.
    """
    
    try:
        media_id = get_media_id(media_name, media_type=media_type)

        if not media_id:
            return f"No media found with name {media_name}."

        similar = get_similar(media_type, int(media_id), page=page)
        results = similar.get('results', [])
        
        similar_title = set()
        
        output = []
        for res in results:
            title = res.get('title') or res.get('name', 'unknown')
            overview = res.get('overview', 'No overview available.')
            year = (res.get('release_date') or res.get('first_air_date') or '')[:4]
            rating = res.get('vote_average', 'N/A')
            poster_path = res.get('poster_path', None)
            
            if title.lower() in similar_title:
                continue
            similar_title.add(title.lower())
            
            output.append(f"Title: {title} | Overview: {overview} | Year: {year} | Rating: {rating} | Poster: {poster_path}\n")
            
            if len(output) >= 5:
                break

        final_output = "\n".join(output)
        return final_output
    except Exception as e:
        print(f"[get_similar_media] error: {e}")
        return ""


@tool
def get_cast(media_name: str, media_type: str, limit: int = 10) -> str:
    """Get the cast of the media by its name and type.
    Args:
        media_name (str): The name of the media.
        media_type (str): The type of the media.
    Returns:
        str: A list of cast members.
    """
    
    try:
        media_id = get_media_id(media_name, media_type=media_type)
        
        if not media_id:
            return f"No media found with name {media_name}."
        
        cast_members = get_media_credits(media_type, media_id)
        cast_list = cast_members.get('cast', [])
        
        output = []
        for mem in cast_list[:limit]:
            name = mem.get('name', 'unknown')
            character = mem.get('character', 'unknown')
            output.append(f"Actor: {name} | Character: {character}")
        
        final = "\n".join(output)
        return final
    except Exception as e:
        print(f"[get_cast] error: {e}")
        return ""


@tool
def get_crew(media_name: str, media_type: str) -> str:
    """Get the crew of the media by its name and type.
    Args:
        media_name (str): The name of the media.
        media_type (str): The type of the media.
    Returns:
        str: A list of crew members.
    """
    
    try:
        media_id = get_media_id(media_name, media_type=media_type)
        
        if not media_id:
            return f"No media found with name {media_name}."
        
        crew_members = get_media_credits(media_type, media_id)
        crew_list = crew_members.get('crew', [])
        directors = [mem for mem in crew_list if mem.get('job') == 'Director']
        
        output = []
        ranked_directors = sorted(directors, key=lambda x: x.get('popularity', 0), reverse=True)
        directors = ranked_directors
        
        if len(directors) == 1:
            name = directors[0].get('name', 'unknown')
            output.append(f"Director: {name}")
            return "\n".join(output)
        else:
            for mem in directors:
                name = mem.get('name', 'unknown')
                output.append(f"Director: {name}")
        
        final = "\n".join(output)
        return final
    except Exception as e:
        print(f"[get_crew] error: {e}")
        return ""
