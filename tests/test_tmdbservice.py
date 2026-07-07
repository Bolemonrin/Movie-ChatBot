import pytest
import requests
from TMDB import search_for_media


def test_search_for_media():
    # Test with a known media name
    results = search_for_media("The Matrix", "movie")
    assert len(results) > 0

    # Test with a non-existent media name
    results = search_for_media("NonExistentMedia", "movie")
    assert len(results) == 0

    # Test with a different media type
    results = search_for_media("Breaking Bad", "tv_show")
    assert len(results) > 0

    # Test with a page number
    results = search_for_media("The Matrix", "movie", page=2)
    assert len(results) > 0

    # Test with invalid parameters
    with pytest.raises(requests.exceptions.RequestException):
        search_for_media("The Matrix", "invalid_media_type")
