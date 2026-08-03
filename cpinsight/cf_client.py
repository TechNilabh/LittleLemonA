import json
import urllib.request
import urllib.error
from datetime import datetime

CF_BASE_URL = "https://codeforces.com/api"

class CFError(Exception):
    pass

def _fetch_json(url):
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'CPInsight-Django/1.0'}
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('status') == 'OK':
                return data.get('result')
            else:
                raise CFError(data.get('comment', 'Failed to fetch data from Codeforces.'))
    except urllib.error.HTTPError as e:
        if e.code == 400:
            raise CFError("Handle not found or invalid.")
        raise CFError(f"HTTP Error {e.code} while connecting to Codeforces.")
    except Exception as e:
        raise CFError(f"Network error: {str(e)}")

def get_user_info(handle):
    url = f"{CF_BASE_URL}/user.info?handles={handle}"
    res = _fetch_json(url)
    if res and len(res) > 0:
        return res[0]
    raise CFError("User info not found.")

def get_user_rating(handle):
    url = f"{CF_BASE_URL}/user.rating?handle={handle}"
    try:
        return _fetch_json(url)
    except CFError:
        return []

def get_user_submissions(handle, count=500):
    url = f"{CF_BASE_URL}/user.status?handle={handle}&from=1&count={count}"
    try:
        return _fetch_json(url)
    except CFError:
        return []

def process_cp_stats(profile, ratings, submissions):
    """
    Computes processed stats like tag frequencies, difficulty distribution,
    rank styling info, and formatted submission history.
    """
    # 1. Rank color & name
    rank = profile.get('rank', 'unrated').lower()
    max_rank = profile.get('maxRank', 'unrated').lower()
    
    # 2. Rating history for Chart.js
    rating_labels = []
    rating_values = []
    for r in ratings:
        dt = datetime.fromtimestamp(r['ratingUpdateTimeSeconds'])
        rating_labels.append(dt.strftime('%b %Y'))
        rating_values.append(r['newRating'])

    # 3. Tag stats & Difficulty stats
    tag_counts = {}
    diff_buckets = {'<1200': 0, '1200-1500': 0, '1500-1800': 0, '1800-2100': 0, '2100+': 0}
    solved_problems = set()
    recent_subs = []

    for sub in submissions:
        verdict = sub.get('verdict', 'UNKNOWN')
        problem = sub.get('problem', {})
        p_name = problem.get('name', 'Unknown')
        p_index = problem.get('index', '')
        contest_id = problem.get('contestId', '')
        p_id = f"{contest_id}{p_index}"
        rating = problem.get('rating')
        tags = problem.get('tags', [])
        creation_time = datetime.fromtimestamp(sub.get('creationTimeSeconds', 0)).strftime('%b %d, %H:%M')

        if verdict == 'OK' and p_id not in solved_problems:
            solved_problems.add(p_id)
            # Tags count
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            # Rating buckets
            if rating:
                if rating < 1200:
                    diff_buckets['<1200'] += 1
                elif rating < 1500:
                    diff_buckets['1200-1500'] += 1
                elif rating < 1800:
                    diff_buckets['1500-1800'] += 1
                elif rating < 2100:
                    diff_buckets['1800-2100'] += 1
                else:
                    diff_buckets['2100+'] += 1

        if len(recent_subs) < 15:
            recent_subs.append({
                'problem_name': p_name,
                'problem_code': p_id,
                'problem_url': f"https://codeforces.com/problemset/problem/{contest_id}/{p_index}" if contest_id else "#",
                'tags': ", ".join(tags[:3]) if tags else "N/A",
                'verdict': verdict,
                'verdict_short': 'AC' if verdict == 'OK' else ('WA' if verdict == 'WRONG_ANSWER' else ('TLE' if verdict == 'TIME_LIMIT_EXCEEDED' else verdict[:4])),
                'when': creation_time,
            })

    # Top tags sorted
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    tag_labels = [t[0] for t in sorted_tags]
    tag_values = [t[1] for t in sorted_tags]

    return {
        'handle': profile.get('handle'),
        'rating': profile.get('rating', 0),
        'max_rating': profile.get('maxRating', 0),
        'rank': profile.get('rank', 'Unrated').title(),
        'max_rank': profile.get('maxRank', 'Unrated').title(),
        'avatar': profile.get('titlePhoto', 'https://userpic.codeforces.org/no-title.jpg'),
        'country': profile.get('country', 'Global'),
        'organization': profile.get('organization', 'N/A'),
        'contribution': profile.get('contribution', 0),
        'friend_of_count': profile.get('friendOfCount', 0),
        'rating_labels_json': json.dumps(rating_labels),
        'rating_values_json': json.dumps(rating_values),
        'tag_labels_json': json.dumps(tag_labels),
        'tag_values_json': json.dumps(tag_values),
        'diff_labels_json': json.dumps(list(diff_buckets.keys())),
        'diff_values_json': json.dumps(list(diff_buckets.values())),
        'recent_submissions': recent_subs,
        'total_solved': len(solved_problems)
    }
