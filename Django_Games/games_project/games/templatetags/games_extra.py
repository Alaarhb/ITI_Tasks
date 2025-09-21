from django import template
from django.db.models import Count, Avg, Max
from ..models import GameScore, Player, Game

register = template.Library()

@register.simple_tag
def get_top_scores(game_name=None, limit=5):
    """DTL Tag: Get top scores"""
    scores = GameScore.objects.select_related('player', 'game')
    if game_name:
        scores = scores.filter(game__name=game_name)
    return scores.order_by('-score')[:limit]

@register.simple_tag
def get_player_stats(player_name):
    """DTL Tag: Get comprehensive player statistics"""
    try:
        player = Player.objects.get(name=player_name)
        scores = GameScore.objects.filter(player=player)
        
        return {
            'player': player,
            'total_games': scores.count(),
            'best_score': scores.aggregate(Max('score'))['score__max'] or 0,
            'average_score': scores.aggregate(Avg('score'))['score__avg'] or 0,
            'games_by_type': {
                game.name: scores.filter(game=game).count() 
                for game in Game.objects.all()
            },
            'recent_scores': scores.order_by('-created_at')[:3]
        }
    except Player.DoesNotExist:
        return None

@register.filter
def get_emoji_for_game(game_name):
    """DTL Filter: Get emoji for game"""
    emojis = {
        'number_guess': '🔢',
        'tic_tac_toe': '❌',
        'rock_paper_scissors': '✂️'
    }
    return emojis.get(game_name, '🎮')

@register.filter
def multiply(value, arg):
    """DTL Filter: Multiply two values"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """DTL Filter: Calculate percentage"""
    try:
        return round((float(value) / float(total)) * 100, 1) if total > 0 else 0
    except (ValueError, TypeError):
        return 0

@register.filter
def difficulty_stars(level):
    """DTL Filter: Convert difficulty level to stars"""
    return '⭐' * int(level) + '☆' * (5 - int(level))

@register.inclusion_tag('games/partials/score_badge.html')
def score_badge(score, max_score=100):
    """DTL Inclusion Tag: Render score badge"""
    percentage = (score / max_score) * 100 if max_score > 0 else 0
    
    if percentage >= 90:
        badge_class = 'badge-excellent'
        badge_text = 'Excellent!'
    elif percentage >= 70:
        badge_class = 'badge-good'
        badge_text = 'Good!'
    elif percentage >= 50:
        badge_class = 'badge-average'
        badge_text = 'Average'
    else:
        badge_class = 'badge-poor'
        badge_text = 'Try Again'
    
    return {
        'score': score,
        'percentage': percentage,
        'badge_class': badge_class,
        'badge_text': badge_text
    }
