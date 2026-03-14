# Деплой на Render с PostgreSQL

## Шаг 1: Подготовка репозитория

Убедись, что все изменения закоммичены и запушены:

```cmd
git add .
git commit -m "Prepare for Render deployment"
git push
```

## Шаг 2: Создание PostgreSQL базы данных на Render

1. **Зайди на Render dashboard**: https://dashboard.render.com
2. **Нажми "New"** → **"PostgreSQL"**
3. **Заполни параметры:**
   - Name: `volunteer-db` (или любое другое)
   - Region: выбери ближайший
   - Plan: Free (или другой)
4. **Нажми "Create Database"**
5. **Дождись создания** (1-2 минуты)
6. **Скопируй "Connection String"** (кнопка "Copy")
   - Выглядит как: `postgresql://user:password@host:port/dbname`

## Шаг 3: Создание Web Service

1. **Нажми "New"** → **"Web Service"**
2. **Подключи GitHub репозиторий:**
   - Выбери свой аккаунт
   - Выбери репозиторий `volunteer-platform`
3. **Настройки:**
   - Name: `volunteer-platform` (или другое)
   - Environment: **Python 3**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn volunteer.wsgi:application --log-file -`
4. **Environment Variables:**
   - `DATABASE_URL` = (вставь connection string из PostgreSQL)
   - `DEBUG` = `False`
   - `SECRET_KEY` = (сгенерируй случайную строку, например через: `python -c "import secrets; print(secrets.token_urlsafe(50))"`)
   - `ALLOWED_HOSTS` = `.onrender.com`
   - `DJANGO_SETTINGS_MODULE` = `volunteer.settings`
5. **Нажми "Create Web Service"**

## Шаг 4: Настройка Build Command (альтернативный вариант)

Render автоматически выполнит:
- `pip install -r requirements.txt`
- `python manage.py collectstatic --noinput`
- `python manage.py migrate --noinput`

Если нужно импортировать данные, добавь в `buildCommand`:
```
pip install -r requirements.txt && python manage.py collectstatic --noinput --clear && python manage.py migrate --noinput && python import_data.py data_dump.json
```

## Шаг 5: Дождись деплоя

- Render автоматически запустит build и deploy
- Это займёт 5-10 минут
- Следи за логами в разделе "Logs"

## Шаг 6: Проверка

1. **Открой сайт** по адресу: `https://volunteer-platform.onrender.com` (или твой домен)
2. **Проверь, что:**
   - Страница событий загружается без ошибок
   - Статика (CSS, JS) работает
   - Данные импортированы (если использовал import_data.py)

## Шаг 7: Настройка Custom Domain (опционально)

Если хочешь свой домен:
1. **Settings** → **Custom Domains**
2. **Add Custom Domain**
3. Следуй инструкциям по настройке DNS

---

## Важные замечания

### PostgreSQL вместо SQLite
- Render не поддерживает SQLite в production (ephemeral filesystem)
- Используется PostgreSQL, который сохраняет данные между деплеями
- Настройки в `settings.py` уже поддерживают `DATABASE_URL` через `dj_database_url`

### Миграции
- Применяются автоматически при каждом деплое через `buildCommand`
- Если нужно, можно запустить вручную через Render Console:
  ```bash
  python manage.py migrate --noinput
  ```

### Статика
- Собирается автоматически в `buildCommand`
- Render автоматически обслуживает статику через WhiteNoise

### Логи
- Просмотр логов: Render Dashboard → Web Service → Logs
- Можно также использовать Render CLI: `render logs`

---

## Устранение проблем

### Ошибка "no such table: events_event"
Убедись, что:
1. `DATABASE_URL` установлен правильно
2. Миграции применяются: `python manage.py migrate --noinput`
3. В логах build есть строки `Applying events.0001_initial... OK`

### Ошибка со статикой
Проверь, что `collectstatic` выполняется без ошибок. Если нужно, добавь в `settings.py`:
```python
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Ошибка импорта данных
Если `import_data.py` падает, проверь:
- Файл `data_dump.json` существует в репозитории
- Формат JSON корректный
- Достаточно места в диске

---

## Резервное копирование

PostgreSQL база на Render автоматически бэкапится. Для дополнительного бэкапа:
1. Используй `pg_dump` через Render Console
2. Или настрой periodic backups в Render dashboard

---

## Масштабирование

- Бесплатный план имеет ограничения (750 часов/месяц, 512 MB RAM)
- Для продакшена рассмотрите платные планы
- Можно добавить Redis для кэширования через Render Add-ons