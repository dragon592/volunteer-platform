# Валидаторы (Validators)

## Описание

Кастомные валидаторы для повторного использования в формах и сериализаторах.

## Структура

- `event_validators.py` - Валидаторы для событий
- `user_validators.py` - Валидаторы для пользователей

## Принципы

1. **Чистые функции** - не имеют побочных эффектов
2. **Возврат значения** - возвращают валидное значение или вызывают `ValidationError`
3. **Переиспользование** - используются в формах, сериализаторах, моделях

## Пример

```python
# validators/event_validators.py
def validate_event_date(value):
    if value < timezone.localdate():
        raise ValidationError('Дата не может быть в прошлом.')
    return value

# forms.py
class EventForm(forms.ModelForm):
    date = forms.DateField(validators=[validate_event_date])
    
# serializers.py
class EventSerializer(serializers.ModelSerializer):
    date = serializers.DateField(validators=[validate_event_date])
```

## Доступные валидаторы

### События
- `validate_event_date()` - дата в будущем
- `validate_max_volunteers()` - лимиты участников (1-1000)
- `validate_xp_reward()` - лимиты XP (0-10000)
- `validate_date_range()` - диапазон дат

### Пользователи
- `validate_unique_email()` - email не занят
