from django.db import models
from django.utils import timezone
from datetime import timedelta


class UserCache(models.Model):
    handle = models.CharField(max_length=100, unique=True)
    fetched_at = models.DateTimeField(auto_now=True)
    profile_json = models.TextField()
    submissions_json = models.TextField()
    rating_json = models.TextField()

    def __str__(self):
        return self.handle

    def is_stale(self, ttl_minutes: int = 10) -> bool:
        """Returns True if the cached data is older than ttl_minutes."""
        return timezone.now() - self.fetched_at > timedelta(minutes=ttl_minutes)
