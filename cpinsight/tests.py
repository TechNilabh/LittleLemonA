"""
Smoke tests for the cpinsight app.
All Codeforces API calls are mocked so no real network requests are made.
"""
import json
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse

# ---------------------------------------------------------------------------
# Shared fake API payloads
# ---------------------------------------------------------------------------

FAKE_PROFILE = {
    "handle": "tourist",
    "rating": 3805,
    "maxRating": 3979,
    "rank": "legendary grandmaster",
    "maxRank": "legendary grandmaster",
    "titlePhoto": "https://userpic.codeforces.org/no-title.jpg",
    "country": "Belarus",
    "organization": "ITMO",
    "contribution": 82,
    "friendOfCount": 99999,
}

FAKE_RATINGS = [
    {"ratingUpdateTimeSeconds": 1609459200, "newRating": 3500, "oldRating": 3400},
    {"ratingUpdateTimeSeconds": 1612137600, "newRating": 3805, "oldRating": 3500},
]

FAKE_SUBMISSIONS = [
    {
        "verdict": "OK",
        "creationTimeSeconds": 1612137600,
        "problem": {
            "contestId": 1,
            "index": "A",
            "name": "Way Too Long Words",
            "rating": 800,
            "tags": ["strings"],
        },
    },
    {
        "verdict": "WRONG_ANSWER",
        "creationTimeSeconds": 1612137700,
        "problem": {
            "contestId": 2,
            "index": "B",
            "name": "Hard Problem",
            "rating": 2000,
            "tags": ["dp", "graphs"],
        },
    },
]


def _patch_cf(info=None, ratings=None, submissions=None):
    """
    Returns a context-manager that patches all three cf_client functions.
    Defaults to fake data; pass an Exception instance to simulate a failure.
    """
    def _side_effect(exc):
        def _raise(*a, **kw):
            raise exc
        return _raise

    info_mock = MagicMock(
        side_effect=_side_effect(info) if isinstance(info, Exception) else None,
        return_value=info if not isinstance(info, Exception) else None,
    )
    if isinstance(info, Exception):
        info_mock = MagicMock(side_effect=info)
    else:
        info_mock = MagicMock(return_value=info or FAKE_PROFILE)

    rating_mock = MagicMock(return_value=ratings if ratings is not None else FAKE_RATINGS)
    subs_mock   = MagicMock(return_value=submissions if submissions is not None else FAKE_SUBMISSIONS)

    return patch.multiple(
        "cpinsight.views",
        get_user_info=info_mock,
        get_user_rating=rating_mock,
        get_user_submissions=subs_mock,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class HomeViewTest(TestCase):
    def test_home_returns_200(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Know your")


class DashboardViewValidHandleTest(TestCase):
    def test_valid_handle_returns_200_with_stats(self):
        with _patch_cf():
            response = self.client.get(reverse("dashboard", kwargs={"handle": "tourist"}))

        self.assertEqual(response.status_code, 200)
        # No error message rendered
        self.assertNotContains(response, "ERROR")
        # Core data points appear on the page
        self.assertContains(response, "tourist")
        self.assertContains(response, "3805")


class DashboardViewInvalidHandleTest(TestCase):
    def test_invalid_handle_returns_200_with_error(self):
        bad_exc = Exception("Codeforces API error: handles: User with handle badhandle### not found")
        with _patch_cf(info=bad_exc):
            response = self.client.get(reverse("dashboard", kwargs={"handle": "badhandle###"}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "badhandle###")
        # The template renders an error block when context["error"] is set
        self.assertTrue(response.context["error"])


class ApiStatsViewTest(TestCase):
    def test_api_stats_valid_handle(self):
        with _patch_cf():
            response = self.client.get(reverse("api_stats", kwargs={"handle": "tourist"}))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("data", data)
        self.assertEqual(data["data"]["handle"], "tourist")

    def test_api_stats_invalid_handle_returns_400(self):
        bad_exc = Exception("Codeforces API error: handles: User not found")
        with _patch_cf(info=bad_exc):
            response = self.client.get(reverse("api_stats", kwargs={"handle": "??invalid??"}))

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["status"], "error")
