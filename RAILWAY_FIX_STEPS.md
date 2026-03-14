# Как исправить "no such table: events_event" в Railway

## Шаг 1: Удалить volume с SQLite базой

1. **Открой Railway dashboard**: https://railway.app/dashboard
2. **Выбери свой проект** (volunteer-platform)
3. **Перейди в раздел "Volumes"** в левом меню
4. **Найди volume** с именем:
   - Обычно называется `data` или `db`
   - Или содержит путь `/app/db.sqlite3`
5. **Нажми на volume**, чтобы открыть детали
6. **Нажми кнопку "Delete Volume"** (или иконку корзины)
7. **Подтверди удаление**

⚠️ **Важно:** Это удалит все данные в SQLite базе. После перезапуска миграции создадут чистую базу, а данные импортируются из `data_dump.json`.

---

## Шаг 2: Перезапустить деплой

1. **Перейди в раздел "Deployments"** (или "Services")
2. **Найди последний deployment** (может быть в статусе "failed" или "running")
3. **Нажми кнопку "Redeploy"** (или "Trigger Deploy")
   - Или кнопка "..." → "Redeploy"
4. **Дождись завершения** (обычно 1-2 минуты)

---

## Шаг 3: Проверить, что всё работает

1. **Открой сайт** в браузере (твой домен на .onrender.com или .railway.app)
2. **Перейди на страницу событий** - должна загружаться без ошибки 500
3. **Проверь логи** в Railway:
   - Deployments → выбери последний deployment → "Logs"
   - Убедись, что нет ошибок `no such table: events_event`
4. **Проверь, что миграции применены:**
   - Services → твой сервис → Console
   - В консоли выполни:
     ```bash
     python manage.py showmigrations events
     ```
   - Все миграции должны быть отмечены `[X]`

---

## Если проблема останется

Если после перезапуска ошибка всё ещё есть:

1. **Открой консоль Railway:**
   - Services → твой сервис → Console
   
2. **Выполни команды вручную:**
   ```bash
   python manage.py migrate --noinput
   python manage.py collectstatic --noinput --clear
   ```

3. **Перезапусти сервис:**
   - Services → твой сервис → Restart

---

## Что происходит при деплое

В `nixpacks.toml` настроена команда запуска:
```toml
cmd = "mkdir -p /app/staticfiles && python manage.py migrate --noinput && python manage.py collectstatic --noinput --clear && python import_data.py data_dump.json && gunicorn volunteer.wsgi:application --log-file -"
```

После удаления volume:
1. Создаётся новая пустая база SQLite
2. `migrate` создаёт все таблицы (включая `events_event`)
3. `collectstatic` собирает статику
4. `import_data.py` загружает данные из `data_dump.json`
5. Запускается gunicorn

---

## Примечание

Если в будущем захочешь использовать PostgreSQL вместо SQLite:
1. Добавь PostgreSQL в Railway: `railway add postgresql`
2. Установи переменную окружения `DATABASE_URL`
3. Удали SQLite volume
4. Перезапусти деплой

PostgreSQL надёжнее для production.