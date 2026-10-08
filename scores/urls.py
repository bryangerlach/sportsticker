from django.urls import path
from . import views

app_name = 'scores'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('team/<slug:team_slug>/', views.team_detail_view, name='team_detail'),
    path('standings/<str:league>/', views.standings_view, name='standings'),
]