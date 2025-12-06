from langchain.tools import tool
from TMDB import *
import json


def get_media_id(media_name: str, media_year: int = None, media_type: str = "movie"):
        
    media_name_lower = media_name.lower()
    results = search_for_media(media_name, media_type)
    
    if not results:
        return None
    
    for item in results:
        title = (item.get('title') or item.get('name') or '').lower()
        if title == media_name_lower:
            # check if year is specified, if so check release date
            if media_year:
                release_date = item.get('release_date') or item.get('first_air_date')
                if release_date and release_date.startswith(str(media_year)):
                    return str(item['id'])
            return str(item['id'])
        
    if media_year:
        release_date = item.get('release_date') or item.get('first_air_date')
        if release_date and release_date.startswith(str(media_year)):
            return str(item['id'])
    
    return str(results[0]['id'])


# @tool
# def find_media(media_name: str, media_type: str="movie", sort_by: str=None) -> list:
#     """Find media files matching query and return their paths.
    
#     Args:
#         media_name: The name of the media to find.
#         media_type: The type of media to find. Defaults to "movie".
#         sort_by: The field to sort by. Defaults to None.
#     """
    
    
#     media_name = media_name.lower()
    
#     results = search_for_media(media_name, media_type)
    
#     if not results:
#         return []
    
#     if sort_by:
#         results = sorted(results, key=lambda x: x.get(sort_by, 0), reverse=True)
    
#     results_dict = []
#     for item in results[:10]:
#         title = item.get('title') or item.get('name', 'unknown')
#         year = (item.get('release_date') or item.get('first_air_date') or '')[:4]
#         rating = item.get('vote_average', 'N/A')
#         id = item['id']
#         results_dict.append({
#             f"ID: {id} | Title: {title} | Year: {year} | Rating: {rating}"
#         })
        
#     return "\n".join(results_dict)

# @tool
# def get_media_summary(media_id: int, media_type: str) -> str:
#     """Find media summary matching query.
    
#     Args:
#         media_id: The id of the media to find.
#         media_type: The type of media to find.
#     """
    
    
#     media_details = get_details(media_type, media_id)
    
#     if not media_details:
#         return f"No details available for {media_type} with ID {media_id}."
    
#     media_overview = media_details.get("overview", "No overview available.")
#     title = media_details.get('title') or media_details.get('name', 'unknown')
    
#     return f"Title: {title}\nOverview: {media_overview}"





def get_media_recommendations(media_name: str, media_type: str):
    media_id = get_media_id(media_name, media_type=media_type)
    
    if not media_id:
        return f"No media found with name {media_name}."
    
    recommendations = get_recommendations(media_type, int(media_id))
    
    return recommendations


def get_similar_media(media_name: str, media_type: str):
    media_id = get_media_id(media_name, media_type=media_type)
    
    if not media_id:
        return f"No media found with name {media_name}."
    
    similar = get_similar(media_type, int(media_id))
    
    return similar



recommendations_list = get_media_recommendations("Inception", "movie")

# print("Recommendations for Inception:\n")
with open('recommendations.txt', 'w') as f:
    for rec in recommendations_list['results']:
        title = rec.get('title')
        print(f'Title: {title}\n', file=f)
    

similar_list = get_similar_media("Inception", "movie")
# print("Similar media to Inception:\n")
with open('similar.txt', 'w') as f:
    for sim in similar_list['results']:
        title = sim.get('title')
        print(f'Title: {title}\n', file=f)
        
        
with open(r'C:\Users\oo222\Documents\Code Stuff\Personal\AI-ChatBot\recommendations.txt', 'r') as f1,
     open(r'C:\Users\oo222\Documents\Code Stuff\Personal\AI-ChatBot\similar.txt', 'r') as f2:
