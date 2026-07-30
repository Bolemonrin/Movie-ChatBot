from pydantic import PlainSerializer

from TMDB import *
from langchain.tools import tool
import json
from typing import Literal, Optional
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.summarizers.luhn import LuhnSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
from sumy.parsers.plaintext import PlaintextParser
import nltk

nltk.download('punkt_tab')


MEDIA_ALIASES = {
    "tv_show": "tv", "tvshow": "tv", "tv_series": "tv", "series": "tv",
    "show": "tv", "television": "tv",
    "film": "movie", "movies": "movie", "feature": "movie",
}

SORT_FIELDS = {"vote_average", "popularity", "release_date", "first_air_date"}

# Function to get the media ID based on the name, year, and type of media
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

        # If no match found with specified year, return the first result
        # if media_year:
        #     release_date = item.get('release_date') or item.get('first_air_date')
        #     if release_date and release_date.startswith(str(media_year)):
        #         return str(item['id'])

        return results[0]['id']
    except Exception as e:
        print(f"[get_media_id] error: {e}")
        return None


def summarize_overview(overview:Optional[str]) -> Optional[str]:
    '''
    Summarize text using the LexRank algorithm.
    Args:
        overview (str): The input text to summarize.
    Returns:         list: Summary sentences.
    '''
    text = overview

    # parse test
    parser = PlaintextParser.from_string(text, Tokenizer('english'))

    # init LexRank summarizer
    summarizer = LuhnSummarizer(Stemmer('english'))
    summarizer.stop_words =get_stop_words('english')

    summary = summarizer(parser.document, 4)
    summary_text = " ".join([str(sentence) for sentence in summary])

    return summary_text




def resolve_media_id(
        media_name: str,
        media_type: str,
    ) -> int:
    media_id = get_media_id(media_name, media_type=media_type)
    if not media_id:
        # [Claude Code] Was print + return 0: the model never sees console prints, and
        # ID 0 produced confusing TMDB 404s downstream. Raising instead lets each tool's
        # except block return a readable "not found" message as the tool result.
        raise ValueError(f"No {media_type} found named '{media_name}'.")

    return media_id

@tool
def find_media(
    media_name: str,
    media_type: Literal["movie", "tv"] = "movie",
    sort_by: Optional[Literal["vote_average", "popularity"]] = None,
) -> str:
    """Search TMDB for a movie or TV show by name.

    Args:
        media_name: The title to search for.
        media_type: Exactly "movie" or "tv". Use "tv" for shows and series.
        sort_by: Optionally re-rank results by "vote_average" or "popularity".

    Returns:
        A newline-separated list of matches, each with ID, Type, Title, Year, Rating.
        Pass the Title and the Type to any follow-up tool.
    """
    # [Claude Code] Fixed the docstring above: it said "Pass both the ID and the Type to
    # any follow-up tool", but every follow-up tool takes a media_name — the model obeyed
    # the docstring and sent media_id, causing the pydantic "media_name Field required"
    # ValidationError.
    mt = MEDIA_ALIASES.get(media_type.lower().strip(), media_type.lower().strip())
    if mt not in ("movie", "tv"):
        return f"Invalid media_type '{media_type}'. Use 'movie' or 'tv'."

    try:
        results = search_for_media(media_name, mt)
    except Exception as e:
        return f"TMDB search failed: {e}"

    if not results:
        return f"No {mt} results found for '{media_name}'."

    if sort_by:
        results = sorted(results, key=lambda x: x.get(sort_by) or 0, reverse=True)

    lines = []
    for item in results[:10]:
        title = item.get("title") or item.get("name") or "unknown"
        year = (item.get("release_date") or item.get("first_air_date") or "")[:4] or "Unknown"
        rating = item.get("vote_average", "N/A")
        lines.append(f"ID: {item['id']} | Type: {mt} | Title: {title} | Year: {year} | Rating: {rating}")

    return "\n".join(lines)


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


# functions below use media id to find
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
        results = recommendations.get('results', [])[:10]

        output = []
        for res in results:
            title = res.get('title') or res.get('name', 'unknown')
            get_overview = res.get('overview', 'No overview available.')
            overview = summarize_overview(get_overview)
            year = (res.get('release_date') or res.get('first_air_date') or '')[:4]
            rating = res.get('vote_average', 'N/A')
            poster_path = res.get('poster_path', None)
            poster_url = (
                f"https://image.tmdb.org/t/p/w500{poster_path}"
                if poster_path
                else None
            )
            output.append(
                f"Title: {title} | Overview: {overview} | Year: {year} | Rating: {rating} | Poster: {poster_url}\n"
            )

        final_output = "\n".join(output)
        return final_output
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

        similar_title = set()

        output = []
        for res in results:
            title = res.get('title') or res.get('name', 'unknown')
            get_overview = res.get('overview', 'No overview available.')
            overview = summarize_overview(get_overview)
            year = (res.get('release_date') or res.get('first_air_date') or '')[:4]
            rating = res.get('vote_average', 'N/A')
            poster_path = res.get('poster_path', None)
            poster_url = (
                f"https://image.tmdb.org/t/p/w500{poster_path}"
                if poster_path
                else None
            )

            if title.lower() in similar_title:
                continue
            similar_title.add(title.lower())

            output.append(f"Title: {title} | Overview: {overview} | Year: {year} | Rating: {rating} | Poster: {poster_url}\n")

            if len(output) >= 5:
                break

        final_output = "\n".join(output)
        return final_output
    except Exception as e:
        print(f"[get_similar_media] error: {e}")
        return f"Unable to retrieve similar media.\nReason: {e}"

@tool
def get_cast(media_name: str, media_type: Literal['movie', 'tv'], limit: int = 10) -> str:
    """Get the cast of the media by its name and type.

    Args:
        media_name (str): The name of the media.
        media_type (str): The type of the media.
        limit (int, optional): The number of cast members to return. Defaults to 10.

    Returns:
        str: A list of cast members.
    """
    try:
        # Get the media ID
        media_id = resolve_media_id(media_name, media_type)

        # Fetch cast for the specified media
        cast_members = get_media_credits(media_type, media_id)
        cast_list = cast_members.get('cast', [])

        output = []
        for mem in cast_list[:limit]:
            name = mem.get('name', 'unknown')
            # [Claude Code] TV uses the aggregate_credits endpoint, where characters
            # live in a "roles" list instead of a top-level "character" field — the old
            # code showed every TV character as "unknown".
            if media_type == "tv":
                roles = mem.get('roles') or []
                character = ", ".join(r.get('character') or 'unknown' for r in roles) or 'unknown'
            else:
                character = mem.get('character', 'unknown')
            output.append(f"Actor: {name} | Character: {character}")

        final = "\n".join(output)
        return final
    except Exception as e:
        print(f"[get_cast] error: {e}")
        # [Claude Code] Was `return ""`: an empty tool result gives the model nothing to
        # reason about, so it would hallucinate a cast. Now matches the other tools.
        return f"Unable to retrieve cast.\nReason: {e}"

@tool
def get_crew(media_name: str, media_type: Literal['movie', 'tv']) -> str:
    """Get the crew of the media by its name and type.

    Args:
        media_name (str): The name of the media.
        media_type (str): The type of the media.

    Returns:
        str: A list of crew members.
    """

    try:
        # Get the media ID
        media_id = resolve_media_id(media_name, media_type)

        # Fetch crew for the specified media
        crew_members = get_media_credits(media_type, media_id)
        crew_list = crew_members.get('crew', [])
        if media_type == "movie":
            directors = [m for m in crew_list if m.get("job") == "Director"]
        else:
            # [Claude Code] TV uses the aggregate_credits endpoint, where crew members
            # carry a "jobs" list instead of a top-level "job" field — the old filter
            # matched nothing, so TV crew results were always empty.
            tv_jobs = {"Creator", "Executive Producer", "Series Director"}
            directors = [
                m for m in crew_list
                if any(j.get("job") in tv_jobs for j in (m.get("jobs") or []))
            ]

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
        return f"Unable to retrieve crew.\nReason: {e}"


# test = find_media("Game of thrones", "tv")
# print(test)
# test = get_media_summary(
#     "Rango",
#     "movie",
# )
# print(test)
