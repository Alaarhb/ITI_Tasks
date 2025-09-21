from django.core.cache import cache
from django.contrib.auth.signals import user_login_failed, user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import hashlib
import secrets
import logging

security_logger = logging.getLogger('games.security')

class SecurityManager:
    """Security utilities for forms and user actions"""
    
    @staticmethod
    def generate_security_token(user_id, game_id, timestamp):
        """Generate security token for score submissions"""
        secret_key = settings.SECRET_KEY
        data = f"{user_id}:{game_id}:{timestamp}:{secret_key}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def validate_security_token(token, user_id, game_id, timestamp, max_age=300):
        """Validate security token"""
        # Check token age
        current_time = timezone.now().timestamp()
        if current_time - timestamp > max_age:
            return False
        
        expected_token = SecurityManager.generate_security_token(user_id, game_id, timestamp)
        return secrets.compare_digest(token, expected_token)
    
    @staticmethod
    def check_rate_limit(identifier, action, limit=5, period=300):
        """Check rate limiting for actions"""
        cache_key = f"rate_limit:{action}:{identifier}"
        current_count = cache.get(cache_key, 0)
        
        if current_count >= limit:
            return False
        
        cache.set(cache_key, current_count + 1, period)
        return True
    
    @staticmethod
    def log_suspicious_activity(user, activity, details):
        """Log suspicious user activity"""
        security_logger.warning(
            f"Suspicious activity - User: {user.username if user else 'Anonymous'}, "
            f"Activity: {activity}, Details: {details}"
        )
    
    @staticmethod
    def is_trusted_ip(ip_address):
        """Check if IP address is in trusted list"""
        trusted_ips = getattr(settings, 'TRUSTED_IPS', [])
        return ip_address in trusted_ips

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Log failed login attempts"""
    username = credentials.get('username', 'Unknown')
    ip_address = get_client_ip(request)
    
    security_logger.warning(f"Failed login attempt: {username} from {ip_address}")
    
    # Implement account lockout logic
    cache_key = f"failed_login:{username}"
    failed_attempts = cache.get(cache_key, 0) + 1
    
    if failed_attempts >= 5:
        # Lock account for 1 hour
        cache.set(f"account_locked:{username}", True, 3600)
        security_logger.error(f"Account locked: {username} due to repeated failed attempts")
    
    cache.set(cache_key, failed_attempts, 300)  # Reset counter after 5 minutes

@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    """Log successful login"""
    ip_address = get_client_ip(request)
    security_logger.info(f"Successful login: {user.username} from {ip_address}")
    
    # Clear failed login attempts
    cache.delete(f"failed_login:{user.username}")
    cache.delete(f"account_locked:{user.username}")

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip