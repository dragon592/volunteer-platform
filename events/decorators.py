from functools import wraps

from django.core.cache import cache
from django.http import JsonResponse


def get_client_ip(request):
    """
    Получает IP адрес клиента с учетом прокси.
    Использует HTTP_X_FORWARDED_FOR если доступен, иначе REMOTE_ADDR.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Берем первый IP из списка (клиент)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip


def rate_limit(key_prefix, limit=120, window_seconds=60):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            user_part = f"user:{request.user.pk}" if request.user.is_authenticated else "anon"
            ip = get_client_ip(request)
            cache_key = f"rl:{key_prefix}:{user_part}:{ip}"

            current = cache.get(cache_key, 0)
            if current >= limit:
                return JsonResponse(
                    {'detail': 'Too many requests, please retry later.'},
                    status=429,
                )

            if current == 0:
                cache.set(cache_key, 1, timeout=window_seconds)
            else:
                try:
                    cache.incr(cache_key)
                except ValueError:
                    cache.set(cache_key, 1, timeout=window_seconds)

            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
