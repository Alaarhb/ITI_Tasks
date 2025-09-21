from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re
from PIL import Image

def validate_username(username):
    """Custom username validator"""
    if len(username) < 3:
        raise ValidationError(_('Username must be at least 3 characters long.'))
    
    if len(username) > 20:
        raise ValidationError(_('Username cannot exceed 20 characters.'))
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        raise ValidationError(_('Username can only contain letters, numbers, hyphens, and underscores.'))
    
    # Check for reserved usernames
    reserved_names = ['admin', 'root', 'user', 'test', 'guest', 'anonymous']
    if username.lower() in reserved_names:
        raise ValidationError(_('This username is reserved and cannot be used.'))

def validate_email_domain(email):
    """Validate email domain"""
    allowed_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
    domain = email.split('@')[-1].lower()
    
    if domain not in allowed_domains:
        raise ValidationError(
            _('Email domain must be one of: %(domains)s'),
            params={'domains': ', '.join(allowed_domains)},
        )

def validate_password_strength(password):
    """Custom password strength validator"""
    errors = []
    
    if len(password) < 8:
        errors.append(_('Password must be at least 8 characters long.'))
    
    if not re.search(r'[A-Z]', password):
        errors.append(_('Password must contain at least one uppercase letter.'))
    
    if not re.search(r'[a-z]', password):
        errors.append(_('Password must contain at least one lowercase letter.'))
    
    if not re.search(r'[0-9]', password):
        errors.append(_('Password must contain at least one digit.'))
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append(_('Password must contain at least one special character.'))
    
    # Check for common patterns
    common_patterns = ['123', 'abc', 'password', 'qwerty']
    for pattern in common_patterns:
        if pattern in password.lower():
            errors.append(_('Password cannot contain common patterns.'))
    
    if errors:
        raise ValidationError(errors)

def validate_profile_image(image):
    """Validate profile image"""
    # Check file size (max 2MB)
    if image.size > 2 * 1024 * 1024:
        raise ValidationError(_('Image file too large. Maximum size is 2MB.'))
    
    # Check image dimensions
    try:
        img = Image.open(image)
        if img.width < 50 or img.height < 50:
            raise ValidationError(_('Image must be at least 50x50 pixels.'))
        
        if img.width > 2000 or img.height > 2000:
            raise ValidationError(_('Image must not exceed 2000x2000 pixels.'))
    except Exception:
        raise ValidationError(_('Invalid image file.'))

def validate_no_profanity(text):
    """Simple profanity filter"""
    profanity_list = ['badword1', 'badword2', 'spam', 'fake']  # Add real words
    text_lower = text.lower()
    
    for word in profanity_list:
        if word in text_lower:
            raise ValidationError(_('Text contains inappropriate content.'))
