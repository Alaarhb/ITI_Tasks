
from django.db import models
from django.utils import timezone
from datetime import timedelta

class ActiveManager(models.Manager):
    """Manager for active objects only"""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class GameManager(models.Manager):
    """Custom manager for Game model"""
    def featured(self):
        return self.filter(is_featured=True, is_active=True)
    
    def by_category(self, category):
        return self.filter(category=category, is_active=True)
    
    def popular(self):
        return self.filter(is_active=True).order_by('-play_count', '-average_score')
    
    def recent(self, days=30):
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(release_date__gte=cutoff_date, is_active=True)

class PlayerManager(models.Manager):
    """Custom manager for Player model"""
    def top_players(self, limit=10):
        return self.filter(is_active=True).order_by('-total_score')[:limit]
    
    def active_recently(self, days=7):
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(last_played__gte=cutoff_date, is_active=True)
    
    def by_level(self, level):
        min_score = (level - 1) * 500
        max_score = level * 500
        return self.filter(total_score__gte=min_score, total_score__lt=max_score)

class GameScoreManager(models.Manager):
    """Custom manager for GameScore model"""
    def personal_bests(self):
        return self.filter(is_personal_best=True)
    
    def by_game(self, game):
        return self.filter(game=game).order_by('-score')
    
    def by_player(self, player):
        return self.filter(player=player).order_by('-created_at')
    
    def recent(self, days=7):
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=cutoff_date)
    
    def top_scores(self, limit=10):
        return self.order_by('-score')[:limit]