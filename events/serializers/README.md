# Сериализаторы (Serializers)

## Описание

Сериализаторы преобразуют модели в JSON и валидируют входящие данные API.

## Структура

- `event_serializers.py` - Сериализаторы событий
- `registration_serializers.py` - Сериализаторы регистраций

## Принципы

1. **DRF Style** - наследуются от `serializers.ModelSerializer`
2. **Валидация** - методы `validate_*` для полей, `validate` для общей логики
3. **Read-only поля** - явно помечаются
4. **Вложенные сериализаторы** - для связанных объектов

## Пример

```python
class EventDetailSerializer(serializers.ModelSerializer):
    organizer = serializers.SerializerMethodField()
    can_register = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = ['id', 'title', 'organizer', 'can_register']
    
    def get_organizer(self, obj):
        return {
            'id': obj.organizer.id,
            'name': obj.organizer.get_full_name()
        }
    
    def get_can_register(self, obj):
        request = self.context.get('request')
        # логика проверки
        return True
```

## Использование

```python
# В контроллере или view
serializer = EventDetailSerializer(event, context={'request': request})
data = serializer.data
```
