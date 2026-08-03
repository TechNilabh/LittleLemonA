import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .cf_client import get_user_info, get_user_rating, get_user_submissions, process_cp_stats, CFError
from .models import UserCache

def index_view(request):
    if request.method == 'POST':
        handle = request.POST.get('handle', '').strip()
        if handle:
            return redirect('dashboard', handle=handle)
    return render(request, 'index.html')

def dashboard_view(request, handle):
    handle = handle.strip()
    error_msg = None
    stats = None

    try:
        # Check database cache first (expire after 10 minutes if needed, or simple cache)
        cache_obj = UserCache.objects.filter(handle__iexact=handle).first()
        if cache_obj:
            profile = json.loads(cache_obj.profile_json)
            ratings = json.loads(cache_obj.rating_json)
            submissions = json.loads(cache_obj.submissions_json)
        else:
            profile = get_user_info(handle)
            ratings = get_user_rating(handle)
            submissions = get_user_submissions(handle)
            
            # Save to cache
            UserCache.objects.update_or_create(
                handle=profile.get('handle', handle),
                defaults={
                    'profile_json': json.dumps(profile),
                    'rating_json': json.dumps(ratings),
                    'submissions_json': json.dumps(submissions),
                }
            )

        stats = process_cp_stats(profile, ratings, submissions)
    except CFError as e:
        error_msg = str(e)
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"

    context = {
        'handle': handle,
        'error': error_msg,
        'stats': stats
    }
    return render(request, 'dashboard.html', context)

def api_stats_view(request, handle):
    try:
        cache_obj = UserCache.objects.filter(handle__iexact=handle).first()
        if cache_obj:
            profile = json.loads(cache_obj.profile_json)
            ratings = json.loads(cache_obj.rating_json)
            submissions = json.loads(cache_obj.submissions_json)
        else:
            profile = get_user_info(handle)
            ratings = get_user_rating(handle)
            submissions = get_user_submissions(handle)

        stats = process_cp_stats(profile, ratings, submissions)
        return JsonResponse({'status': 'success', 'data': stats})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
