from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('games/admin/', admin.site.urls),
    path('', include('games.Urls')),
]

