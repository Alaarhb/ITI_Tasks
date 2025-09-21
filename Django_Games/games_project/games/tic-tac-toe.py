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

def tic_tac_toe(request):
    """Enhanced Tic Tac Toe with advanced session management"""
    game = get_object_or_404(Game, name='tic_tac_toe', is_active=True)
    
    # Get comprehensive game statistics
    game_analytics = DatabaseOperations.get_game_analytics(game.id)
    
    # Recent games with detailed information
    recent_games = GameScore.objects.filter(
        game=game
    ).select_related('player').annotate(
        result=Case(
            When(score=100, then=Value('Win')),
            When(score=50, then=Value('Draw')),
            default=Value('Loss'),
            output_field= models.CharField()
        )
    ).order_by('-created_at')[:10]
    
    # Win rate statistics
    total_games = GameScore.objects.filter(game=game).count()
    wins = GameScore.objects.filter(game=game, score=100).count()
    draws = GameScore.objects.filter(game=game, score=50).count()
    losses = total_games - wins - draws
    
    win_stats = {
        'total': total_games,
        'wins': wins,
        'draws': draws,
        'losses': losses,
        'win_rate': round((wins / total_games * 100), 1) if total_games > 0 else 0,
        'draw_rate': round((draws / total_games * 100), 1) if total_games > 0 else 0,
    }
    
    context = {
        'game': game,
        'game_analytics': game_analytics,
        'recent_games': recent_games,
        'win_stats': win_stats,
        'ai_levels': [
            {'value': 1, 'name': 'Beginner', 'description': 'Random moves'},
            {'value': 2, 'name': 'Easy', 'description': 'Basic strategy'},
            {'value': 3, 'name': 'Normal', 'description': 'Smart AI'},
            {'value': 4, 'name': 'Hard', 'description': 'Advanced strategy'},
            {'value': 5, 'name': 'Expert', 'description': 'Perfect play'},
        ]
    }
    
    return render(request, 'games/tic_tac_toe.html', context)

@csrf_exempt
def tic_tac_toe_move(request):
    """Enhanced Tic Tac Toe move handling with session tracking"""
    if request.method == 'POST':
        data = json.loads(request.body)
        board = data.get('board', [''] * 9)
        position = data.get('position')
        player_name = data.get('player_name', 'Anonymous')
        difficulty = data.get('difficulty', 3)
        
        # Get or create player
        player, created = Player.objects.get_or_create(
            name=player_name,
            defaults={
                'total_games': 0,
                'total_score': 0,
                'preferred_difficulty': difficulty,
                'avatar': random.choice(['❌', '⭕', '🎯', '🎮', '🏆'])
            }
        )
        
        game = Game.objects.get(name='tic_tac_toe')
        
        # Create or get game session
        session_id = data.get('session_id')
        if session_id:
            try:
                game_session = GameSession.objects.get(session_id=session_id)
            except GameSession.DoesNotExist:
                game_session = GameSession.objects.create(
                    player=player,
                    game=game,
                    difficulty=difficulty,
                    current_data={'board': board, 'moves': []}
                )
        else:
            game_session = GameSession.objects.create(
                player=player,
                game=game,
                difficulty=difficulty,
                current_data={'board': board, 'moves': []}
            )
        
        # Record player move
        moves = game_session.current_data.get('moves', [])
        moves.append({
            'player': 'X',
            'position': position,
            'timestamp': timezone.now().isoformat()
        })
        
        # Player move
        if board[position] == '':
            board[position] = 'X'
            
            # Check if player wins
            winner = check_winner(board)
            if winner == 'X':
                # Player wins - create score with detailed tracking
                with transaction.atomic():
                    score_record = GameScore.objects.create(
                        player=player,
                        game=game,
                        score=100,
                        attempts=1,
                        duration=game_session.duration,
                        difficulty_played=difficulty,
                        game_data={
                            'final_board': board,
                            'moves': moves,
                            'result': 'win',
                            'moves_to_win': len([m for m in moves if m['player'] == 'X'])
                        },
                        accuracy=100,
                        session_id=game_session.session_id
                    )
                    
                    game_session.end_session(100)
                    DatabaseOperations.update_achievements(player.id)
                
                return JsonResponse({
                    'board': board,
                    'winner': 'X',
                    'message': f'🎉 {player.name} wins! Perfect strategy!',
                    'session_id': str(game_session.session_id),
                    'score': 100
                })
            
            # Check for draw
            if '' not in board:
                with transaction.atomic():
                    GameScore.objects.create(
                        player=player,
                        game=game,
                        score=50,
                        attempts=1,
                        duration=game_session.duration,
                        difficulty_played=difficulty,
                        game_data={
                            'final_board': board,
                            'moves': moves,
                            'result': 'draw'
                        },
                        session_id=game_session.session_id
                    )
                    
                    game_session.end_session(50)
                
                return JsonResponse({
                    'board': board,
                    'winner': 'Draw',
                    'message': f'🤝 Draw! Good game, {player.name}!',
                    'session_id': str(game_session.session_id),
                    'score': 50
                })
            
            # Computer move with difficulty-based AI
            computer_move = get_computer_move_advanced(board, difficulty)
            if computer_move is not None:
                board[computer_move] = 'O'
                
                # Record computer move
                moves.append({
                    'player': 'O',
                    'position': computer_move,
                    'timestamp': timezone.now().isoformat()
                })
                
                # Update session
                game_session.current_data = {'board': board, 'moves': moves}
                game_session.moves_count = len(moves)
                game_session.save()
                
                # Check if computer wins
                winner = check_winner(board)
                if winner == 'O':
                    with transaction.atomic():
                        GameScore.objects.create(
                            player=player,
                            game=game,
                            score=0,
                            attempts=1,
                            duration=game_session.duration,
                            difficulty_played=difficulty,
                            game_data={
                                'final_board': board,
                                'moves': moves,
                                'result': 'loss'
                            },
                            session_id=game_session.session_id
                        )
                        
                        game_session.end_session(0)
                    
                    return JsonResponse({
                        'board': board,
                        'winner': 'O',
                        'message': f'💔 Computer wins! Try again, {player.name}!',
                        'session_id': str(game_session.session_id),
                        'score': 0
                    })
                
                # Check for draw after computer move
                if '' not in board:
                    with transaction.atomic():
                        GameScore.objects.create(
                            player=player,
                            game=game,
                            score=50,
                            attempts=1,
                            duration=game_session.duration,
                            difficulty_played=difficulty,
                            game_data={
                                'final_board': board,
                                'moves': moves,
                                'result': 'draw'
                            },
                            session_id=game_session.session_id
                        )
                        
                        game_session.end_session(50)
                    
                    return JsonResponse({
                        'board': board,
                        'winner': 'Draw',
                        'message': f'🤝 Draw! Well played, {player.name}!',
                        'session_id': str(game_session.session_id),
                        'score': 50
                    })
        
        return JsonResponse({
            'board': board,
            'session_id': str(game_session.session_id)
        })

def check_winner(board):
    """Check if there's a winner in Tic Tac Toe"""
    winning_combos = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]              # Diagonals
    ]
    
    for combo in winning_combos:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] != '':
            return board[combo[0]]
    return None

def get_computer_move_advanced(board, difficulty):
    """Advanced AI for Tic Tac Toe based on difficulty level"""
    if difficulty == 1:  # Beginner - mostly random
        available = [i for i, spot in enumerate(board) if spot == '']
        return random.choice(available) if available else None
    
    elif difficulty == 2:  # Easy - some strategy
        if random.random() < 0.3:  # 30% strategic moves
            return get_strategic_move(board)
        else:
            available = [i for i, spot in enumerate(board) if spot == '']
            return random.choice(available) if available else None
    
    elif difficulty >= 3:  # Normal and above - full strategy
        return get_strategic_move(board)

def get_strategic_move(board):
    """Strategic move calculation for Tic Tac Toe AI"""
    # Try to win
    for i in range(9):
        if board[i] == '':
            board[i] = 'O'
            if check_winner(board) == 'O':
                board[i] = ''
                return i
            board[i] = ''
    
    # Try to block player
    for i in range(9):
        if board[i] == '':
            board[i] = 'X'
            if check_winner(board) == 'X':
                board[i] = ''
                return i
            board[i] = ''
    
    # Take center if available
    if board[4] == '':
        return 4
    
    # Take corners
    corners = [0, 2, 6, 8]
    available_corners = [i for i in corners if board[i] == '']
    if available_corners:
        return random.choice(available_corners)
    
    # Take any available spot
    available = [i for i, spot in enumerate(board) if spot == '']
    return random.choice(available) if available else None
