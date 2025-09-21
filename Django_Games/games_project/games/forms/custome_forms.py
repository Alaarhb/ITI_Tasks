from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import logging

security_logger = logging.getLogger('games.security')

class SecureLoginForm(forms.Form):
    """Custom secure login form with rate limiting and logging"""
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Username or Email',
            'autocomplete': 'username',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Password',
            'autocomplete': 'current-password'
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Remember me for 30 days"
    )
    
    captcha = CaptchaField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter CAPTCHA'
        })
    )
    
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            HTML('<div class="text-center mb-4"><h2>Welcome Back!</h2></div>'),
            Field('username', css_class='mb-3'),
            Field('password', css_class='mb-3'),
            Field('captcha', css_class='mb-3'),
            Field('remember_me', css_class='form-check mb-3'),
            Submit('submit', 'Sign In', css_class='btn btn-primary btn-lg w-100 mb-3'),
            HTML('<div class="text-center"><a href="{% url \'password_reset\' %}">Forgot your password?</a></div>')
        )
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username is not None and password:
            # Try to authenticate with username or email
            user = None
            
            # First try username
            user = authenticate(self.request, username=username, password=password)
            
            # If that fails, try email
            if user is None:
                try:
                    user_by_email = User.objects.get(email=username)
                    user = authenticate(self.request, username=user_by_email.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user is None:
                # Log failed login attempt
                security_logger.warning(
                    f"Failed login attempt for username/email: {username} from IP: {self.get_client_ip()}"
                )
                raise ValidationError(
                    "Please enter a correct username/email and password. "
                    "Note that both fields may be case-sensitive."
                )
            else:
                self.confirm_login_allowed(user)
                
                # Log successful login
                security_logger.info(
                    f"Successful login for user: {user.username} from IP: {self.get_client_ip()}"
                )
        
        return self.cleaned_data
    
    def confirm_login_allowed(self, user):
        """Check if user is allowed to login"""
        if not user.is_active:
            raise ValidationError("This account is inactive.")
    
    def get_user(self):
        return self.user_cache
    
    def get_client_ip(self):
        """Get client IP address"""
        if self.request:
            x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = self.request.META.get('REMOTE_ADDR')
            return ip
        return 'Unknown'

class ContactForm(forms.Form):
    """Secure contact form with comprehensive validation"""
    
    SUBJECT_CHOICES = [
        ('general', 'General Inquiry'),
        ('bug_report', 'Bug Report'),
        ('feature_request', 'Feature Request'),
        ('account_issue', 'Account Issue'),
        ('technical_support', 'Technical Support'),
        ('partnership', 'Partnership Inquiry'),
    ]
    
    name = forms.CharField(
        max_length=100,
        validators=[validate_no_profanity],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your full name'
        })
    )
    
    email = forms.EmailField(
        validators=[validate_email_domain],
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email address'
        })
    )
    
    subject = forms.ChoiceField(
        choices=SUBJECT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    message = forms.CharField(
        max_length=2000,
        validators=[validate_no_profanity],
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Please describe your inquiry in detail...'
        })
    )
    
    priority = forms.ChoiceField(
        choices=[
            ('low', 'Low Priority'),
            ('medium', 'Medium Priority'),
            ('high', 'High Priority'),
            ('urgent', 'Urgent'),
        ],
        initial='medium',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    newsletter_signup = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Subscribe to our newsletter for updates"
    )
    
    captcha = CaptchaField()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            HTML('<h3 class="mb-4">Contact Us</h3>'),
            HTML('<p class="text-muted mb-4">We\'d love to hear from you. Send us a message and we\'ll respond as soon as possible.</p>'),
            Row(
                Column('name', css_class='form-group col-md-6 mb-3'),
                Column('email', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('subject', css_class='mb-3'),
            Field('message', css_class='mb-3'),
            HTML('<label class="form-label">Priority Level:</label>'),
            Field('priority', css_class='mb-3'),
            Field('newsletter_signup', css_class='form-check mb-3'),
            Field('captcha', css_class='mb-3'),
            Submit('submit', 'Send Message', css_class='btn btn-primary btn-lg')
        )
    
    def clean_message(self):
        """Validate message content"""
        message = self.cleaned_data.get('message')
        
        # Check minimum length
        if len(message) < 10:
            raise ValidationError("Message must be at least 10 characters long.")
        
        # Check for spam patterns
        spam_patterns = ['click here', 'free money', 'guaranteed', 'act now']
        message_lower = message.lower()
        
        for pattern in spam_patterns:
            if pattern in message_lower:
                security_logger.warning(f"Potential spam detected in contact form: {pattern}")
                raise ValidationError("Message contains suspicious content.")
        
        return message
    
    def send_email(self):
        """Send contact form email"""
        try:
            subject_map = dict(self.SUBJECT_CHOICES)
            email_subject = f"Contact Form: {subject_map[self.cleaned_data['subject']]}"
            
            message = f"""
            New contact form submission:
            
            Name: {self.cleaned_data['name']}
            Email: {self.cleaned_data['email']}
            Subject: {subject_map[self.cleaned_data['subject']]}
            Priority: {self.cleaned_data['priority']}
            
            Message:
            {self.cleaned_data['message']}
            
            Newsletter Signup: {'Yes' if self.cleaned_data['newsletter_signup'] else 'No'}
            """
            
            send_mail(
                email_subject,
                message,
                self.cleaned_data['email'],
                [settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
            
            return True
        except Exception as e:
            security_logger.error(f"Failed to send contact form email: {str(e)}")
            return False

class GameScoreSubmissionForm(forms.Form):
    """Secure form for submitting game scores"""
    
    game_id = forms.IntegerField(widget=forms.HiddenInput())
    score = forms.IntegerField(min_value=0)
    attempts = forms.IntegerField(min_value=1)
    duration = forms.IntegerField(
        min_value=1,
        help_text="Game duration in seconds"
    )
    game_data = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    # Security token to prevent score manipulation
    security_token = forms.CharField(widget=forms.HiddenInput())
    
    def __init__(self, game=None, player=None, *args, **kwargs):
        self.game = game
        self.player = player
        super().__init__(*args, **kwargs)
        
        if game:
            self.fields['score'].max_value = game.max_score
            self.fields['game_id'].initial = game.id
    
    def clean_security_token(self):
        """Validate security token"""
        token = self.cleaned_data.get('security_token')
        # Implement token validation logic
        if not self.validate_security_token(token):
            security_logger.warning(
                f"Invalid security token in score submission for game {self.game.id}"
            )
            raise ValidationError("Invalid security token.")
        return token
    
    def clean(self):
        cleaned_data = super().clean()
        score = cleaned_data.get('score')
        game_id = cleaned_data.get('game_id')
        
        # Validate score against game limits
        if self.game and score > self.game.max_score:
            raise ValidationError(f"Score cannot exceed {self.game.max_score}")
        
        # Additional anti-cheat validation
        if self.is_suspicious_score(cleaned_data):
            security_logger.warning(
                f"Suspicious score submission: {score} for game {game_id} by player {self.player.id if self.player else 'Unknown'}"
            )
            raise ValidationError("Score submission appears suspicious.")
        
        return cleaned_data
    
    def validate_security_token(self, token):
        """Implement security token validation"""
        # This would implement actual token validation
        return True  # Simplified for example
    
    def is_suspicious_score(self, data):
        """Check for suspicious scoring patterns"""
        score = data.get('score')
        duration = data.get('duration')
        attempts = data.get('attempts')
        
        if not all([score, duration, attempts]):
            return False
        
        # Check for impossibly high scores in short time
        if duration < 10 and score > self.game.max_score * 0.8:
            return True
        
        # Check for perfect scores with minimal attempts
        if score == self.game.max_score and attempts == 1 and duration < 5:
            return True
        
        return False
