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


def home(request):
    """Enhanced home view with comprehensive database queries"""
    
    # Cache key for expensive queries
    cache_key = 'home_dashboard_data'
    dashboard_data = cache.get(cache_key)
    
    if not dashboard_data:
        # Complex database queries with optimizations
        dashboard_data = {
            # Featured games with statistics
            'featured_games': Game.objects.filter(
                is_featured=True, 
                is_active=True
            ).select_related('category').annotate(
                total_plays=Count('scores'),
                average_rating=Avg('scores__score') / F('max_score') * 100,
                unique_players=Count('scores__player', distinct=True)
            ).order_by('-total_plays'),
            
            # Top players with recent activity
            'top_players': Player.objects.filter(
                is_active=True
            ).select_related('favorite_category').annotate(
                recent_games=Count(
                    'scores',
                    filter=Q(scores__created_at__gte=timezone.now() - timedelta(days=7))
                )
            ).order_by('-total_score')[:10],
            
            # Recent high scores with player and game info
            'recent_scores': GameScore.objects.select_related(
                'player', 'game', 'game__category'
            ).filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).order_by('-score')[:15],
            
            # Game categories with statistics
            'categories': Category.objects.filter(
                is_active=True
            ).annotate(
                game_count=Count('games', filter=Q(games__is_active=True)),
                total_plays=Count('games__scores'),
                avg_score=Avg('games__scores__score')
            ).filter(game_count__gt=0),
            
            # Site statistics
            'stats': {
                'total_players': Player.objects.filter(is_active=True).count(),
                'total_games': Game.objects.filter(is_active=True).count(),
                'games_played_today': GameScore.objects.filter(
                    created_at__date=timezone.now().date()
                ).count(),
                'active_players_week': Player.objects.filter(
                    last_played__gte=timezone.now() - timedelta(days=7)
                ).count(),
            }
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, dashboard_data, 300)
    
    context = {
        **dashboard_data,
        'current_time': timezone.now(),
        'trending_games': DatabaseOperations.get_trending_games(),
    }
    
    return render(request, 'games/home.html', context)

def player_profile(request, pk):
    """Detailed player profile with advanced statistics"""
    player = get_object_or_404(Player, pk=pk, is_active=True)
    
    # Get comprehensive player statistics
    stats = DatabaseOperations.get_player_statistics(pk)
    
    # Recent games with performance trends
    recent_scores = GameScore.objects.filter(
        player=player
    ).select_related('game').order_by('-created_at')[:20]
    
    # Game-wise statistics
    game_stats = GameScore.objects.filter(
        player=player
    ).values(
        'game__display_name',
        'game__icon'
    ).annotate(
        games_played=Count('id'),
        best_score=Max('score'),
        avg_score=Avg('score'),
        total_score=Sum('score'),
        last_played=Max('created_at')
    ).order_by('-games_played')
    
    # Player achievements
    achievements = PlayerAchievement.objects.filter(
        player=player
    ).select_related('achievement').order_by('-completed_at', '-progress')
    
    # Performance trends (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_performance = GameScore.objects.filter(
        player=player,
        created_at__gte=thirty_days_ago
    ).extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        games_played=Count('id'),
        avg_score=Avg('score'),
        total_score=Sum('score')
    ).order_by('day')
    
    context = {
        'player': player,
        'stats': stats,
        'recent_scores': recent_scores,
        'game_stats': game_stats,
        'achievements': achievements,
        'daily_performance': list(daily_performance),
        'rank_info': {
            'current_rank': player.rank,
            'total_players': Player.objects.filter(is_active=True).count(),
        }
    }
    
    return render(request, 'games/player_profile.html', context)