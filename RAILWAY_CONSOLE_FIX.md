# Исправление через Railway Console (если нет Volumes)

## Шаг 1: Открыть консоль Railway

1. **Railway dashboard** → твой проект
2. **Services** → выбери сервис (обычно "web" или "app")
3. **Вкладка "Console"** (или кнопка "Open Console")
4. Дождись подключения (появится терминал)

---

## Шаг 2: Проверить текущее состояние

В консоли выполни:
```bash
python manage.py showmigrations events
```

Посмотри, какие миграции отмечены [X]. Если `0001_initial` не отмечен - таблица не создана.

---

## Шаг 3: Применить миграции

```bash
python manage.py migrate --noinput
```

Должно вывести:
```
Operations to perform:
  Apply all migrations: events, admin, auth, contenttypes, sessions
Running migrations:
  Applying events.0001_initial... OK
  ...
```

---

## Шаг 4: Собрать статику

```bash
python manage.py collectstatic --noinput --clear
```

---

## Шаг 5: Импортировать данные

```bash
python import_data.py data_dump.json
```

---

## Шаг 6: Перезапустить сервис

1. **Services** → твой сервис
2. **Кнопка "..."** (меню) → **Restart**

Или через консоль:
```bash
exit
# И затем в dashboard: Restart
```

---

## Шаг 7: Проверить

1. Открой сайт
2. Проверь логи (Deployments → Logs)
3. Ошибки `no such table: events_event` быть не должно

---

## Если миграции уже применены, но таблица отсутствует

Возможно база повреждена или создана не полностью. Тогда:

```bash
# Удалить базу
rm db.sqlite3

# Применить миграции заново
python manage.py migrate --noinput

# Импортировать данные
python import_data.py data_dump.json
```

---

## Примечание

Если после перезапуска база сбрасывается (таблица исчезает снова), значит Railway использует ephemeral filesystem. В этом случае нужно:

1. **Добавить volume** (Railway автоматически создаст при следующем деплое):
   - В `railway.json` добавь:
   ```json
   {
     "volumes": [
       {
         "name": "data",
         "mountPath": "/app"
       }
     ]
   }
   ```
2. **Или перейти на PostgreSQL** (рекомендуется):
   ```bash
   railway add postgresql
   ```
   DATABASE_URL установится автоматически.