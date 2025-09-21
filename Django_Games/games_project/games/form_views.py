from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.http import JsonResponse, Http404
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.views.generic import FormView
from django_ratelimit.decorators import ratelimit
from games.forms.model_forms import SecureUserRegistrationForm, PlayerProfileForm, GameFeedbackForm
from games.forms.custom_forms import SecureLoginForm, ContactForm, GameScoreSubmissionForm
from games.forms.formsets import GameScoreFormSet, MultipleChoiceTestForm
from games.security import SecurityManager
from games.models import Player, Game, GameScore

@sensitive_post_parameters('password1', 'password2')
@csrf_protect
@ratelimit(key='ip', rate='3/m', method='POST')
def secure_registration(request):
    """Secure user registration view"""
    
    if request.user.is_authenticated:
        messages.info(request, 'You are already registered and logged in.')
        return redirect('home')
    
    if request.method == 'POST':
        # Check rate limiting
        ip_address = get_client_ip(request)
        if not SecurityManager.check_rate_limit(ip_address, 'registration', 3, 3600):
            messages.error(request, 'Too many registration attempts. Please try again later.')
            return render(request, 'games/security/rate_limited.html')
        
        form = SecureUserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                
                # Log successful registration
                security_logger.info(f"New user registered: {user.username} from {ip_address}")
                
                # Auto-login after registration
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=password)
                if user:
                    login(request, user)
                    messages.success(request, f'Welcome {user.first_name}! Your account has been created successfully.')
                    return redirect('home')
                
            except Exception as e:
                security_logger.error(f"Registration error: {str(e)}")
                messages.error(request, 'An error occurred during registration. Please try again.')
        else:
            # Log form validation errors
            security_logger.warning(f"Registration form validation failed from {ip_address}: {form.errors}")
    else:
        form = SecureUserRegistrationForm()
    
    return render(request, 'games/auth/register.html', {'form': form})

@sensitive_post_parameters('password')
@csrf_protect
@never_cache
@ratelimit(key='ip', rate='5/m', method='POST')
def secure_login(request):
    """Secure login view with enhanced security"""
    
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        ip_address = get_client_ip(request)
        
        # Check if account is locked
        username = request.POST.get('username', '')
        if cache.get(f"account_locked:{username}"):
            messages.error(request, 'Account temporarily locked due to multiple failed attempts.')
            return render(request, 'games/auth/login.html', {'form': SecureLoginForm()})
        
        # Check rate limiting
        if not SecurityManager.check_rate_limit(ip_address, 'login', 5, 300):
            messages.error(request, 'Too many login attempts. Please try again later.')
            return render(request, 'games/security/rate_limited.html')
        
        form = SecureLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Set session timeout based on "remember me"
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)  # Browser close
            else:
                request.session.set_expiry(2592000)  # 30 days
            
            next_url = request.GET.get('next', 'home')
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Login failed. Please check your credentials.')
    else:
        form = SecureLoginForm()
    
    return render(request, 'games/auth/login.html', {'form': form})

@login_required
@csrf_protect
def profile_edit(request):
    """Secure profile editing view"""
    
    try:
        player = request.user.player
    except Player.DoesNotExist:
        messages.error(request, 'Player profile not found.')
        return redirect('home')
    
    if request.method == 'POST':
        # Rate limiting for profile updates
        if not SecurityManager.check_rate_limit(request.user.id, 'profile_update', 10, 3600):
            messages.error(request, 'Too many profile updates. Please try again later.')
            return redirect('profile_edit')
        
        form = PlayerProfileForm(request.POST, request.FILES, instance=player)
        if form.is_valid():
            try:
                updated_player = form.save()
                
                # Log profile update
                security_logger.info(f"Profile updated: {request.user.username}")
                
                messages.success(request, 'Your profile has been updated successfully!')
                return redirect('player_profile', pk=updated_player.id)
            except Exception as e:
                security_logger.error(f"Profile update error for {request.user.username}: {str(e)}")
                messages.error(request, 'An error occurred while updating your profile.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PlayerProfileForm(instance=player)
    
    return render(request, 'games/profile/edit.html', {'form': form, 'player': player})

@csrf_protect
@ratelimit(key='ip', rate='2/h', method='POST')
def contact_view(request):
    """Secure contact form view"""
    
    if request.method == 'POST':
        ip_address = get_client_ip(request)
        
        # Additional rate limiting for contact form
        if not SecurityManager.check_rate_limit(ip_address, 'contact', 3, 3600):
            messages.error(request, 'Too many contact form submissions. Please try again later.')
            return render(request, 'games/security/rate_limited.html')
        
        form = ContactForm(request.POST)
        if form.is_valid():
            try:
                if form.send_email():
                    # Log contact form submission
                    security_logger.info(
                        f"Contact form submitted: {form.cleaned_data['name']} "
                        f"<{form.cleaned_data['email']}> from {ip_address}"
                    )
                    
                    messages.success(request, 'Your message has been sent successfully! We\'ll get back to you soon.')
                    return redirect('contact')
                else:
                    messages.error(request, 'Failed to send your message. Please try again.')
            except Exception as e:
                security_logger.error(f"Contact form error: {str(e)}")
                messages.error(request, 'An error occurred while sending your message.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContactForm()
    
    return render(request, 'games/contact.html', {'form': form})

@login_required
@csrf_protect
@require_http_methods(["POST"])
def submit_score(request, game_id):
    """Secure score submission view"""
    
    game = get_object_or_404(Game, id=game_id, is_active=True)
    
    try:
        player = request.user.player
    except Player.DoesNotExist:
        return JsonResponse({'error': 'Player profile not found'}, status=404)
    
    # Rate limiting for score submissions
    if not SecurityManager.check_rate_limit(f"score_{request.user.id}", 'score_submission', 10, 300):
        security_logger.warning(f"Rate limit exceeded for score submission: {request.user.username}")
        return JsonResponse({'error': 'Too many score submissions'}, status=429)
    
    form = GameScoreSubmissionForm(game=game, player=player, data=request.POST)
    if form.is_valid():
        try:
            # Create game score
            score = GameScore.objects.create(
                player=player,
                game=game,
                score=form.cleaned_data['score'],
                attempts=form.cleaned_data['attempts'],
                duration=timedelta(seconds=form.cleaned_data['duration']),
                game_data=form.cleaned_data.get('game_data', {}),
                is_completed=True
            )
            
            # Log score submission
            security_logger.info(
                f"Score submitted: {player.name} - {game.display_name}: {score.score}"
            )
            
            return JsonResponse({
                'success': True,
                'score': score.score,
                'is_personal_best': score.is_personal_best,
                'message': 'Score submitted successfully!'
            })
            
        except Exception as e:
            security_logger.error(f"Score submission error: {str(e)}")
            return JsonResponse({'error': 'Failed to submit score'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid form data', 'errors': form.errors}, status=400)

@login_required
@csrf_protect
def bulk_score_entry(request):
    """Bulk score entry using formsets"""
    
    # Only allow staff users
    if not request.user.is_staff:
        raise PermissionDenied
    
    if request.method == 'POST':
        formset = GameScoreFormSet(request.POST)
        if formset.is_valid():
            try:
                instances = formset.save(commit=False)
                
                for instance in instances:
                    # Set the player for each score
                    if not instance.player_id:
                        instance.player = request.user.player
                    instance.save()
                
                # Handle deletions
                for obj in formset.deleted_objects:
                    obj.delete()
                
                security_logger.info(f"Bulk score entry by {request.user.username}: {len(instances)} scores")
                messages.success(request, f'Successfully processed {len(instances)} game scores.')
                return redirect('bulk_score_entry')
                
            except Exception as e:
                security_logger.error(f"Bulk score entry error: {str(e)}")
                messages.error(request, 'An error occurred while processing scores.')
        else:
            messages.error(request, 'Please correct the errors in the forms below.')
    else:
        formset = GameScoreFormSet(queryset=GameScore.objects.none())
    
    return render(request, 'games/admin/bulk_scores.html', {'formset': formset})

# Class-based view example with security
class SecureFormView(FormView):
    """Base secure form view with common security measures"""
    
    @method_decorator(csrf_protect)
    @method_decorator(ratelimit(key='ip', rate='10/h', method='POST'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def form_invalid(self, form):
        # Log form validation failures
        security_logger.warning(
            f"Form validation failed for {self.__class__.__name__}: {form.errors}"
        )
        return super().form_invalid(form)
    
    def form_valid(self, form):
        # Log successful form submissions
        security_logger.info(
            f"Form submitted successfully: {self.__class__.__name__}"
        )
        return super().form_valid(form)

print("🔒 Django Lab5 Forms & Security Implementation Created!")
print("📋 Three Form Methods: ModelForm, Custom Form, and Formsets")
print("🛡️ Comprehensive Security: CSRF, Rate Limiting, Validation, Logging")
print("🎯 Study Materials: Advanced form patterns and security best practices")