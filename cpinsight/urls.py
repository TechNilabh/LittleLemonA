from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('dashboard/<str:handle>/', views.dashboard_view, name='dashboard'),
    path('api/stats/<str:handle>/', views.api_stats_view, name='api_stats'),
]
