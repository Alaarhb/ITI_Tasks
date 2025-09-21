from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from captcha.fields import CaptchaField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML, Div
from crispy_forms.bootstrap import Field
from games.models import Player, Game, GameScore, Category
from games.validators import (
    validate_username, validate_email_domain, 
    validate_password_strength, validate_profile_image, validate_no_profanity
)

class SecureUserRegistrationForm(UserCreationForm):
    """Secure user registration form using ModelForm"""
    
    email = forms.EmailField(
        required=True,
        validators=[validate_email_domain],
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autocomplete': 'email'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        validators=[validate_no_profanity],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name',
            'autocomplete': 'given-name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        validators=[validate_no_profanity],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name',
            'autocomplete': 'family-name'
        })
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="I accept the Terms of Service and Privacy Policy"
    )
    
    captcha = CaptchaField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter CAPTCHA'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Custom validation for username
        self.fields['username'].validators.append(validate_username)
        self.fields['password1'].validators.append(validate_password_strength)
        
        # Widget customization
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username',
            'autocomplete': 'username'
        })
        
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a strong password',
            'autocomplete': 'new-password'
        })
        
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password'
        })
        
        # Crispy Forms Helper
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            HTML('<h3 class="mb-4">Create Your Account</h3>'),
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('username', css_class='mb-3'),
            Field('email', css_class='mb-3'),
            Row(
                Column('password1', css_class='form-group col-md-6 mb-3'),
                Column('password2', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('captcha', css_class='mb-3'),
            Div(
                Field('terms_accepted', css_class='form-check'),
                css_class='mb-3'
            ),
            Submit('submit', 'Create Account', css_class='btn btn-primary btn-lg w-100')
        )
    
    def clean_email(self):
        """Custom email validation"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email
    
    def clean_username(self):
        """Custom username validation"""
        username = self.cleaned_data.get('username')
        
        # Check if username is taken
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken.")
        
        return username
    
    def clean(self):
        """Form-level validation"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        username = cleaned_data.get('username')
        
        # Check password similarity to username
        if username and password1 and username.lower() in password1.lower():
            raise ValidationError("Password cannot be too similar to username.")
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save user with additional security measures"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Create associated Player profile
            Player.objects.create(
                user=user,
                name=user.username,
                email=user.email,
                bio=f"Welcome {user.first_name}! Ready to play some games?",
                is_public=True
            )
        
        return user

class PlayerProfileForm(forms.ModelForm):
    """Secure player profile form"""
    
    avatar_image = forms.ImageField(
        required=False,
        validators=[validate_profile_image],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    class Meta:
        model = Player
        fields = ['name', 'email', 'bio', 'avatar_image', 'preferred_difficulty', 'is_public', 'show_email']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Display name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email address'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about yourself...'
            }),
            'preferred_difficulty': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'show_email': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add validators
        self.fields['name'].validators.append(validate_no_profanity)
        self.fields['bio'].validators.append(validate_no_profanity)
        
        # Crispy Forms Helper
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            HTML('<h3 class="mb-4">Profile Settings</h3>'),
            Row(
                Column('name', css_class='form-group col-md-6 mb-3'),
                Column('email', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('bio', css_class='mb-3'),
            Field('avatar_image', css_class='mb-3'),
            Row(
                Column('preferred_difficulty', css_class='form-group col-md-6 mb-3'),
                Column(
                    Div(
                        Field('is_public', css_class='form-check mb-2'),
                        Field('show_email', css_class='form-check'),
                        css_class='mt-3'
                    ),
                    css_class='form-group col-md-6'
                ),
                css_class='form-row'
            ),
            Submit('submit', 'Update Profile', css_class='btn btn-success')
        )
    
    def clean_name(self):
        """Validate unique display name"""
        name = self.cleaned_data.get('name')
        if self.instance and self.instance.name == name:
            return name
        
        if Player.objects.filter(name__iexact=name).exists():
            raise ValidationError("This display name is already taken.")
        
        return name

class GameFeedbackForm(forms.ModelForm):
    """Secure game feedback form"""
    
    RATING_CHOICES = [
        (1, '⭐ Poor'),
        (2, '⭐⭐ Fair'),
        (3, '⭐⭐⭐ Good'),
        (4, '⭐⭐⭐⭐ Very Good'),
        (5, '⭐⭐⭐⭐⭐ Excellent'),
    ]
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    feedback_text = forms.CharField(
        max_length=1000,
        validators=[validate_no_profanity],
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Share your thoughts about this game...'
        }),
        label="Your Feedback"
    )
    
    recommend = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Would you recommend this game to others?"
    )
    
    captcha = CaptchaField()
    
    class Meta:
        model = GameScore  # We'll extend this model to include feedback
        fields = ['rating', 'feedback_text', 'recommend']
    
    def __init__(self, *args, **kwargs):
        self.game = kwargs.pop('game', None)
        self.player = kwargs.pop('player', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            HTML('<h4 class="mb-4">Rate & Review</h4>'),
            Field('rating', css_class='mb-3'),
            Field('feedback_text', css_class='mb-3'),
            Field('recommend', css_class='form-check mb-3'),
            Field('captcha', css_class='mb-3'),
            Submit('submit', 'Submit Feedback', css_class='btn btn-primary')
        )