from django.db import models
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, Max, Min, F, Case, When, Value
from datetime import timedelta, datetime
import operator
from functools import reduce

class TimestampedQuerySet(models.QuerySet):
    """Base QuerySet with timestamp filtering methods"""
    
    def created_today(self):
        """Filter records created today"""
        return self.filter(created_at__date=timezone.now().date())
    
    def created_this_week(self):
        """Filter records created this week"""
        start_week = timezone.now() - timedelta(days=7)
        return self.filter(created_at__gte=start_week)
    
    def created_this_month(self):
        """Filter records created this month"""
        start_month = timezone.now() - timedelta(days=30)
        return self.filter(created_at__gte=start_month)
    
    def created_between(self, start_date, end_date):
        """Filter records created between two dates"""
        return self.filter(created_at__range=[start_date, end_date])
    
    def recent(self, days=7):
        """Filter recent records"""
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=cutoff_date)
    
    def older_than(self, days):
        """Filter records older than specified days"""
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(created_at__lt=cutoff_date)

class ActiveQuerySet(TimestampedQuerySet):
    """QuerySet for models with is_active field"""
    
    def active(self):
        """Filter active records only"""
        return self.filter(is_active=True)
    
    def inactive(self):
        """Filter inactive records only"""
        return self.filter(is_active=False)
    
    def toggle_active(self):
        """Toggle active status for all records in queryset"""
        return self.update(is_active=models.F('is_active').bitxor(True))

class PlayerQuerySet(ActiveQuerySet):
    """Custom QuerySet for Player model with advanced filtering methods"""
    
    def with_scores(self):
        """Players with at least one score"""
        return self.filter(scores__isnull=False).distinct()
    
    def without_scores(self):
        """Players without any scores"""
        return self.filter(scores__isnull=True)
    
    def top_players(self, limit=10):
        """Get top players by total score"""
        return self.active().order_by('-total_score')[:limit]
    
    def by_level_range(self, min_level=1, max_level=100):
        """Filter players by level range"""
        min_score = (min_level - 1) * 500
        max_score = max_level * 500
        return self.filter(
            total_score__gte=min_score,
            total_score__lt=max_score
        )
    
    def beginners(self):
        """Players at beginner level (1-5)"""
        return self.by_level_range(1, 5)
    
    def intermediate(self):
        """Players at intermediate level (6-15)"""
        return self.by_level_range(6, 15)
    
    def advanced(self):
        """Players at advanced level (16-50)"""
        return self.by_level_range(16, 50)
    
    def experts(self):
        """Players at expert level (50+)"""
        return self.filter(total_score__gte=25000)  # Level 50+
    
    def active_recently(self, days=7):
        """Players who played recently"""
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(last_played__gte=cutoff_date)
    
    def inactive_players(self, days=30):
        """Players who haven't played for specified days"""
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(
            models.Q(last_played__lt=cutoff_date) | 
            models.Q(last_played__isnull=True)
        )
    
    def with_achievements(self):
        """Players who have earned achievements"""
        return self.filter(
            achievements__is_completed=True
        ).distinct()
    
    def search(self, query):
        """Search players by name or email"""
        if not query:
            return self.none()
        
        return self.filter(
            models.Q(name__icontains=query) |
            models.Q(email__icontains=query)
        ).distinct()
    
    def with_statistics(self):
        """Annotate players with comprehensive statistics"""
        return self.annotate(
            games_played=Count('scores'),
            games_won=Count('scores', filter=Q(scores__score__gte=F('scores__game__max_score') * 0.8)),
            average_score=Avg('scores__score'),
            best_game_score=Max('scores__score'),
            worst_game_score=Min('scores__score'),
            total_playtime=Sum('scores__duration'),
            favorite_game=models.Subquery(
                # Subquery to find most played game
                self.model.objects.filter(
                    pk=models.OuterRef('pk')
                ).values('scores__game__display_name').annotate(
                    game_count=Count('scores__game')
                ).order_by('-game_count').values('scores__game__display_name')[:1]
            ),
            recent_activity=Count(
                'scores',
                filter=Q(scores__created_at__gte=timezone.now() - timedelta(days=7))
            ),
            win_rate=Case(
                When(games_played__gt=0, 
                     then=Cast(F('games_won'), models.FloatField()) / Cast(F('games_played'), models.FloatField()) * 100),
                default=Value(0),
                output_field=models.FloatField()
            )
        )
    
    def leaderboard(self, game=None, period='all_time'):
        """Generate leaderboard queryset"""
        queryset = self.with_statistics()
        
        if game:
            queryset = queryset.filter(scores__game=game)
        
        if period == 'today':
            queryset = queryset.filter(scores__created_at__date=timezone.now().date())
        elif period == 'week':
            queryset = queryset.filter(scores__created_at__gte=timezone.now() - timedelta(days=7))
        elif period == 'month':
            queryset = queryset.filter(scores__created_at__gte=timezone.now() - timedelta(days=30))
        
        return queryset.order_by('-total_score', '-average_score')

class GameQuerySet(ActiveQuerySet):
    """Custom QuerySet for Game model"""
    
    def featured(self):
        """Get featured games"""
        return self.filter(is_featured=True, is_active=True)
    
    def by_category(self, category):
        """Filter games by category"""
        if isinstance(category, str):
            return self.filter(category__name__iexact=category, is_active=True)
        return self.filter(category=category, is_active=True)
    
    def by_difficulty(self, min_level=1, max_level=5):
        """Filter games by difficulty level"""
        return self.filter(
            difficulty_level__gte=min_level,
            difficulty_level__lte=max_level,
            is_active=True
        )
    
    def easy_games(self):
        """Get easy games (difficulty 1-2)"""
        return self.by_difficulty(1, 2)
    
    def medium_games(self):
        """Get medium games (difficulty 3)"""
        return self.by_difficulty(3, 3)
    
    def hard_games(self):
        """Get hard games (difficulty 4-5)"""
        return self.by_difficulty(4, 5)
    
    def popular(self, min_plays=10):
        """Get popular games based on play count"""
        return self.filter(play_count__gte=min_plays, is_active=True).order_by('-play_count')
    
    def highly_rated(self, min_rating=75):
        """Get highly rated games"""
        return self.filter(average_score__gte=min_rating, is_active=True).order_by('-average_score')
    
    def new_releases(self, days=30):
        """Get recently released games"""
        cutoff_date = timezone.now().date() - timedelta(days=days)
        return self.filter(release_date__gte=cutoff_date, is_active=True)
    
    def with_statistics(self):
        """Annotate games with comprehensive statistics"""
        return self.annotate(
            total_players=Count('scores__player', distinct=True),
            total_plays=Count('scores'),
            recent_plays=Count('scores', filter=Q(scores__created_at__gte=timezone.now() - timedelta(days=7))),
            avg_score=Avg('scores__score'),
            highest_score=Max('scores__score'),
            avg_duration=Avg('scores__duration'),
            completion_rate=Avg(
                Case(
                    When(scores__is_completed=True, then=Value(100)),
                    default=Value(0),
                    output_field=models.FloatField()
                )
            ),
            popularity_score=F('total_plays') * 0.7 + F('avg_score') * 0.3
        )
    
    def trending(self, days=7):
        """Get trending games based on recent activity"""
        return self.with_statistics().filter(
            recent_plays__gt=0
        ).order_by('-recent_plays', '-total_players')
    
    def search(self, query):
        """Search games by name or description"""
        if not query:
            return self.none()
        
        return self.filter(
            models.Q(display_name__icontains=query) |
            models.Q(description__icontains=query) |
            models.Q(category__name__icontains=query)
        ).distinct()

class GameScoreQuerySet(TimestampedQuerySet):
    """Custom QuerySet for GameScore model"""
    
    def completed_only(self):
        """Filter completed games only"""
        return self.filter(is_completed=True)
    
    def personal_bests(self):
        """Filter personal best scores only"""
        return self.filter(is_personal_best=True)
    
    def by_player(self, player):
        """Filter scores by player"""
        return self.filter(player=player)
    
    def by_game(self, game):
        """Filter scores by game"""
        return self.filter(game=game)
    
    def high_scores(self, threshold=80):
        """Filter high scores above threshold percentage"""
        return self.filter(
            score__gte=models.F('max_possible_score') * threshold / 100
        )
    
    def low_scores(self, threshold=40):
        """Filter low scores below threshold percentage"""
        return self.filter(
            score__lt=models.F('max_possible_score') * threshold / 100
        )
    
    def perfect_scores(self):
        """Filter perfect scores"""
        return self.filter(score=models.F('max_possible_score'))
    
    def quick_games(self, max_duration_minutes=5):
        """Filter games completed quickly"""
        return self.filter(
            duration__lte=timedelta(minutes=max_duration_minutes)
        )
    
    def long_games(self, min_duration_minutes=15):
        """Filter games that took long to complete"""
        return self.filter(
            duration__gte=timedelta(minutes=min_duration_minutes)
        )
    
    def with_performance_rating(self):
        """Annotate scores with performance ratings"""
        return self.annotate(
            score_percentage=Case(
                When(max_possible_score__gt=0, 
                     then=Cast(F('score'), models.FloatField()) / Cast(F('max_possible_score'), models.FloatField()) * 100),
                default=Value(0),
                output_field=models.FloatField()
            ),
            performance_rating=Case(
                When(score_percentage__gte=90, then=Value('Excellent')),
                When(score_percentage__gte=75, then=Value('Good')),
                When(score_percentage__gte=60, then=Value('Average')),
                When(score_percentage__gte=40, then=Value('Below Average')),
                default=Value('Poor'),
                output_field=models.CharField()
            ),
            difficulty_bonus=F('difficulty_played') * 10,
            final_rating=F('score_percentage') + F('difficulty_bonus')
        )
    
    def leaderboard(self, game=None, period='all_time', limit=100):
        """Generate leaderboard queryset"""
        queryset = self.completed_only().select_related('player', 'game')
        
        if game:
            queryset = queryset.filter(game=game)
        
        if period == 'today':
            queryset = queryset.created_today()
        elif period == 'week':
            queryset = queryset.created_this_week()
        elif period == 'month':
            queryset = queryset.created_this_month()
        
        return queryset.order_by('-score', '-created_at')[:limit]
    
    def statistics_for_period(self, start_date=None, end_date=None):
        """Get statistical summary for a period"""
        queryset = self.completed_only()
        
        if start_date and end_date:
            queryset = queryset.created_between(start_date, end_date)
        
        return queryset.aggregate(
            total_games=Count('id'),
            total_players=Count('player', distinct=True),
            avg_score=Avg('score'),
            highest_score=Max('score'),
            total_score=Sum('score'),
            avg_duration=Avg('duration'),
            perfect_games=Count('id', filter=Q(score=F('max_possible_score'))),
            completion_rate=Avg(
                Case(
                    When(is_completed=True, then=Value(100)),
                    default=Value(0),
                    output_field=models.FloatField()
                )
            )
        )
