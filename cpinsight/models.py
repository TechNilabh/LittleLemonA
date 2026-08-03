from django.db import models

class UserCache(models.Model):
    handle = models.CharField(max_length=100, unique=True)
    fetched_at = models.DateTimeField(auto_now=True)
    profile_json = models.TextField()
    submissions_json = models.TextField()
    rating_json = models.TextField()

    def __str__(self):
        return self.handle
