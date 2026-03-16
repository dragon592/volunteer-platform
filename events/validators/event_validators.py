"""
Валидаторы для событий.
"""
from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_event_date(value):
    """Валидация даты события (не может быть в прошлом)"""
    if value < timezone.localdate():
        raise ValidationError('Дата события не может быть в прошлом.')
    return value


def validate_max_volunteers(value):
    """Валидация максимального количества волонтеров"""
    if value < 1:
        raise ValidationError('Количество участников не может быть меньше 1.')
    if value > 1000:
        raise ValidationError('Количество участников не может превышать 1000.')
    return value


def validate_xp_reward(value):
    """Валидация XP награды"""
    if value < 0:
        raise ValidationError('XP награда не может быть отрицательной.')
    if value > 10000:
        raise ValidationError('XP награда не может превышать 10000.')
    return value


def validate_date_range(date_from, date_to):
    """Валидация диапазона дат"""
    if date_from and date_to and date_from > date_to:
        raise ValidationError('Дата "от" не может быть позже даты "до".')
    return True
