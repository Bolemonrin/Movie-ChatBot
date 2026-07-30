"""Unit tests for the agent tools in tools.py.

All TMDB network calls are mocked (patched inside the `tools` module namespace,
since tools.py does `from TMDB import *`), so these tests run offline and never
touch the real API.
"""
import pytest
from unittest.mock import patch

from tools import (
    get_media_id,
    resolve_media_id,
    find_media,
    get_media_summary,
    get_cast,
    get_crew,
)

# Canned TMDB search results, shaped like the real /search response items.
MOVIE_RESULTS = [
    {"id": 68718, "title": "Django Unchained", "release_date": "2012-12-25",
     "vote_average": 8.2, "popularity": 50.0},
    {"id": 10772, "title": "Django", "release_date": "1966-04-01",
     "vote_average": 7.2, "popularity": 10.0},
]


# ---------- get_media_id / resolve_media_id ----------

def test_get_media_id_exact_match_is_case_insensitive():
    with patch("tools.search_for_media", return_value=MOVIE_RESULTS):
        assert get_media_id("DJANGO UNCHAINED") == 68718
        assert get_media_id("django unchained") == 68718


def test_get_media_id_falls_back_to_first_result():
    """No exact title match -> first (most relevant) search result wins."""
    with patch("tools.search_for_media", return_value=MOVIE_RESULTS):
        assert get_media_id("django movie thing") == 68718


def test_get_media_id_returns_none_when_no_results():
    with patch("tools.search_for_media", return_value=[]):
        assert get_media_id("does not exist") is None


def test_resolve_media_id_raises_for_unknown_title():
    """Must raise (not return 0) so tools can report 'not found' to the model."""
    with patch("tools.search_for_media", return_value=[]):
        with pytest.raises(ValueError, match="No movie found"):
            resolve_media_id("does not exist", "movie")


# ---------- find_media ----------

def test_find_media_formats_results():
    with patch("tools.search_for_media", return_value=MOVIE_RESULTS):
        out = find_media.invoke({"media_name": "django", "media_type": "movie"})
    assert "ID: 68718" in out
    assert "Title: Django Unchained" in out
    assert "Year: 2012" in out


def test_find_media_schema_rejects_alias_media_types():
    """The Literal['movie', 'tv'] schema validates BEFORE the function body runs, so
    aliases like 'film' are rejected at the tool boundary — the model is forced to
    send an exact value (the MEDIA_ALIASES fallback only applies to direct calls)."""
    with pytest.raises(Exception, match="movie.*tv|literal"):
        find_media.invoke({"media_name": "django", "media_type": "film"})


def test_find_media_aliases_still_work_for_direct_calls():
    with patch("tools.search_for_media", return_value=MOVIE_RESULTS) as mock_search:
        find_media.func("django", "film")
    mock_search.assert_called_once_with("django", "movie")


def test_find_media_reports_no_results():
    with patch("tools.search_for_media", return_value=[]):
        out = find_media.invoke({"media_name": "zzz", "media_type": "movie"})
    assert "No movie results found" in out


# ---------- get_media_summary ----------

def test_get_media_summary_returns_title_and_overview():
    details = {"id": 68718, "title": "Django Unchained",
               "overview": "A freed slave sets out to rescue his wife."}
    with patch("tools.search_for_media", return_value=MOVIE_RESULTS), \
         patch("tools.get_details", return_value=details):
        out = get_media_summary.invoke({"media_name": "Django Unchained", "media_type": "movie"})
    assert "Django Unchained" in out
    assert "rescue his wife" in out


def test_get_media_summary_unknown_title_returns_readable_error():
    """The model must receive a 'not found' message it can act on, not a crash."""
    with patch("tools.search_for_media", return_value=[]):
        out = get_media_summary.invoke({"media_name": "zzz", "media_type": "movie"})
    assert "Unable to retrieve summary" in out
    assert "No movie found" in out


# ---------- get_cast ----------

def test_get_cast_movie_uses_character_field():
    credits = {"cast": [{"name": "Jamie Foxx", "character": "Django"}]}
    with patch("tools.search_for_media", return_value=MOVIE_RESULTS), \
         patch("tools.get_media_credits", return_value=credits):
        out = get_cast.invoke({"media_name": "Django Unchained", "media_type": "movie"})
    assert "Actor: Jamie Foxx | Character: Django" in out


def test_get_cast_tv_uses_roles_list():
    """aggregate_credits (TV) nests characters in a 'roles' list, not 'character'."""
    credits = {"cast": [{"name": "Peter Dinklage",
                         "roles": [{"character": "Tyrion Lannister"}]}]}
    tv_results = [{"id": 1399, "name": "Game of Thrones", "first_air_date": "2011-04-17"}]
    with patch("tools.search_for_media", return_value=tv_results), \
         patch("tools.get_media_credits", return_value=credits):
        out = get_cast.invoke({"media_name": "Game of Thrones", "media_type": "tv"})
    assert "Tyrion Lannister" in out
    assert "unknown" not in out


def test_get_cast_error_returns_message_not_empty_string():
    with patch("tools.search_for_media", return_value=[]):
        out = get_cast.invoke({"media_name": "zzz", "media_type": "movie"})
    assert out != ""
    assert "Unable to retrieve cast" in out


# ---------- get_crew ----------

def test_get_crew_movie_filters_directors():
    credits = {"crew": [
        {"name": "Quentin Tarantino", "job": "Director", "popularity": 9.0},
        {"name": "Someone Else", "job": "Producer", "popularity": 5.0},
    ]}
    with patch("tools.search_for_media", return_value=MOVIE_RESULTS), \
         patch("tools.get_media_credits", return_value=credits):
        out = get_crew.invoke({"media_name": "Django Unchained", "media_type": "movie"})
    assert "Quentin Tarantino" in out
    assert "Someone Else" not in out


def test_get_crew_tv_uses_jobs_list():
    """aggregate_credits (TV) nests jobs in a 'jobs' list, not a top-level 'job'."""
    credits = {"crew": [
        {"name": "David Benioff", "jobs": [{"job": "Executive Producer"}], "popularity": 8.0},
        {"name": "Random Grip", "jobs": [{"job": "Grip"}], "popularity": 1.0},
    ]}
    tv_results = [{"id": 1399, "name": "Game of Thrones", "first_air_date": "2011-04-17"}]
    with patch("tools.search_for_media", return_value=tv_results), \
         patch("tools.get_media_credits", return_value=credits):
        out = get_crew.invoke({"media_name": "Game of Thrones", "media_type": "tv"})
    assert "David Benioff" in out
    assert "Random Grip" not in out
