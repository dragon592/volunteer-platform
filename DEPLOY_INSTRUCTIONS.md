# 🚀 Инструкция по деплою на Render.com с переносом базы данных

## 📋 Что уже сделано

✅ Настроен `settings.py` для работы с PostgreSQL через `DATABASE_URL`
✅ Добавлен `psycopg2-binary` в `requirements.txt`
✅ Настроен `whitenoise` для статических файлов
✅ Готов `build.sh` скрипт для автоматической сборки
✅ Созданы все миграции
✅ Созданы скрипты `export_data.py` и `import_data.py` для экспорта/импорта данных

---

## 🔄 План действий

### 1. Подготовка данных из локальной SQLite

#### 1.1 Создание дампа данных (JSON)
```bash
cd c:/Users/MURA/Documents/volunteer-platform-main
.\venv\Scripts\python.exe export_data.py
```

**Что делает скрипт:**
- Экспортирует все данные из SQLite базы в `data_dump.json`
- Использует UTF-8 кодировку (работает на Windows без ошибок)
- Показывает статистику по экспортированным объектам

**Результат:**
```
✅ Данные успешно экспортированы в data_dump.json (23.17 KB)
📊 Экспортировано объектов: 64
```

#### 1.2 Проверка дампа
```bash
type data_dump.json | findstr "events\|auth_user"
```
Должны увидеть данные о пользователях и событиях.

---

### 2. Создание аккаунта на Render.com

1. Перейдите на [render.com](https://render.com)
2. Зарегистрируйтесь (можно через GitHub)
3. Подтвердите email

---

### 3. Создание PostgreSQL базы данных

1. В дашборде Render нажмите **"New"** → **"PostgreSQL"**
2. Настройте:
   - **Name**: `volunteer-platform-db` (или любое другое)
   - **Region**: выберите ближайший (например, `Frankfurt` для Европы)
   - **Plan**: `Free`
3. Нажмите **"Create Database"**
4. **Скопируйте `Connection String`** (покажет после создания)
   - Выглядит как: `postgresql://username:password@hostname:port/database`

---

### 4. Деплой веб-сервиса

#### 4.1 Загрузка кода на GitHub (если ещё не загружено)

```bash
cd c:/Users/MURA/Documents/volunteer-platform-main

# Инициализировать git (если не было)
git init

# Добавить remote (замените на ваш репозиторий)
git remote add origin https://github.com/username/volunteer-platform.git

# Добавить все файлы
git add .

# Создать коммит
git commit -m "Подготовка к деплою на Render"

# Отправить на GitHub
git push -u origin main
```

#### 4.2 Создание Web Service на Render

1. В дашборде Render нажмите **"New"** → **"Web Service"**
2. Подключите ваш GitHub репозиторий
3. Настройте:
   - **Name**: `volunteer-platform` (или любое)
   - **Region**: тот же, что у БД
   - **Plan**: `Free`
   - **Branch**: `main` (или ваша ветка)
   - **Build Command**: `bash build.sh` (уже указан в render.yaml)
   - **Start Command**: `gunicorn volunteer.wsgi:application` (уже указан)
4. python -c "import secrets; print(secrets.token_urlsafe(50))"
5. Нажмите **"Create Web Service"**

Render начнёт сборку и деплой. Это займет 5-10 минут.

---

### 5. Перенос данных из SQLite в PostgreSQL

**После успешного деплоя** (статус "Live") нужно загрузить данные:

#### 5.1 Получите DATABASE_URL с Render
1. Перейдите в настройки вашей PostgreSQL базы
2. Скопируйте `Connection String`

#### 5.2 Установите переменную окружения локально
```bash
set DATABASE_URL=postgresql://username:password@hostname:port/database
```
Или в PowerShell:
```powershell
$env:DATABASE_URL="postgresql://username:password@hostname:port/database"
```

#### 5.3 Проверьте подключение к базе данных
```bash
.\venv\Scripts\python.exe manage.py check
```
Должно показать `System check identified no issues (0 silenced).`

#### 5.4 Примените миграции на Render БД
```bash
cd c:/Users/MURA/Documents/volunteer-platform-main
.\venv\Scripts\python.exe manage.py migrate --noinput
```

#### 5.5 Загрузите данные из дампа
```bash
.\venv\Scripts\python.exe import_data.py
```
Или явно укажите файл:
```bash
.\venv\Scripts\python.exe import_data.py data_dump.json
```

#### 5.6 Проверьте данные
```bash
.\venv\Scripts\python.exe manage.py shell
```
```python
from events.models import Event, UserProfile
print(f"Events: {Event.objects.count()}")
print(f"Users: {UserProfile.objects.count()}")
exit()
```

---

### 6. Финальные проверки

#### 6.1 Проверьте, что статические файлы собраны
Render автоматически запускает `collectstatic` через `build.sh`. Проверьте в логах деплоя, что файлы собрались.

#### 6.2 Откройте сайт
Render предоставит URL вида: `https://volunteer-platform.onrender.com`

#### 6.3 Проверьте:
- ✅ Главная страница загружается
- ✅ Авторизация работает
- ✅ События отображаются
- ✅ Статические файлы (CSS/JS) загружаются

---

## ⚠️ Возможные проблемы и решения

### Проблема: `psycopg2` не устанавливается на Windows
**Решение:** Мы используем `psycopg2-binary`, который работает на Windows. На Render (Linux) тоже будет работать.

### Проблема: Ошибка `relation "events_event" does not exist`
**Решение:** Миграции не были применены. Запустите `manage.py migrate` с `DATABASE_URL`.

### Проблема: Статические файлы не загружаются
**Решение:** 
1. Проверьте, что `whitenoise` добавлен в `MIDDLEWARE` (уже сделано)
2. Проверьте лог `collectstatic` в Render
3. Убедитесь, что `STATIC_ROOT` настроен (уже `BASE_DIR / 'staticfiles'`)

### Проблема: Сайт не открывается, ошибка 404
**Решение:** 
1. Проверьте `ALLOWED_HOSTS` в settings.py (должен включать `*.onrender.com`)
2. Перезапустите сервис на Render

### Проблема: Ошибка при `loaddata` (дублирование или несуществующие зависимости)
**Решение:** 
1. Очистите базу: `manage.py flush` (осторожно, удалит все данные!)
2. Примените миграции: `manage.py migrate`
3. Загрузите дамп заново

---

## 📝 Дополнительные настройки (опционально)

### Кастомный домен
1. В настройках Web Service на Render добавьте Custom Domain
2. Настройте DNS у вашего регистратора:
   - Type: `CNAME`
   - Name: `www` (или ваш поддомен)
   - Value: `volunteer-platform.onrender.com`

### SSL
Render автоматически предоставляет SSL для custom domains.

---

## 🎯 Краткая шпаргалка

```bash
# 1. Экспорт данных из SQLite
.\venv\Scripts\python.exe export_data.py

# 2. Установка DATABASE_URL (локально для тестирования)
$env:DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# 3. Проверка подключения
.\venv\Scripts\python.exe manage.py check

# 4. Применение миграций на новой БД
.\venv\Scripts\python.exe manage.py migrate

# 5. Загрузка данных
.\venv\Scripts\python.exe import_data.py

# 6. Сбор статики (локально для проверки)
.\venv\Scripts\python.exe manage.py collectstatic --noinput
```

---

## ✅ Готово!

После выполнения всех шагов ваш volunteer-platform будет работать на Render.com с перенесённой базой данных.

**Важно:** Бесплатный план Render усыпляет сервис после 15 минут бездействия. Первый пробуждение может занять 30-60 секунд.