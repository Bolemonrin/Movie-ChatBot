"""Raw HTTP client for the TMDB REST API.

This is the only module that talks to the network. Every function here maps 1:1
onto a TMDB endpoint, returns plain parsed JSON, and never raises: request errors
are logged and swallowed so callers always get an empty value of the right type
({} for the detail endpoints, [] for search) instead of a crash.

Interpretation and formatting of this data belongs one layer up, in the agent
tools -- nothing in this file knows about the LLM.
"""
import os
from dotenv import load_dotenv
import requests

load_dotenv()

TMDB_ACCESS_TOKEN = os.getenv("TMDB_ACCESS_TOKEN")
# os.getenv("TMDB_API_KEY")

BASE_URL = 'https://api.themoviedb.org/3'
HEADERS = {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_ACCESS_TOKEN}"
    }

def search_for_media(media_name: str, media_type: str, page: int=1):
    url = f'{BASE_URL}/search/{media_type}'
    params = {
        'query': media_name,
        'include_adult': True,
        'language': 'en-US',
        'page': page
    }

    try:
        # [Claude Code] Added timeout=10 to every request in this file: without it, one
        # stalled TMDB call would hang the agent forever.
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
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
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # log the error
        print(f"[TMDB] get_details error: {e}")
        # [Claude Code] Was `return []`: success returns a dict, so callers doing
        # .get(...) crashed with "'list' object has no attribute 'get'" whenever TMDB
        # failed. Same fix applied to the other dict-returning functions below.
        return {}

def get_recommendations(media_type: str, media_id: int, page: int=1):
    url = f'{BASE_URL}/{media_type}/{media_id}/recommendations'
    params = {
        'language': 'en-US',
        'page': page
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # log the error
        print(f"[TMDB] get_recommendations error: {e}")
        return {}


def get_similar(media_type: str, media_id: int, page: int = 1):
    url = f'{BASE_URL}/{media_type}/{media_id}/similar'
    params = {
        'language': 'en-US',
        'page': page
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # log the error
        print(f"[TMDB] get_similar error: {e}")
        return {}


def get_media_credits(media_type: str, media_id: int):
    url = f"{BASE_URL}/{media_type}/{media_id}/{'credits' if media_type == 'movie' else 'aggregate_credits'}"
    params = {
        'language': 'en-US'
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # log the error
        print(f"[TMDB] get_media_credits error: {e}")
        return {}
