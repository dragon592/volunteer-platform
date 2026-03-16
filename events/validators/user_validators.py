"""
Валидаторы для пользователей и профилей.
"""
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


def validate_unique_email(email, user_id=None):
    """Проверяет, что email не используется другим пользователем"""
    qs = User.objects.filter(email=email)
    if user_id:
        qs = qs.exclude(id=user_id)
    if qs.exists():
        raise ValidationError('Этот email уже используется другим аккаунтом.')
    return email
