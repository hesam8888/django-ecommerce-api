from django.core.cache import cache
from django.conf import settings
from datetime import datetime, timedelta

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def is_rate_limited(request, key_prefix, max_attempts=5, cooldown_minutes=15):
    """
    Check if a request should be rate limited.
    
    Args:
        request: The HTTP request
        key_prefix: Prefix for the cache key
        max_attempts: Maximum number of attempts allowed
        cooldown_minutes: Minutes to wait after max attempts are reached
    
    Returns:
        tuple: (is_limited, remaining_attempts, cooldown_remaining)
    """
    ip = get_client_ip(request)
    cache_key = f"{key_prefix}:{ip}"
    
    # Get current attempts data
    attempts_data = cache.get(cache_key, {
        'attempts': 0,
        'first_attempt': datetime.now().timestamp(),
        'cooldown_until': None
    })
    
    # Check if in cooldown period
    if attempts_data['cooldown_until']:
        cooldown_remaining = attempts_data['cooldown_until'] - datetime.now().timestamp()
        if cooldown_remaining > 0:
            return True, 0, int(cooldown_remaining / 60)
        else:
            # Reset if cooldown period is over
            attempts_data = {
                'attempts': 0,
                'first_attempt': datetime.now().timestamp(),
                'cooldown_until': None
            }
    
    # Increment attempts
    attempts_data['attempts'] += 1
    
    # Check if max attempts reached
    if attempts_data['attempts'] >= max_attempts:
        attempts_data['cooldown_until'] = (datetime.now() + timedelta(minutes=cooldown_minutes)).timestamp()
        cache.set(cache_key, attempts_data, timeout=cooldown_minutes * 60)
        return True, 0, cooldown_minutes
    
    # Update cache
    cache.set(cache_key, attempts_data, timeout=cooldown_minutes * 60)
    
    return False, max_attempts - attempts_data['attempts'], 0 