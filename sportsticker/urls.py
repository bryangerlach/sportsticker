from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Route the root URL directly to your scores dashboard
    path('', include('scores.urls')),
]