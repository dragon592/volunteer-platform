# План рефакторинга архитектуры платформы волонтёров

## 📊 Анализ текущего состояния

### Проблемы выявленные:
1. **Смешанная архитектура** - бизнес-логика в view-функциях
2. **Дублирование кода** - проверка профиля повторяется 10+ раз
3. **Отсутствие централизованной обработки ошибок**
4. **N+1 запросы** в event_detail, leaderboard
5. **Нет валидации на API уровне**
6. **Монолитный JavaScript** без модульности
7. **Устаревший роутинг** - можно улучшить

## 🎯 Цели рефакторинга

1. **Разделение ответственности** - Controllers/Services/Views
2. **Централизованная обработка ошибок** - ErrorHandlerMiddleware
3. **Валидация** - Serializers + Validators
4. **Оптимизация запросов** - select_related/prefetch_related
5. **Модульный фронтенд** - API Service + Components + Hooks
6. **Безопасность** - улучшенная валидация, rate limiting
7. **Производительность** - кэширование, индексы

## 📁 Новая структура проекта

```
events/
├── controllers/           # Контроллеры (бизнес-логика)
│   ├── __init__.py
│   ├── event_controller.py
│   ├── profile_controller.py
│   ├── chat_controller.py
│   ├── notification_controller.py
│   └── auth_controller.py
├── serializers/           # Сериализаторы для API
│   ├── __init__.py
│   ├── event_serializers.py
│   └── registration_serializers.py
├── validators/            # Кастомные валидаторы
│   ├── __init__.py
│   ├── event_validators.py
│   └── user_validators.py
├── middleware/
│   ├── error_handler.py       # Глобальный обработчик ошибок
│   └── rest_exception_handler.py  # Для DRF
├── services.py            # Служебные функции (остается)
├── selectors.py           # Запросы (остается)
├── forms.py               # Формы Django (остается)
├── models.py              # Модели (улучшены)
├── views_*.py             # View-функции (упрощены)
└── urls.py                # Роуты (остается)

static/events/js/
├── services/
│   └── api.js            # Единый API клиент
├── components/
│   └── EventCard.js      # Компонент карточки события
└── hooks/
    └── useEvents.js      # Кастомный хук для событий
```

## 🔄 Основные изменения

### Бэкенд

#### 1. Контроллеры
- `EventController` - управление событиями
- `ProfileController` - управление профилями
- `ChatController` - управление чатом
- `NotificationController` - управление уведомлениями
- `AuthController` - аутентификация

#### 2. Сериализаторы
- `EventListSerializer` - список событий
- `EventDetailSerializer` - детали события
- `EventCreateUpdateSerializer` - создание/обновление
- `EventRegistrationSerializer` - регистрация

#### 3. Валидаторы
- `validate_event_date()` - дата не в прошлом
- `validate_max_volunteers()` - лимиты участников
- `validate_xp_reward()` - лимиты XP
- `validate_unique_email()` - уникальность email

#### 4. Middleware
- `ErrorHandlerMiddleware` - глобальная обработка ошибок
- `rest_exception_handler` - для DRF API

#### 5. Оптимизации
- Добавлен `get_absolute_url()` в Notification
- Улучшены индексы в моделях
- Исправлены N+1 запросы через `select_related`/`prefetch_related`

### Фронтенд

#### 1. API Service (`api.js`)
- Единый клиент для всех запросов
- Обработка CSRF токенов
- Централизованная обработка ошибок
- Поддержка всех сущностей (Events, Profiles, Chat, Notifications, Auth)

#### 2. Components
- `EventCard` - переиспользуемый компонент карточки события
- Поддержка обновления данных
- Адаптивный дизайн

#### 3. Hooks
- `useEvents()` - управление состоянием событий
- Подписка на изменения
- Автоматическая загрузка
- Фильтрация и пагинация

#### 4. Улучшения в `app.js`
- Модульная структура
- Интеграция API сервиса
- Обработка регистрации через API
- Бесконечная прокрутка (опционально)

## 🐛 Исправленные баги

1. **Аватар организатора** - добавлена проверка на наличие аватара
2. **Registered count** - используется правильное свойство `registered_count`
3. **Полные события** - кнопка показывает "Полный" когда мест нет
4. **Дублирование инициализации** - убрано дублирование `DOMContentLoaded`

## 🚀 Производительность

1. **Кэширование** - частые запросы кэшируются
2. **Индексы** - добавлены в модели:
   - `Event`: `is_active`, `date`, `city`
   - `EventRegistration`: `event`, `status`, `volunteer`
   - `Notification`: `user`, `is_read`
3. **select_related** - для ForeignKey
4. **prefetch_related** - для ManyToMany
5. **distinct()** - предотвращение дублей при фильтрации

## 🔒 Безопасность

1. **Валидация** - на всех уровнях (forms, serializers, validators)
2. **Rate Limiting** - расширен (уже был, добавлены новые лимиты)
3. **CSRF Protection** - через API сервис
4. **SQL Injection** - защищено через ORM
5. **XSS** - экранирование в шаблонах

## 📝 Миграция

### Шаги для развертывания:

1. Установить зависимости:
```bash
pip install -r requirements.txt
```

2. Применить миграции (если добавлены новые):
```bash
python manage.py makemigrations
python manage.py migrate
```

3. Обновить middleware в `settings.py`:
```python
MIDDLEWARE = [
    ...
    'events.middleware.error_handler.ErrorHandlerMiddleware',
]
```

4. Добавить REST Framework в `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    ...
    'rest_framework',
]
```

5. Собрать статику:
```bash
python manage.py collectstatic
```

## 🧪 Тестирование

Рекомендуется протестировать:
- [ ] Все endpoints API
- [ ] Регистрацию и вход
- [ ] Создание/редактирование событий
- [ ] Регистрацию на события
- [ ] Чат и уведомления
- [ ] Обработку ошибок
- [ ] Валидацию форм
- [ ] Производительность (N+1 запросы)

## 📈 Дальнейшие улучшения

1. **API Documentation** - Swagger/OpenAPI
2. **Unit Tests** - покрытие контроллеров и сервисов
3. **Integration Tests** - полные сценарии
4. **Caching** - Redis для частых запросов
5. **WebSocket** - для реального времени в чате
6. **Docker** - контейнеризация
7. **CI/CD** - автоматические тесты и деплой

## 📚 Документация

- `README.md` - общее описание
- `ARCHITECTURE.md` - детали архитектуры
- `API.md` - документация API endpoints
- `DEPLOYMENT.md` - инструкции по деплою

---

**Статус:** ✅ Рефакторинг завершен
**Дата:** 2025-03-16
**Версия:** 2.0
