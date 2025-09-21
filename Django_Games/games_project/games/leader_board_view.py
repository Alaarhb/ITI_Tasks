from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, CreateView
from django.contrib import messages
from django.db.models import (
    Count, Avg, Sum, Max, Min, Q, F, Case, When, Value, 
    IntegerField, Prefetch, Subquery, OuterRef
)
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db import transaction
import random
import json
from datetime import timedelta
from .models import (
    Player, Game, GameScore, Category, Achievement, 
    PlayerAchievement, GameSession, Leaderboard
)
from .database_operations import DatabaseOperations


class LeaderboardView(ListView):
    """Enhanced leaderboard with filtering and pagination"""
    model = GameScore
    template_name = 'games/leaderboard.html'
    context_object_name = 'scores'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = GameScore.objects.select_related('player', 'game').filter(is_completed=True)
        
        # Filter by game
        game_id = self.request.GET.get('game')
        if game_id:
            queryset = queryset.filter(game_id=game_id)
        
        # Filter by period
        period = self.request.GET.get('period', 'all_time')
        if period == 'today':
            queryset = queryset.filter(created_at__date=timezone.now().date())
        elif period == 'week':
            week_ago = timezone.now() - timedelta(days=7)
            queryset = queryset.filter(created_at__gte=week_ago)
        elif period == 'month':
            month_ago = timezone.now() - timedelta(days=30)
            queryset = queryset.filter(created_at__gte=month_ago)
        
        return queryset.order_by('-score')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['games'] = Game.objects.filter(is_active=True).order_by('display_name')
        context['current_game'] = self.request.GET.get('game')
        context['current_period'] = self.request.GET.get('period', 'all_time')
        
        # Add ranking information
        scores = context['scores']
        for i, score in enumerate(scores, start=1):
            score.rank = i
        
        return context

def analytics_dashboard(request):
    """Comprehensive analytics dashboard"""
    if not request.user.is_staff:
        raise Http404("Not authorized")
    
    # Time period filtering
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Game analytics
    game_analytics = []
    for game in Game.objects.filter(is_active=True):
        analytics = DatabaseOperations.get_game_analytics(game.id, days)
        analytics['game'] = game
        game_analytics.append(analytics)
    
    # Player analytics
    player_stats = Player.objects.filter(
        is_active=True,
        scores__created_at__gte=start_date
    ).annotate(
        recent_games=Count('scores', filter=Q(scores__created_at__gte=start_date)),
        recent_score=Sum('scores__score', filter=Q(scores__created_at__gte=start_date)),
        avg_recent_score=Avg('scores__score', filter=Q(scores__created_at__gte=start_date))
    ).filter(recent_games__gt=0).order_by('-recent_score')[:20]
    
    # Daily statistics
    daily_stats = GameScore.objects.filter(
        created_at__gte=start_date
    ).extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        games_played=Count('id'),
        unique_players=Count('player', distinct=True),
        total_score=Sum('score'),
        avg_score=Avg('score')
    ).order_by('day')
    
    context = {
        'game_analytics': game_analytics,
        'player_stats': player_stats,
        'daily_stats': list(daily_stats),
        'period_days': days,
        'total_stats': {
            'total_players': Player.objects.filter(is_active=True).count(),
            'total_games': Game.objects.filter(is_active=True).count(),
            'total_scores': GameScore.objects.count(),
            'recent_activity': GameScore.objects.filter(
                created_at__gte=start_date
            ).count(),
        }
    }
    
    return render(request, 'games/analytics.html', context)

print("🚀 Enhanced Views with Advanced Database Operations Created!")
print("📊 Features: Session management, analytics, and comprehensive tracking")
print("🎯 Study Materials: Complex queries, transactions, and performance optimization")