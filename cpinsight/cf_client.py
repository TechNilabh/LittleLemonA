"""
Thin wrapper around the public Codeforces API.
Uses `requests` with a 5-second timeout.
Raises plain Exception with a readable message on any failure.
"""
import requests

CF_BASE_URL = "https://codeforces.com/api"
TIMEOUT = 5


def _get(url: str):
    """Internal helper: fetch CF API URL, return result list/dict or raise."""
    try:
        resp = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": "CPInsight/1.0"})
        data = resp.json()
    except requests.exceptions.Timeout:
        raise Exception("Codeforces API timed out. Try again in a moment.")
    except Exception as exc:
        raise Exception(f"Network error while contacting Codeforces: {exc}")

    if data.get("status") != "OK":
        comment = data.get("comment", "Unknown error from Codeforces API.")
        raise Exception(f"Codeforces API error: {comment}")

    return data["result"]


def get_user_info(handle: str) -> dict:
    """Return a single user's profile dict or raise on bad handle."""
    result = _get(f"{CF_BASE_URL}/user.info?handles={handle}")
    if not result:
        raise Exception(f"No user found for handle '{handle}'.")
    return result[0]


def get_user_rating(handle: str) -> list:
    """Return list of rating change dicts; returns [] if user has no contests."""
    try:
        return _get(f"{CF_BASE_URL}/user.rating?handle={handle}")
    except Exception:
        return []


def get_user_submissions(handle: str, count: int = 500) -> list:
    """Return list of submission dicts (up to `count`); returns [] on error."""
    try:
        return _get(f"{CF_BASE_URL}/user.status?handle={handle}&from=1&count={count}")
    except Exception:
        return []
