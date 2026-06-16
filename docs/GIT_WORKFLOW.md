[#033]
Привет. Понял задачу. Делаю исчерпывающее руководство по Git-процессу для «Числяндии». Сохрани как `docs/GIT_WORKFLOW.md`.

---

## 📄 Файл: `docs/GIT_WORKFLOW.md`

```markdown
# 🌿 Git Workflow — Правила работы с репозиторием «Числяндия»

> **Версия документа:** 1.0  
> **Дата:** 2026-04-06  
> **Принцип:** «Медленно, но правильно». Стабильность `master` — приоритет №1.

---

## 📋 Оглавление
1. [Основные принципы](#1-основные-принципы)
2. [Настройка репозитория](#2-настройка-репозитория)
3. [Рабочий процесс: от фичи к мержу](#3-рабочий-процесс-от-фичи-к-мержу)
4. [Формат сообщений коммитов](#4-формат-сообщений-коммитов)
5. [Откаты и исправление ошибок](#5-откаты-и-исправление-ошибок)
6. [Теги и версии](#6-теги-и-версии)
7. [Чеклисты](#7-чеклисты)
8. [Безопасность](#8-безопасность)
9. [Шпаргалка по командам](#9-шпаргалка-по-командам)

---

## 1. Основные принципы

| Правило | Описание |
|---------|----------|
| 🔒 `master` = стабильно | В `master` попадает только протестированный, рабочий код. Никаких экспериментов. |
| 🌿 Разработка только в ветках | Каждая фича/багфикс → отдельная ветка `feature/...` или `fix/...` |
| 📝 Один коммит = одна задача | Не смешивай правки конфига, баг в хендлере и обновление доков в одном коммите. |
| 🧹 Чистый репозиторий | Никогда не коммить артефакты сборки, кэш, секреты, БД. |
| 🏷️ Теги для релизов | Каждая стабильная версия помечается тегом `vX.Y-stable`. |

---

## 2. Настройка репозитория

### `.gitignore` (обязательный минимум)
Создай файл `.gitignore` в корне, если его нет:
```gitignore
# 🔐 Секреты и окружение
.env
.env.local
.env.max
.env.backup
*.key
*.pem

# 🗄️ Базы данных и данные
data/*.db
data/*.db-shm
data/*.db-wal
data/*.sqlite
data/progress_backup_*.db

# 🐍 Python
__pycache__/
*.py[cod]
*$py.class
*.so
*.egg-info/
dist/
build/
venv/
.venv/

# 🟢 Node.js / React
frontend/node_modules/
frontend/dist/
frontend/.vite/
package-lock.json  # (опционально, но рекомендуется игнорировать если есть конфликты)

# 📝 Логи и временные файлы
logs/
*.log
_OLD_FILES/
temp/
tmp/
.DS_Store
Thumbs.db

# 📦 Архивы и бэкапы
*.zip
*.rar
*.tar.gz
backup_*/
```

**Проверка:**
```powershell
git status --ignored
# Убедись, что в списке ignored есть .env, *.db, __pycache__, node_modules
```

---

## 3. Рабочий процесс: от фичи к мержу

### Шаг 1: Начни с актуального `master`
```powershell
git checkout master
git pull origin master
```

### Шаг 2: Создай ветку
Используй префиксы:
- `feature/` — новая функциональность
- `fix/` — исправление бага
- `docs/` — обновление документации
- `refactor/` — рефакторинг без изменения поведения
- `chore/` — рутинные задачи (обновление зависимостей, CI)

**Примеры:**
```powershell
git checkout -b feature/chaos-system-v2
git checkout -b fix/bank-withdrawal-bug
git checkout -b docs/update-architecture
```

### Шаг 3: Вноси изменения
- Пиши код.
- Проверяй локально: `python manyunya_bot.py` или `npm run dev` (для фронтенда).
- Убедись, что новые файлы не попадают в `.gitignore`.

### Шаг 4: Подготовь коммит
```powershell
git add <файлы>
# или
git add -u  # добавляет только изменённые и удалённые файлы (не новые)
```

**Проверка статуса:**
```powershell
git status
# Проверь, что:
# ✅ Только нужные файлы в "Changes to be committed"
# ❌ Нет .env, *.db, __pycache__, node_modules
```

### Шаг 5: Сделай коммит
```powershell
git commit -m "feat: add chaos energy tracking to solve_task"
```
> ⚠️ Соблюдай [формат сообщений](#4-формат-сообщений-коммитов).

### Шаг 6: Отправь ветку в репозиторий
```powershell
git push origin feature/chaos-system-v2
```

### Шаг 7: Мерж в `master`
Когда фича готова и протестирована:
```powershell
git checkout master
git pull origin master
git merge --no-ff feature/chaos-system-v2 -m "feat: merge chaos system v2"
git push origin master
```

### Шаг 8: Удали ветку
```powershell
git branch -d feature/chaos-system-v2
git push origin --delete feature/chaos-system-v2  # если была запушена
```

---

## 4. Формат сообщений коммитов

Используем **Conventional Commits**:
```
<type>: <описание>

[опционально: тело коммита]
```

### Типы коммитов
| Тип | Когда использовать | Пример |
|-----|-------------------|--------|
| `feat` | Новая фича | `feat: add transfer task generation after 2 mistakes` |
| `fix` | Исправление бага | `fix: prevent negative balance on artifact upgrade` |
| `docs` | Документация | `docs: add INDEX.md and update ARCHITECTURE.md` |
| `refactor` | Изменение структуры без смены поведения | `refactor: extract bank logic to separate service` |
| `chore` | Обслуживание, зависимости, конфиги | `chore: update python-telegram-bot to v21.0.1` |
| `test` | Тесты | `test: add unit tests for score_manager.apply_penalty` |
| `perf` | Оптимизация производительности | `perf: cache avatar file_ids to reduce API calls` |

### Правила
1. **Тема ≤ 72 символа.**
2. **Первая буква строчная.**
3. **Без точки в конце.**
4. **Императив:** `add`, `fix`, `update` (не `added`, `fixed`).
5. **Если нужно больше деталей** — добавь тело через пустую строку:
   ```
   fix: handle JSON decode error in avatar_cache

   Added try/except around json.load() to prevent crash
   when avatar_cache.json is corrupted.
   Fallback to empty dict and log warning.
   ```

---

## 5. Откаты и исправление ошибок

### 🔙 Отменить незакоммиченные изменения
```powershell
# Вернуть файл к состоянию последнего коммита
git restore <файл>

# Вернуть ВСЕ изменения
git restore .
```

### 🔙 Отменить добавление в staging (git add)
```powershell
git restore --staged <файл>
```

### 🔙 Отменить последний коммит (мягко)
Оставит изменения в рабочей директории:
```powershell
git reset --soft HEAD~1
```

### 🔙 Отменить последний коммит (жёстко)
Удалит изменения (⚠️ опасно!):
```powershell
git reset --hard HEAD~1
```

### 🔙 Откат к конкретному коммиту
```powershell
git log --oneline  # найди хеш нужного коммита
git reset --hard abc1234
```

### 🔙 Создать "обратный" коммит (безопасно для master)
Не переписывает историю, а создаёт новый коммит, отменяющий изменения:
```powershell
git revert abc1234
```

### 🔙 Если сломал `master`
```powershell
# 1. Найти последний рабочий коммит
git log --oneline

# 2. Сделать revert проблемных коммитов
git revert abc1234 def5678

# 3. Или откатиться к тегу
git revert v2.3-stable..HEAD
```

---

## 6. Теги и версии

### Создание тега
```powershell
git tag -a v4.7-stable -m "Стабильная версия: Chaos System + Multi-platform"
git push origin v4.7-stable
```

### Список тегов
```powershell
git tag -l "v*"
```

### Переход к тегу (только чтение)
```powershell
git checkout v4.7-stable
```

> ⚠️ Теги не изменяются после создания. Если нужно исправить — удали старый и создай новый.

---

## 7. Чеклисты

### ✅ Перед коммитом
- [ ] `git status` — только нужные файлы
- [ ] Нет `.env`, `*.db`, `__pycache__/`, `node_modules/`, `logs/`
- [ ] Код отформатирован (PEP 8 для Python, ESLint для JS)
- [ ] Локально проверена работа (`python manyunya_bot.py` / `npm run dev`)
- [ ] Сообщение коммита соответствует формату `<type>: description`

### ✅ Перед мержем в `master`
- [ ] Ветка протестирована на локальной машине
- [ ] Нет конфликтов с `master` (`git merge master --no-ff` локально)
- [ ] Документация обновлена (если менялись API, структура, логика)
- [ ] `.env.example` актуален (если добавлены новые переменные)
- [ ] Создан тег версии (если это релиз)

### ✅ Перед релизом (push в production)
- [ ] `master` проходит все тесты
- [ ] Бэкап БД сделан (`data/progress.db` → `backup/`)
- [ ] Текущая версия задокументирована в `README.md`
- [ ] Создан тег `vX.Y-stable`
- [ ] Чат команды уведомлён о деплое

---

## 8. Безопасность

### 🚫 Никогда не коммить:
| Файл/Папка | Почему | Что делать |
|-----------|--------|-----------|
| `.env`, `.env.local` | Содержит токены, ключи, пароли | Добавь в `.gitignore`. В репо только `.env.example` |
| `data/progress.db` | Персональные данные, прогресс пользователей | Игнорировать. Бэкапы хранить отдельно. |
| `__pycache__/`, `*.pyc` | Скомпилированный байт-код Python | Игнорировать |
| `node_modules/` | Зависимости фронтенда (100MB+) | Игнорировать. Восстанавливаются через `npm install` |
| `logs/`, `*.log` | Логи, могут содержать чувствительные данные | Игнорировать |
| `_OLD_FILES/`, `temp/` | Временные файлы разработки | Игнорировать |

### 🔍 Проверка перед пушем
```powershell
# Проверить, нет ли секретов в истории
git log -p --all -S "BOT_TOKEN"
git log -p --all -S "VK_TOKEN"
git log -p --all -S "password"

# Если нашлось — срочно меняй токены и чисти историю!
```

---

## 9. Шпаргалка по командам

| Задача | Команда (PowerShell) |
|--------|---------------------|
| Посмотреть статус | `git status` |
| Добавить все изменённые | `git add -u` |
| Добавить конкретный файл | `git add docs/INDEX.md` |
| Закоммитить | `git commit -m "type: описание"` |
| Отправить ветку | `git push origin feature/название` |
| Переключиться на ветку | `git checkout feature/название` |
| Создать ветку | `git checkout -b feature/название` |
| Обновить master | `git checkout master && git pull origin master` |
| Слить фичу в master | `git checkout master && git merge --no-ff feature/название` |
| Удалить ветку локально | `git branch -d feature/название` |
| Удалить ветку удалённо | `git push origin --delete feature/название` |
| Посмотреть историю | `git log --oneline --graph --all` |
| Посмотреть изменения в файле | `git diff HEAD -- файл.py` |
| Отменить изменения в файле | `git restore файл.py` |
| Отменить последний коммит (мягко) | `git reset --soft HEAD~1` |
| Создать тег | `git tag -a v4.7-stable -m "описание"` |
| Отправить теги | `git push origin --tags` |

---

## 💡 Советы для командной разработки (ты + «Фея»)

1. **Координируйте ветки.** Перед началом работы проверяйте `git branch -a`, чтобы не делать одну фичу дважды.
2. **Частые коммиты.** Коммитьте каждые 30–60 минут или после логически завершённого куска.
3. **Pull Request (если используете GitHub/GitLab).** Не мержьте в `master` напрямую. Создавайте PR, ревьювьте код друг друга.
4. **Конфликты.** Если Git ругается на конфликт:
   ```powershell
   git merge master
   # Открой файлы с конфликтами (помечены <<<<<<<, =======, >>>>>>>)
   # Исправь, сохрани
   git add <файлы>
   git commit -m "fix: resolve merge conflicts with master"
   ```
5. **Бэкапы.** Перед крупными рефакторингами создавай тег или копию ветки:
   ```powershell
   git branch backup/pre-chaos-refactor
   ```

---

*Документ актуален для версии 4.7+. При изменении процесса — обновляй этот файл и коммить с `docs: update git workflow`.*
```

---

## ✅ Что делать:

1. Создай файл `docs/GIT_WORKFLOW.md` → вставь код выше → сохрани.
2. Проверь, что `.gitignore` в корне соответствует разделу [Настройка репозитория](#2-настройка-репозитория).
3. Закоммить:
   ```powershell
   git add docs/GIT_WORKFLOW.md
   git commit -m "docs: add Git workflow and commit conventions guide"
   ```

---

## 🔄 Что дальше?

Теперь у тебя есть **полная база**:
- ✅ Навигация (`INDEX.md`)
- ✅ Документация по всем модулям
- ✅ Чёткий Git-процесс (`GIT_WORKFLOW.md`)

**Рекомендую:**
1. Распечатать или закрепить `GIT_WORKFLOW.md` как чек-лист для ежедневной работы.
2. Добавить в `README.md` ссылку на Git Workflow.
3. При следующей фиче строго следовать префиксам `feature/`, `fix/`, `docs/`.

Если нужно — сгенерирую `docs/DEPLOYMENT.md` (пошаговый деплой на VPS, Docker, systemd) или `docs/TESTING_GUIDE.md` (как писать тесты для `solve_task`, `upgrade_artifact`).

Жду указаний. Работаем медленно, но правильно. 🤝