"""Tests for the raw TMDB client in TMDB.py.

HTTP is mocked with unittest.mock, so no network or API key is needed. One live
smoke test at the bottom runs only when TMDB_ACCESS_TOKEN is set.

Note: the old version of this file expected search_for_media to *raise* on bad
input — but the client deliberately swallows request errors and returns an empty
value so the agent gets a string it can reason about instead of a crash. The
tests below assert that contract.
"""
import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from TMDB import (
    search_for_media,
    get_details,
    get_recommendations,
    get_similar,
    get_media_credits,
)


def _fake_response(json_data, status=200):
    resp = MagicMock()
    resp.json.return_value = json_data
    if status >= 400:
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(f"HTTP {status}")
    else:
        resp.raise_for_status.return_value = None
    return resp


# ---------- success paths ----------

def test_search_returns_result_list():
    payload = {"results": [{"id": 603, "title": "The Matrix"}]}
    with patch("TMDB.requests.get", return_value=_fake_response(payload)):
        results = search_for_media("The Matrix", "movie")
    assert results == payload["results"]


def test_get_details_returns_dict():
    payload = {"id": 603, "title": "The Matrix", "overview": "..."}
    with patch("TMDB.requests.get", return_value=_fake_response(payload)):
        details = get_details("movie", 603)
    assert details["title"] == "The Matrix"


def test_credits_endpoint_switches_for_tv():
    """Movies use /credits; TV must use /aggregate_credits."""
    with patch("TMDB.requests.get", return_value=_fake_response({"cast": []})) as mock_get:
        get_media_credits("movie", 603)
        get_media_credits("tv", 1399)

    movie_url = mock_get.call_args_list[0].args[0]
    tv_url = mock_get.call_args_list[1].args[0]
    assert movie_url.endswith("/movie/603/credits")
    assert tv_url.endswith("/tv/1399/aggregate_credits")


def test_requests_send_a_timeout():
    """Without a timeout, one stalled TMDB call hangs the whole agent."""
    with patch("TMDB.requests.get", return_value=_fake_response({"results": []})) as mock_get:
        search_for_media("The Matrix", "movie")
    assert mock_get.call_args.kwargs.get("timeout") == 10


# ---------- error paths: swallowed, and the right empty type ----------

def test_search_error_returns_empty_list():
    with patch("TMDB.requests.get", return_value=_fake_response({}, status=404)):
        assert search_for_media("The Matrix", "invalid_media_type") == []


@pytest.mark.parametrize("func,args", [
    (get_details, ("movie", 0)),
    (get_recommendations, ("movie", 0)),
    (get_similar, ("movie", 0)),
    (get_media_credits, ("movie", 0)),
])
def test_dict_functions_return_empty_dict_on_error(func, args):
    """These return dicts on success, so their error value must be {} — returning []
    made callers crash with "'list' object has no attribute 'get'"."""
    with patch("TMDB.requests.get", return_value=_fake_response({}, status=404)):
        assert func(*args) == {}


def test_network_exception_is_swallowed():
    with patch("TMDB.requests.get", side_effect=requests.exceptions.ConnectionError("down")):
        assert search_for_media("The Matrix", "movie") == []
        assert get_details("movie", 603) == {}


# ---------- live smoke test (only with a real token) ----------

@pytest.mark.skipif(not os.getenv("TMDB_ACCESS_TOKEN"), reason="TMDB_ACCESS_TOKEN not set")
def test_live_search_smoke():
    results = search_for_media("The Matrix", "movie")
    titles = [r.get("title", "") for r in results]
    assert any("Matrix" in t for t in titles)
