# Контроллеры (Controllers)

## Описание

Контроллеры содержат бизнес-логику приложения и отделяют её от view-функций.

## Структура

- `event_controller.py` - Управление событиями
- `profile_controller.py` - Управление профилями
- `chat_controller.py` - Управление чатом
- `notification_controller.py` - Управление уведомлениями
- `auth_controller.py` - Аутентификация

## Принципы

1. **Статические методы** - контроллеры не хранят состояние
2. **Возврат данных** - возвращают словари для шаблонов или объекты ответов
3. **Обработка ошибок** - выбрасывают исключения, которые обрабатываются в view
4. **Транзакции** - используют `@transaction.atomic` для атомарных операций

## Пример использования

```python
# В view-функции
def event_list(request):
    try:
        context = EventController.get_event_list(request)
        return render(request, 'events/event_list.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')
        return redirect('event_list')
```

## Миграция со старых view

Старые view-функции были рефакторингованы:
- Бизнес-логика перемещена в контроллеры
- View стали тонкими (только обработка запроса/ответа)
- Обработка ошибок централизована
