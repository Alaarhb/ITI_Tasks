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

def number_guess(request):
    """Enhanced Number Guessing Game with detailed tracking"""
    game = get_object_or_404(Game, name='number_guess', is_active=True)
    
    if request.method == 'POST':
        player_name = request.POST.get('player_name', 'Anonymous')
        guess = int(request.POST.get('guess', 0))
        
        # Get or create player with enhanced data
        player, created = Player.objects.get_or_create(
            name=player_name,
            defaults={
                'total_games': 0,
                'total_score': 0,
                'preferred_difficulty': 3,
                'avatar': random.choice(['🎮', '🎯', '🎲', '⭐', '🏆'])
            }
        )
        
        # Get or create game session
        session_id = request.session.get('game_session_id')
        if session_id:
            try:
                game_session = GameSession.objects.get(
                    session_id=session_id,
                    status='active'
                )
            except GameSession.DoesNotExist:
                game_session = None
        else:
            game_session = None
        
        if not game_session:
            target = random.randint(1, 100)
            game_session = GameSession.objects.create(
                player=player,
                game=game,
                current_data={'target': target, 'guesses': []},
                difficulty=3
            )
            request.session['game_session_id'] = str(game_session.session_id)
            attempts = 1
        else:
            target = game_session.current_data['target']
            attempts = len(game_session.current_data.get('guesses', [])) + 1
        
        # Record the guess
        guesses = game_session.current_data.get('guesses', [])
        guesses.append({
            'guess': guess,
            'timestamp': timezone.now().isoformat(),
            'attempt': attempts
        })
        game_session.current_data['guesses'] = guesses
        game_session.moves_count = attempts
        game_session.save()
        
        if guess == target:
            # Game completed - comprehensive scoring
            base_score = max(100 - attempts, 10)
            difficulty_bonus = game_session.difficulty * 5
            time_bonus = max(10 - (game_session.duration.seconds // 60), 0) if game_session.duration else 0
            
            final_score = base_score + difficulty_bonus + time_bonus
            
            # End session and create score record
            game_session.end_session(final_score)
            
            # Create detailed game score with transaction
            with transaction.atomic():
                score_record = GameScore.objects.create(
                    player=player,
                    game=game,
                    score=final_score,
                    attempts=attempts,
                    duration=game_session.duration,
                    started_at=game_session.started_at,
                    ended_at=game_session.ended_at,
                    difficulty_played=game_session.difficulty,
                    game_data={
                        'target_number': target,
                        'all_guesses': guesses,
                        'completion_time': game_session.duration.total_seconds() if game_session.duration else None
                    },
                    accuracy=100,  # Perfect accuracy for correct guess
                    session_id=game_session.session_id
                )
                
                # Update achievements
                DatabaseOperations.update_achievements(player.id)
            
            messages.success(
                request, 
                f'🎉 Congratulations {player.name}! You guessed {target} in {attempts} attempts! '
                f'Final Score: {final_score} points'
            )
            
            # Clear session
            if 'game_session_id' in request.session:
                del request.session['game_session_id']
            
            return redirect('number_guess')
        
        else:
            hint = "📈 Too low! Try higher." if guess < target else "📉 Too high! Try lower."
            
            # Update current score based on progress
            progress_score = max(50 - attempts * 2, 0)
            game_session.current_score = progress_score
            game_session.save()
            
            context = {
                'game': game,
                'hint': hint,
                'attempts': attempts,
                'guess': guess,
                'player': player,
                'progress_percentage': min((attempts / 20) * 100, 100),
                'current_score': progress_score,
                'session': game_session,
            }
            return render(request, 'games/number_guess.html', context)
    
    # GET request - show game with enhanced statistics
    recent_scores = GameScore.objects.filter(
        game=game
    ).select_related('player').order_by('-score')[:10]
    
    game_analytics = DatabaseOperations.get_game_analytics(game.id)
    
    # Personal best for current session (if player name in session)
    personal_best = None
    if 'player_name' in request.session:
        try:
            player = Player.objects.get(name=request.session['player_name'])
            personal_best = GameScore.objects.filter(
                player=player,
                game=game
            ).order_by('-score').first()
        except Player.DoesNotExist:
            pass
    
    context = {
        'game': game,
        'recent_scores': recent_scores,
        'game_analytics': game_analytics,
        'personal_best': personal_best,
        'difficulty_levels': [
            {'value': 1, 'name': 'Very Easy', 'description': 'More hints, larger range'},
            {'value': 2, 'name': 'Easy', 'description': 'Extra hints'},
            {'value': 3, 'name': 'Normal', 'description': 'Standard gameplay'},
            {'value': 4, 'name': 'Hard', 'description': 'Fewer hints'},
            {'value': 5, 'name': 'Expert', 'description': 'Minimal hints, time pressure'},
        ]
    }
    
    return render(request, 'games/number_guess.html', context)