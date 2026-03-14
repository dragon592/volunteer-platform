# Исправление ошибки "no such table: events_event" в Railway

## Если у тебя НЕТ раздела Volumes в Railway dashboard

### Шаг 1: Открой консоль Railway

1. Зайди в **Railway dashboard** → выбери проект
2. Перейди в **Services** → выбери свой сервис (обычно "web")
3. Нажди вкладку **Console** (или кнопку "Open Console")
4. Дождись подключения (появится чёрный терминал)

### Шаг 2: Выполни эти команды в консоли (копируй и вставляй)

```bash
rm -f db.sqlite3
python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear
python import_data.py data_dump.json
exit
```

### Шаг 3: Перезапусти сервис

1. В Railway dashboard: **Services** → твой сервис
2. Нажми **"..."** (меню) → **Restart**

### Шаг 4: Проверь

- Открой сайт в браузере
- Страница событий должна загружаться без ошибки 500
- Проверь логи: **Deployments** → последний deployment → **Logs**

---

## Если команды не работают

Возможно, у тебя другой путь к базе. Проверь:
```bash
ls -la *.sqlite3
```

Если файл называется иначе, удали его:
```bash
rm -f <имя_файла>.sqlite3
```

---

## Что делают команды:

1. `rm -f db.sqlite3` - удаляет старую повреждённую базу
2. `python manage.py migrate --noinput` - создаёт все таблицы заново
3. `python manage.py collectstatic --noinput --clear` - собирает статику
4. `python import_data.py data_dump.json` - загружает тестовые данные
5. `exit` - выходит из консоли

---

## Примечание

Если после перезапуска ошибка вернётся, значит Railway использует ephemeral filesystem без volume. В этом случае нужно добавить volume в `railway.json`:

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn volunteer.wsgi:application --log-file -",
    "healthcheckPath": "/",
    "restartPolicy": {
      "type": "ON_FAILURE"
    }
  },
  "volumes": [
    {
      "name": "data",
      "mountPath": "/app"
    }
  ]
}
```

Затем сделай новый деплой (push в git).