from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="index"),
    path("dashboard/<str:handle>/", views.dashboard, name="dashboard"),
    path("api/stats/<str:handle>/", views.api_stats, name="api_stats"),
]
