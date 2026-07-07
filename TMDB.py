import os
from dotenv import load_dotenv
import requests
from difflib import SequenceMatcher

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_ACCESS_TOKEN")
# os.getenv("TMDB_API_KEY")

BASE_URL = 'https://api.themoviedb.org/3'
HEADERS = {
        "accept": "application",
        "Authorization": f"Bearer {TMDB_API_KEY}"
    }

def search_for_media(media_name: str, media_type: str, page: int=1):
    url = url = f'{BASE_URL}/search/{media_type}'
    params = {
        'query': media_name,
        'include_adult': True,
        'language': 'en-US',
        'page': page
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json().get('results', [])
    except requests.exceptions.RequestException as e:
        # log the error
        print(f"[TMDB] search_for_media error: {e}")
        return []


def get_details(media_type: str, media_id: int):
    url = f'{BASE_URL}/{media_type}/{media_id}'
    params = {
        'language': 'en-US'
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # log the error
        print(f"[TMDB] get_details error: {e}")
        return []

def get_recommendations(media_type: str, media_id: int, page: int=1):
    url = f'{BASE_URL}/{media_type}/{media_id}/recommendations'
    params = {
        'language': 'en-US',
        'page': page
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # log the error
        print(f"[TMDB] get_recommendations error: {e}")
        return []


def get_similar(media_type: str, media_id: int, page: int = 1):
    url = f'{BASE_URL}/{media_type}/{media_id}/similar'
    params = {
        'language': 'en-US',
        'page': page
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # log the error
        print(f"[TMDB] get_similar error: {e}")
        return []


def get_media_credits(media_type: str, media_id: int):
    url = f"{BASE_URL}/{media_type}/{media_id}/{'credits' if media_type == 'movie' else 'aggregate_credits'}"
    params = {
        'language': 'en-US'
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # log the error
        print(f"[TMDB] get_media_credits error: {e}")
        return []


# type = 'tv'
# id = 78191
# credits = get_media_credits(type, id)
# print(credits)
# recommendations = get_recommendations("movie", 24428)
# for rec in recommendations['results']:
#     title = rec.get('title')
#     overview = rec.get('overview')
#     id = rec.get('id')
#     background = rec.get('backdrop_path')
#     print(f'Media ID: {id}\nTitle: {title}\nOverview: {overview}\nBackdrop: {background}\n')
# print(recommendations)
