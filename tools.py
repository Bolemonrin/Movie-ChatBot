# tools.py

from TMDB import *  # Importing functions and classes from TMDB module

# Function to find media based on name, type, and optionally sort by a specific attribute
def find_media(media_name: str, media_type: str = "movie", sort_by: str = None):
    results = search_for_media(media_name, media_type)  # Search for media using the provided name and type
    if not results:
        return []  # Return an empty list if no results are found
    if sort_by:
        results.sort(key=lambda x: x.get(sort_by, 0), reverse=True)  # Sort results based on the specified attribute in descending order
    return results

# Function to get recommendations for media based on search results
def get_media_recommendations(results: list, media_type: str, media_id: int, limit: int = 5):
    if not results:
        return []  # Return an empty list if no results are found
    if len(results) >= 3:
        recommendations = get_recommendations(media_type, media_id)  # Get recommendations for the given media
        return recommendations[:limit]  # Return up to 'limit' number of recommendations

    similar = get_similar(media_type, media_id)  # Get similar media based on the given ID
    return similar[:limit]  # Return up to 'limit' number of similar media

# Function to get the media ID based on search results and optionally a year
def get_media_id(results: list, media_name: str, media_year: int = None):
    if not results:
        return None  # Return None if no results are found

    media_name = media_name.lower()  # Convert media name to lowercase for case-insensitive comparison
    for item in results:
        title = (item.get('title') or item.get('name') or '').lower()  # Extract and convert the title to lowercase
        if title == media_name:
            # Check if year is specified, if so check release date
            if media_year:
                release_date = item.get('release_date') or item.get('first_air_date')
                if release_date.startswith(str(media_year)):
                    return item['id']  # Return the media ID if the year matches
            return item['id']  # Return the media ID

    return results[0]['id']  # Return the ID of the first result if no exact match is found

# Function to get a summary of media based on its ID and type
def get_media_summary(media_id: int, media_type: str):
    media_details = get_details(media_type, media_id) or {}  # Get details for the given media ID
    media_overview = media_details.get("overview", "")  # Extract the overview from media details

    return media_overview

# Function to clarify search results based on user clarification (e.g., year, actor)
def clarify_for_ambiguity(results: list, clarification: dict):
    if not results:
        return None  # Return None if no results are found
    if 'year' in clarification:
        for item in results:
            release_date = item.get('release_date') or item.get('first_air_date') or ''
            if release_date.startswith(str(clarification['year'])):
                return item  # Return the item if the year matches
    if 'actor' in clarification:
        actor_name = find_cast(
            clarification.get('actor'),
            clarification.get('media_type'),
            clarification.get('media_id')
        )

        if actor_name:
            return actor_name  # Return the actor's name if found
    if clarification.get('sort_by') == 'latest':
        validItems = [item for item in results if item.get('release_date') or item.get('first_air_date')]

        if validItems:
            return max(results, key=lambda x: x.get('release_date') or x.get('first_air_date'))

    return None  # Return the latest item if no specific clarification is found

# Function to find an actor's name based on media type, ID, and optionally a cast type
def find_cast(actor: str, media_type: str, media_id: int, cast_type: str = "Acting"):

    try:
        credits = get_media_credits(media_type, media_id) or {}  # Get credits for the given media ID
        get_cast = credits.get('cast', [])  # Extract the cast list from the credits
    except Exception as e:
        print("Error: ", e)  # Print an error message if an exception occurs
    actors = []
    for person in get_cast:
        if person.get('known_for_department') == cast_type:
            actors.append(person)

    actor = actor.strip().lower()  # Convert the actor's name to lowercase and strip any leading/trailing whitespace
    for person in actors:
        if person.get('name', '').lower() == actor:
            return person['name'].lower()  # Return the actor's name if found

    return None  # Return None if no matching actor is found

# Example usage of functions
type = 'movie'
id = 24428
actor = 'Robert Downey Jr.'
credits = find_cast(actor, type, id)
print(credits)
