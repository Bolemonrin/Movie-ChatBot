from TMDB import *


def find_media(media_name: str, media_type: str="movie", sort_by: str=None):    
    results = search_for_media(media_name, media_type)
    
    if not results:
        return []
    
    if sort_by:
        results.sort(key=lambda x: x.get(sort_by, 0), reverse=True)

    return results


def get_media_recommendations(result: list, media_type: str, media_id: int, limit: int = 5):
    if not result:
        return []
    
    if len(result) >= 3:
        recommendations = get_recommendations(media_type, media_id)
        return recommendations[:limit]
    
    similar = get_similar(media_type, media_id)
    return similar[:limit]
    
def get_media_id(results: list, media_name: str, media_year: int = None):
    if not results:
        return None
    
    media_name = media_name.lower()
    
    for item in results:
        title = (item.get('title') or item.get('name') or '').lower()
        if title == media_name:
            # check if year is specified, if so check release date
            if media_year:
                release_date = item.get('release_date') or item.get('first_air_date')
                if release_date.startswith(str(media_year)):
                    return item['id']
            return item['id']
    
    return results[0]['id']

def get_media_summary(media_id: int, media_type: str):
    media_details = get_details(media_type, media_id) or {}
    media_overview = media_details.get("overview", "")
    
    return media_overview


def clarify_for_ambiguity(results: list, clarification: dict):
    if not results:
        return None
    
    
    if 'year' in clarification:
        for item in results:
            release_date = item.get('release_date') or item.get('first_air_date') or ''
            if release_date.startswith(str(clarification['year'])):
                return item
    
    if 'actor' in clarification:
        actor_name = find_cast(
            clarification.get('actor'),
            clarification.get('media_type'),
            clarification.get('media_id')
        )
        
        if actor_name:
            return actor_name
        
    if clarification.get('sort_by') == 'latest':
        validItems = [item for item in results if item.get('release_date') or item.get('first_air_date')]
        
        if validItems:
            return max(results, key=lambda x: x.get('release_date') or x.get('first_air_date'))
        
    return None

    
def find_cast(actor: str, media_type: str, media_id: int, cast_type: str = "Acting"):
    
    # print(media_credits)
    try:
        credits = get_media_credits(media_type, media_id) or {}
        get_cast = credits.get('cast', [])
    
    except Exception as e:
        print("Error: ", e)
    
    actors = []
    for person in get_cast:
        if person.get('known_for_department') == cast_type:
            actors.append(person)
    
    actor = actor.strip().lower()
    for person in actors:
        if person.get('name', '').lower() == actor:
            return person['name'].lower()
        
    return None


# search = find_media("The Lego Movie", "movie")
# media_id = get_media_id(search, "The Lego Movie")
# summary = get_media_summary(media_id, "movie")
# recommendation = get_media_recommendations("movie", media_id)

# print(search)
# print(summary)
# print("\n\n")
# print(recommendation)

type = 'movie'
id = 24428
actor = 'Robert Downey Jr.'
credits = find_cast(actor, type, id)
print(credits)