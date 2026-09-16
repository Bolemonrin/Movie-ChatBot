"""Superseded and BROKEN, kept for reference only.

A manual print-based check (not a pytest test, despite its original name
test_tools.py) for a clarify_for_ambiguity helper that no longer exists on any
branch — so the import on the first line fails. It also ran its checks at import
time rather than under a __main__ guard.

Renamed off the test_ prefix so pytest and IDE test discovery stop trying to
collect it. The real tool tests are in tests/test_tools.py.
"""
from tools import clarify_for_ambiguity

# --- Mock find_cast so it doesn't make API calls ---
def find_cast(actor, media_type, media_id):
    return "mocked actor"

# Inject mock into the global scope for the test
globals()['find_cast'] = find_cast

def test_clarify_no_error():
    results = [
        {"title": "Iron Man", "release_date": "2008-05-02", "id": 1726},
        {"title": "Iron Man 2", "release_date": "2010-05-07", "id": 10138},
    ]
    clarification = {"year": 2010}

    result = clarify_for_ambiguity(results, clarification)
    print("✅ No error test result:", result)


def test_clarify_with_keyerror():
    results = [
        {"name": "Loki", "first_air_date": "2021-06-09", "id": 84958},  # TV show
        {"name": "Hawkeye", "id": 88329},  # Missing both date keys
    ]
    clarification = {"year": 2021}

    try:
        result = clarify_for_ambiguity(results, clarification)
        print("❌ Expected crash but got:", result)
    except KeyError as e:
        print("💥 Caught KeyError:", e)

test_clarify_no_error()
test_clarify_with_keyerror()