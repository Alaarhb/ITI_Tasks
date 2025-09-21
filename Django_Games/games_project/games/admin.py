from django.contrib import admin
from .models import GameScore

@admin.register(GameScore)
class GameScoreAdmin(admin.ModelAdmin):
    list_display = ('player_name', 'game_type', 'score', 'attempts', 'created_at')
    list_filter = ('game_type', 'created_at')
    search_fields = ('player_name', 'game_type')
    ordering = ('-score', '-created_at')
