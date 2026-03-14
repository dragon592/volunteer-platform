# Исправление проблемы "no such table: events_event" в Production

## Проблема
В production (Railway/Render) возникает ошибка:
```
sqlite3.OperationalError: no such table: events_event
```

Хотя миграции показываются как применённые, таблица `events_event` отсутствует в SQLite базе данных.

## Причина
В production используется volume (persistent storage) с SQLite файлом, который был создан ДО применения миграций. Когда контейнер запускается, он использует старый файл базы данных без таблиц.

## Решение

### Вариант 1: Удалить volume с базой данных (рекомендуется)

#### Для Railway:
```bash
# Удалить volume с базой данных
railway volume:rm db.sqlite3

# Или через Railway CLI:
railway console
rm /app/db.sqlite3
exit

# Перезапустить деплой
railway up
```

#### Для Render:
```bash
# Удалить volume через Render dashboard:
# 1. Перейдите в раздел "Volumes" вашего сервиса
# 2. Найдите volume с именем (обычно "data" или "db")
# 3. Удалите его

# Или через Render CLI:
render volumes:delete <volume-name> --service <service-name>

# Перезапустить сервис
render services:restart <service-name>
```

### Вариант 2: Применить миграции вручную через консоль контейнера

```bash
# Подключиться к контейнеру
railway console
# или
render ssh

# Внутри контейнера выполнить:
python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

# Выйти и перезапустить
exit
railway up  # или render services:restart
```

### Вариант 3: Использовать PostgreSQL вместо SQLite (наиболее надёжно)

1. **В Railway/Render создать PostgreSQL базу данных:**
   - Railway: `railway add postgresql`
   - Render: Создать отдельный PostgreSQL сервис

2. **Получить DATABASE_URL:**
   ```bash
   railway variables:get DATABASE_URL
   # или в Render dashboard в переменных окружения
   ```

3. **Установить переменную окружения в приложении:**
   ```
   DATABASE_URL=postgresql://user:password@host:port/dbname
   ```

4. **Удалить SQLite volume** (как в варианте 1)

5. **Перезапустить деплой** - миграции применятся к PostgreSQL

## Проверка после исправления

1. **Проверить, что таблица создана:**
   ```bash
   railway console
   python -c "from django.db import connection; cursor = connection.cursor(); cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='events_event'\"); print('Exists:', cursor.fetchone() is not None)"
   ```

2. **Проверить статус миграций:**
   ```bash
   python manage.py showmigrations events
   ```

3. **Проверить, что приложение работает:**
   - Открыть сайт в браузере
   - Убедиться, что страница со списком событий загружается без ошибок

## Примечание

Если в production используется SQLite с volume, убедитесь, что:
- Volume не смонтирован в режиме "read-only"
- У приложения есть права на запись в директорию с базой данных
- В `nixpacks.toml` команда `python manage.py migrate --noinput` выполняется ДО запуска gunicorn

В текущем `nixpacks.toml` это уже настроено правильно:
```toml
[start]
cmd = "mkdir -p /app/staticfiles && python manage.py migrate --noinput && python manage.py collectstatic --noinput --clear && python import_data.py data_dump.json && gunicorn volunteer.wsgi:application --log-file -"
```

Однако, если volume уже содержит старую базу без таблиц, миграции не смогут создать таблицы из-за блокировок или конфликтов. В этом случае помогает полное удаление volume.