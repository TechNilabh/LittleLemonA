import json
from datetime import datetime

from django.shortcuts import render, redirect
from django.http import JsonResponse

from .cf_client import get_user_info, get_user_rating, get_user_submissions
from .models import UserCache


# Make CF client functions importable by name in views module scope
# (used by patch.multiple in tests)
__all__ = ["home", "dashboard", "api_stats", "get_user_info", "get_user_rating", "get_user_submissions"]


# ---------------------------------------------------------------------------
# Stat computation (lives here, not in cf_client)
# ---------------------------------------------------------------------------

def _compute_stats(profile: dict, ratings: list, submissions: list) -> dict:
    """
    Derive all analytics from raw CF API data.
    Returns a dict ready to be passed directly to the template context.
    """
    # -- Rating history -------------------------------------------------------
    rating_labels = []
    rating_values = []
    for r in ratings:
        dt = datetime.utcfromtimestamp(r["ratingUpdateTimeSeconds"])
        rating_labels.append(dt.strftime("%b %Y"))
        rating_values.append(r["newRating"])

    # -- Tag counts & difficulty buckets (over unique solved problems only) ---
    tag_counts: dict[str, int] = {}
    diff_buckets = {
        "<1200": 0,
        "1200-1599": 0,
        "1600-1999": 0,
        "2000-2399": 0,
        "2400+": 0,
    }
    solved_ids: set[str] = set()
    recent_submissions = []

    for sub in submissions:
        verdict = sub.get("verdict", "")
        problem = sub.get("problem", {})
        contest_id = problem.get("contestId", "")
        p_index = problem.get("index", "")
        p_id = f"{contest_id}{p_index}"
        p_name = problem.get("name", "Unknown")
        p_rating = problem.get("rating")
        tags = problem.get("tags", [])
        created_ts = sub.get("creationTimeSeconds", 0)
        when = datetime.utcfromtimestamp(created_ts).strftime("%b %d, %H:%M")

        # Unique AC → count tags & difficulty
        if verdict == "OK" and p_id not in solved_ids:
            solved_ids.add(p_id)
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            if p_rating is not None:
                if p_rating < 1200:
                    diff_buckets["<1200"] += 1
                elif p_rating < 1600:
                    diff_buckets["1200-1599"] += 1
                elif p_rating < 2000:
                    diff_buckets["1600-1999"] += 1
                elif p_rating < 2400:
                    diff_buckets["2000-2399"] += 1
                else:
                    diff_buckets["2400+"] += 1

        # Last 20 submissions (all verdicts)
        if len(recent_submissions) < 20:
            if verdict == "OK":
                verdict_short = "AC"
            elif verdict == "WRONG_ANSWER":
                verdict_short = "WA"
            elif verdict == "TIME_LIMIT_EXCEEDED":
                verdict_short = "TLE"
            elif verdict == "RUNTIME_ERROR":
                verdict_short = "RE"
            elif verdict == "COMPILATION_ERROR":
                verdict_short = "CE"
            else:
                verdict_short = verdict[:4] if verdict else "?"

            p_url = (
                f"https://codeforces.com/problemset/problem/{contest_id}/{p_index}"
                if contest_id else "#"
            )
            recent_submissions.append({
                "problem_name": p_name,
                "problem_code": p_id,
                "problem_url": p_url,
                "tags": ", ".join(tags[:3]) if tags else "—",
                "verdict": verdict,
                "verdict_short": verdict_short,
                "when": when,
            })

    # Top-8 tags by frequency
    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    tag_labels = [t[0] for t in top_tags]
    tag_values = [t[1] for t in top_tags]

    return {
        "handle": profile.get("handle"),
        "rating": profile.get("rating", 0),
        "max_rating": profile.get("maxRating", 0),
        "rank": (profile.get("rank") or "Unrated").title(),
        "max_rank": (profile.get("maxRank") or "Unrated").title(),
        "avatar": profile.get("titlePhoto", "https://userpic.codeforces.org/no-title.jpg"),
        "country": profile.get("country") or "—",
        "organization": profile.get("organization") or "—",
        "contribution": profile.get("contribution", 0),
        "total_solved": len(solved_ids),
        # JSON strings for Chart.js data-* attributes
        "rating_labels_json": json.dumps(rating_labels),
        "rating_values_json": json.dumps(rating_values),
        "tag_labels_json": json.dumps(tag_labels),
        "tag_values_json": json.dumps(tag_values),
        "diff_labels_json": json.dumps(list(diff_buckets.keys())),
        "diff_values_json": json.dumps(list(diff_buckets.values())),
        "recent_submissions": recent_submissions,
    }


def _fetch_and_cache(handle: str) -> tuple[dict, list, list]:
    """Fetch from CF API and upsert into UserCache. Returns (profile, ratings, submissions)."""
    profile = get_user_info(handle)
    ratings = get_user_rating(handle)
    submissions = get_user_submissions(handle)

    UserCache.objects.update_or_create(
        handle=profile["handle"],
        defaults={
            "profile_json": json.dumps(profile),
            "rating_json": json.dumps(ratings),
            "submissions_json": json.dumps(submissions),
        },
    )
    return profile, ratings, submissions


def _load_from_cache(cache_obj: UserCache) -> tuple[dict, list, list]:
    return (
        json.loads(cache_obj.profile_json),
        json.loads(cache_obj.rating_json),
        json.loads(cache_obj.submissions_json),
    )


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

def home(request):
    """GET+POST / — renders landing page; POST redirects to dashboard."""
    if request.method == "POST":
        handle = request.POST.get("handle", "").strip()
        if handle:
            return redirect("dashboard", handle=handle)
    return render(request, "index.html")


def dashboard(request, handle: str):
    """GET /dashboard/<handle>/ — profile + charts + submissions."""
    handle = handle.strip()
    error = None
    stats = None

    try:
        cache_obj = UserCache.objects.filter(handle__iexact=handle).first()
        if cache_obj and not cache_obj.is_stale():
            profile, ratings, submissions = _load_from_cache(cache_obj)
        else:
            profile, ratings, submissions = _fetch_and_cache(handle)

        stats = _compute_stats(profile, ratings, submissions)

    except Exception as exc:
        error = str(exc)

    return render(request, "dashboard.html", {
        "handle": handle,
        "error": error,
        "stats": stats,
    })


def api_stats(request, handle: str):
    """GET /api/stats/<handle>/ — same computed stats as JSON (for Streamlit)."""
    handle = handle.strip()
    try:
        cache_obj = UserCache.objects.filter(handle__iexact=handle).first()
        if cache_obj and not cache_obj.is_stale():
            profile, ratings, submissions = _load_from_cache(cache_obj)
        else:
            profile, ratings, submissions = _fetch_and_cache(handle)

        stats = _compute_stats(profile, ratings, submissions)
        # recent_submissions contains dicts — already JSON-serialisable
        return JsonResponse({"status": "ok", "data": stats})

    except Exception as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
