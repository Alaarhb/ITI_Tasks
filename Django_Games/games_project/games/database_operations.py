from django.db.models import Q, F, Case, When, Value, IntegerField
from django.db.models.functions import Extract, TruncDate, Coalesce
from django.utils import timezone
from datetime import timedelta
from .models import Player, Game, GameScore, Achievement, PlayerAchievement

class DatabaseOperations:
    """Advanced database operations for analytics and reporting"""
    
    @staticmethod
    def get_player_statistics(player_id):
        """Get comprehensive player statistics"""
        return Player.objects.filter(id=player_id).annotate(
            games_played=Count('scores'),
            average_score=Avg('scores__score'),
            best_score=Max('scores__score'),
            worst_score=Min('scores__score'),
            total_playtime=Sum('scores__duration'),
            favorite_game=Subquery(
                GameScore.objects.filter(player_id=player_id)
                .values('game__display_name')
                .annotate(count=Count('game'))
                .order_by('-count')
                .values('game__display_name')[:1]
            )
        ).first()
    
    @staticmethod
    def get_game_analytics(game_id, days=30):
        """Get detailed game analytics"""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        return GameScore.objects.filter(
            game_id=game_id,
            created_at__gte=cutoff_date
        ).aggregate(
            total_plays=Count('id'),
            average_score=Avg('score'),
            highest_score=Max('score'),
            average_duration=Avg('duration'),
            unique_players=Count('player', distinct=True),
            completion_rate=Avg(
                Case(
                    When(is_completed=True, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ) * 100
        )
    
    @staticmethod
    def get_leaderboard(game_id=None, period='all_time', limit=10):
        """Get leaderboard with various filtering options"""
        queryset = GameScore.objects.select_related('player', 'game')
        
        if game_id:
            queryset = queryset.filter(game_id=game_id)
        
        if period == 'daily':
            queryset = queryset.filter(created_at__date=timezone.now().date())
        elif period == 'weekly':
            week_ago = timezone.now() - timedelta(days=7)
            queryset = queryset.filter(created_at__gte=week_ago)
        elif period == 'monthly':
            month_ago = timezone.now() - timedelta(days=30)
            queryset = queryset.filter(created_at__gte=month_ago)
        
        return queryset.order_by('-score')[:limit]
    
    @staticmethod
    def update_achievements(player_id):
        """Check and update player achievements"""
        player = Player.objects.get(id=player_id)
        achievements = Achievement.objects.filter(is_active=True)
        
        for achievement in achievements:
            player_achievement, created = PlayerAchievement.objects.get_or_create(
                player=player,
                achievement=achievement,
                defaults={'progress': 0}
            )
            
            if not player_achievement.is_completed:
                # Calculate progress based on achievement type
                if achievement.type == 'score':
                    if achievement.game:
                        best_score = GameScore.objects.filter(
                            player=player,
                            game=achievement.game
                        ).aggregate(Max('score'))['score__max'] or 0
                        player_achievement.progress = best_score
                    else:
                        player_achievement.progress = player.highest_score
                
                elif achievement.type == 'games':
                    player_achievement.progress = player.total_games
                
                elif achievement.type == 'streak':
                    # Calculate win streak (implementation would depend on game logic)
                    pass
                
                # Check if achievement is now completed
                player_achievement.check_completion()
    
    @staticmethod
    def get_trending_games(days=7):
        """Get trending games based on recent activity"""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        return Game.objects.filter(is_active=True).annotate(
            recent_plays=Count(
                'scores',
                filter=Q(scores__created_at__gte=cutoff_date)
            ),
            recent_players=Count(
                'scores__player',
                filter=Q(scores__created_at__gte=cutoff_date),
                distinct=True
            ),
            recent_average_score=Avg(
                'scores__score',
                filter=Q(scores__created_at__gte=cutoff_date)
            )
        ).filter(
            recent_plays__gt=0
        ).order_by('-recent_plays', '-recent_players')

print("🎮 Django Lab3 Database Models Created!")
print("📚 Study Materials: Advanced Database Design Patterns")
print("🔍 Features: Enhanced relationships, managers, and analytics")
print("📊 Analytics: Player statistics, game metrics, and leaderboards")