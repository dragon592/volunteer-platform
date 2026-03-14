# Установка Railway CLI и исправление базы данных

## Шаг 1: Установка Railway CLI

### Вариант A: Через PowerShell (рекомендуется для Windows)

Открой **PowerShell от имени администратора** и выполни:

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
iwr https://railway.app/install.ps1 -UseBasicParsing | iex
```

### Вариант B: Через npm (если есть Node.js)

```bash
npm i -g @railway/cli
```

### Вариант C: Через scoop (если установлен)

```bash
scoop bucket add railway https://github.com/railwayapp/scoop-railway.git
scoop install railway
```

---

## Шаг 2: Проверка установки

В новом терминале (PowerShell или CMD) выполни:

```bash
railway --version
```

Должно вывести версию (например, `0.7.0`).

---

## Шаг 3: Авторизация

```bash
railway login
```

Откроется браузер - авторизуйся через GitHub/GitLab.

---

## Шаг 4: Подключение к проекту

Перейди в папку проекта:
```bash
cd c:/Users/MURA/Documents/volunteer-platform-main
```

Подключи проект:
```bash
railway link
```

Выбери свой проект `volunteer-platform` из списка.

---

## Шаг 5: Исправление базы данных

Теперь выполни команды для исправления:

```bash
railway console
```

В появившейся консоли (появится `>>>`) выполни:

```python
rm -f db.sqlite3
python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear
python import_data.py data_dump.json
exit
```

**Важно:** Каждую команду нажимай Enter.

---

## Шаг 6: Перезапуск сервиса

Выйди из консоли (команда `exit`), затем:

```bash
railway up
```

Или через dashboard: Services → Restart.

---

## Шаг 7: Проверка

1. Открой сайт в браузере
2. Страница событий должна работать
3. Проверь логи: `railway logs` или в dashboard

---

## Если что-то не работает

### Ошибка "command not found: railway"
- Перезапусти терминал после установки
- Убедись, что путь к Railway добавлен в PATH

### Ошибка "No projects found"
- Убедись, что ты в правильной директории проекта
- Попробуй `railway link --project <project-id>`
- project-id найди в URL dashboard: `https://railway.app/project/<project-id>`

### Ошибка при удалении db.sqlite3
- Файл может быть в другом месте. Проверь:
  ```bash
  ls -la *.sqlite3
  ```
- Удали найденный файл:
  ```bash
  rm -f <filename>.sqlite3
  ```

### Миграции не применяются
- Проверь, что в консоли Railway ты в папке `/app`
- Выполни `pwd` для проверки пути
- Если не в `/app`, перейди: `cd /app`

---

## Альтернатива: Исправить через nixpacks.toml

Если CLI не устанавливается, могу изменить `nixpacks.toml`, чтобы миграции применялись автоматически при каждом деплое с принудительным пересозданием базы. Это решит проблему без ручных действий.

Хочешь, чтобы я это сделал?