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


def rock_paper_scissors(request):
    """Enhanced Rock Paper Scissors with DTL Variables and Statistics"""
    game_obj = get_object_or_404(Game, name='rock_paper_scissors')
    
    if request.method == 'POST':
        player_choice = request.POST.get('choice')
        player_name = request.POST.get('player_name', 'Anonymous')
        
        # Get or create player
        player, created = Player.objects.get_or_create(
            name=player_name,
            defaults={'total_games': 0, 'total_score': 0}
        )
        
        choices = ['rock', 'paper', 'scissors']
        computer_choice = random.choice(choices)
        
        # Determine winner using DTL logic
        result = determine_rps_winner(player_choice, computer_choice)
        
        # Update session stats using DTL Variables
        games_played = request.session.get('rps_games_played', 0) + 1
        wins = request.session.get('rps_wins', 0)
        ties = request.session.get('rps_ties', 0)
        
        score = 0
        if result == 'win':
            wins += 1
            score = 10
        elif result == 'tie':
            ties += 1
            score = 5
        
        # Save score and update player
        GameScore.objects.create(
            player=player,
            game=game_obj,
            score=score,
            attempts=games_played
        )
        
        player.total_games += 1
        player.total_score += score
        player.save()
        
        # Update session
        request.session['rps_games_played'] = games_played
        request.session['rps_wins'] = wins
        request.session['rps_ties'] = ties
        
        # DTL Context with comprehensive data
        context = {
            'game': game_obj,
            'player': player,
            'player_choice': player_choice,
            'computer_choice': computer_choice,
            'result': result,
            'score': score,
            'games_played': games_played,
            'wins': wins,
            'ties': ties,
            'losses': games_played - wins - ties,
            'win_rate': round((wins / games_played) * 100, 1) if games_played > 0 else 0,
            'choice_emoji': get_choice_emoji(player_choice),
            'computer_emoji': get_choice_emoji(computer_choice),
            'result_message': get_result_message(result, player.name),
        }
        
        return render(request, 'games/rock_paper_scissors.html', context)
    
    # GET request - show game statistics using DTL
    player_scores = GameScore.objects.filter(game=game_obj).select_related('player')[:10]
    game_stats = GameScore.objects.filter(game=game_obj).aggregate(
        total_games=Count('id'),
        total_wins=Count('id', filter=models.Q(score=10)),
        total_ties=Count('id', filter=models.Q(score=5)),
        avg_score=Avg('score')
    )
    
    context = {
        'game': game_obj,
        'player_scores': player_scores,
        'game_stats': game_stats,
        'session_stats': {
            'games_played': request.session.get('rps_games_played', 0),
            'wins': request.session.get('rps_wins', 0),
            'ties': request.session.get('rps_ties', 0),
        }
    }
    
    return render(request, 'games/rock_paper_scissors.html', context)

def determine_rps_winner(player, computer):
    """Determine Rock Paper Scissors winner"""
    if player == computer:
        return 'tie'
    elif (player == 'rock' and computer == 'scissors') or \
         (player == 'paper' and computer == 'rock') or \
         (player == 'scissors' and computer == 'paper'):
        return 'win'
    else:
        return 'lose'

def get_choice_emoji(choice):
    """Get emoji for choice - DTL Helper Function"""
    emojis = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}
    return emojis.get(choice, '❓')

def get_result_message(result, player_name):
    """Get result message - DTL Helper Function"""
    messages = {
        'win': f'🎉 {player_name} wins!',
        'lose': f'💔 {player_name} loses!',
        'tie': f'🤝 It\'s a tie, {player_name}!'
    }
    return messages.get(result, 'Unknown result')

def reset_rps_stats(request):
    """Reset Rock Paper Scissors session statistics"""
    for key in ['rps_games_played', 'rps_wins', 'rps_ties']:
        if key in request.session:
            del request.session[key]
    messages.info(request, '📊 Statistics reset successfully!')
    return redirect('rock_paper_scissors')
