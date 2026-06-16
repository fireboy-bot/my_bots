[#025]
Привет. Файл `web/api_server.py` получил. Это Flask API сервер — «мост» между React-фронтендом и ядром «Числяндии».

Ниже — готовая документация. Просто сохрани в `docs/WEB_API_SERVER.md`.

---

## 📄 Файл: `docs/WEB_API_SERVER.md`

```markdown
# 🌐 Web API Server — Flask адаптер для фронтенда

> **Файл:** `web/api_server.py`  
> **Версия:** 1.0 (WebAdapter — Simple Bridge) 🌉🔗✅  
> **Ответственность:** Простая трансляция HTTP-запросов от React-фронтенда к методам `ChislyandiaEngine`

---

## 📋 Обзор

`api_server.py` — минималистичный Flask-сервер, который предоставляет REST API для веб-версии «Числяндии». 

**Ключевой принцип:** 
> «ВСЯ логика — в ядре (`core/game_engine.py`). Здесь только трансляция.»

| Функция | Описание |
|---------|----------|
| 🔄 Прокси-паттерн | Эндпоинты просто вызывают методы `engine.*` без добавления бизнес-логики |
| 🔓 CORS | Разрешает запросы с любого источника (для разработки) |
| 📦 Нормализация задач | Загрузка и адаптация задач из `tasks.json` для фронтенда |
| 🔐 Безопасность | Валидация входных данных, логирование ошибок |
| 🪟 Windows-совместимость | Принудительная кодировка UTF-8 для stdout/stderr |

```
┌─────────────────┐
│   React Frontend│
│   (Vite + JSX)  │
└────────┬────────┘
         │ HTTP/JSON
         ▼
┌─────────────────┐
│  Flask API      │
│  (api_server.py)│
└────────┬────────┘
         │ Прямой вызов
         ▼
┌─────────────────┐
│  Chislyandia-   │
│  Engine (ядро)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PlayerStorage  │
│  (SQLite БД)    │
└─────────────────┘
```

---

## ⚙️ Инициализация и запуск

### Глобальные зависимости

```python
# Добавляем корень проекта в sys.path для импорта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Импорт ядра
from database.storage import PlayerStorage
from core.score_manager import ScoreManager
from core.game_engine import ChislyandiaEngine
```

### Создание экземпляров ядра (ЕДИНСТВЕННОЕ место)

```python
storage = PlayerStorage()
score_manager = ScoreManager(storage)
engine = ChislyandiaEngine(storage, score_manager)
```

> ⚠️ **Важно:** Эти объекты создаются один раз при старте сервера и используются всеми запросами. Это обеспечивает:
> - Единое соединение с БД
> - Согласованность кэша
> - Отсутствие рассинхрона между запросами

### Запуск сервера

```bash
# Из корня проекта:
python web/api_server.py

# Сервер запустится на:
# http://127.0.0.1:5001
```

**Параметры запуска:**
```python
app.run(
    host='127.0.0.1',  # Только локальный доступ (безопасно)
    port=5001,         # Порт (не конфликтует с Telegram polling)
    debug=False,       # Выключено для продакшена
    threaded=True      # Обработка параллельных запросов
)
```

---

## 🔧 Вспомогательные функции

### `load_tasks_from_file(world=None) -> List[Dict]` 🎯
Загружает и нормализует задачи из `data/tasks.json` для отправки во фронтенд.

**Поддерживаемый формат `tasks.json`:**
```json
{
  "addition": {
    "tasks": [
      {
        "id": "add_001",
        "question": "5 + 3 = ?",
        "correct_answer": "8",
        "score": 10
      }
    ]
  }
}
```

**Нормализация (что добавляется автоматически):**
| Поле | Источник | Описание |
|------|----------|----------|
| `options` | Генерируется | Если нет в исходнике → создаются 4 варианта вокруг правильного ответа |
| `world` / `island` | Ключ словаря | Определяется по названию мира в JSON |
| `operation_type` | Анализ вопроса | Определяется по символам: `×` → `1digit_mult`, `÷` → `2digit_div`, и т.д. |

**Fallback:** Если файл не найден или пустой → возвращаются моковые задачи.

---

## 📡 Эндпоинты API

### 🔍 Health Check

#### `GET /api/health`
Проверка работоспособности сервера.

**Ответ:**
```json
{
  "status": "ok",
  "timestamp": "2026-04-05T14:30:00Z",
  "service": "chislyandia-web-adapter"
}
```

---

### 👤 Профиль игрока

#### `GET /api/player/<user_id>/profile`
Получает профиль игрока.

**Делегирует:** `engine.get_player_profile(user_id)`

**Ответ:** См. документацию `ChislyandiaEngine.get_player_profile()`

---

### 🎮 Игровые задачи

#### `GET /api/game/task?user_id=123&world=addition`
Получает случайную задачу для указанного мира.

**Параметры запроса:**
| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `user_id` | `str` | ✅ | ID игрока |
| `world` | `str` | ❌ | Фильтр по миру (`addition`, `multiplication`, ...) |

**Ответ (пример):**
```json
{
  "id": "add_042",
  "question": "15 + 27 = ?",
  "correct_answer": "42",
  "options": ["40", "41", "42", "43"],
  "score": 10,
  "world": "addition",
  "island": "addition",
  "operation_type": "2digit_add"
}
```

---

#### `POST /api/game/check_answer` 🎯
Проверяет ответ игрока — **вся логика в `engine.solve_task()`**.

**Тело запроса (JSON):**
```json
{
  "user_id": "123456",
  "answer": "42",
  "task_id": "add_042",
  "expected_answer": "42",
  "island_id": "addition",
  "operation_type": "2digit_add"
}
```

**Обязательные поля:** `user_id`, `answer`, `task_id`, `expected_answer`

**Ответ:** См. документацию `ChislyandiaEngine.solve_task()` — возвращается полный результат с:
- `correct`: был ли ответ верным
- `reward`: начислено/списано очков
- `chaos_state`: состояние системы хаоса
- `transfer_task`: задача-перенос (если сгенерирована)
- и др.

---

### 🏦 Банк

#### `GET /api/bank/<user_id>`
Информация о банковском вкладе.

**Делегирует:** `engine.get_bank_info(user_id)`

---

#### `POST /api/bank/<user_id>/deposit`
Положить золото в банк.

**Тело запроса:**
```json
{"amount": 500}
```

**Ответ:**
```json
{"success": true, "message": "✅ Вклад успешен!..."}
```

---

#### `POST /api/bank/<user_id>/withdraw`
Забрать вклад с процентами.

**Ответ:**
```json
{
  "success": true,
  "message": "✅ Забрано 1250 очков!...",
  "total": 1250
}
```

---

### 🏰 Замок

#### `GET /api/castle/<user_id>`
Информация о замке.

**Делегирует:** `engine.get_castle_info(user_id)`

---

#### `POST /api/castle/<user_id>/upkeep`
Оплатить содержание замка.

**Тело запроса:**
```json
{"days": 7}  // Опционально, по умолчанию 1
```

---

#### `POST /api/castle/<user_id>/upgrade_decoration`
Улучшить декорацию замка.

**Тело запроса:**
```json
{"decoration_id": "fountain"}
```

**Делегирует:** `engine.castle.upgrade_decoration(user_id, dec_id)`

---

### 🔮 Артефакты

#### `GET /api/artifacts/<user_id>`
Список артефактов игрока.

**Делегирует:** `engine.get_artifact_info(user_id)`

---

#### `POST /api/artifacts/<user_id>/upgrade`
Улучшить артефакт.

**Тело запроса:**
```json
{"artifact_id": "artifact_luck"}
```

**Делегирует:** `engine.upgrade_artifact(user_id, art_id)`

---

## ⚠️ Важные замечания

### 1. Прокси-паттерн: никаких бизнес-правил здесь
Все эндпоинты следуют шаблону:
```python
@app.route('/api/...')
def endpoint(...):
    try:
        # 1. Получить данные из запроса
        # 2. Валидировать (минимум)
        # 3. Вызвать engine.метод(...)
        # 4. Вернуть jsonify(result)
    except Exception as e:
        logger.error(...)
        return jsonify({"error": str(e)}), 500
```

**Не добавляйте бизнес-логику в эндпоинты!** Если нужно новое поведение — реализуйте его в `core/` и вызовите из API.

### 2. CORS и безопасность
```python
CORS(app, resources={r"/api/*": {"origins": ["*"]}})
```
- `*` разрешает запросы с любого источника — **удобно для разработки, опасно для продакшена**.
- **Для продакшена:** замените `["*"]` на `["https://chislyandia.ru"]` или другой домен.

### 3. Обработка ошибок
Все эндпоинты обернуты в `try/except` с логированием:
```python
logger.error(f"[ERROR] endpoint_name: {e}", exc_info=True)
return jsonify({"error": str(e)}), 500
```
- `exc_info=True` добавляет стек-трейс в логи (полезно для отладки)
- Клиент получает только сообщение об ошибке (без внутренних деталей)

### 4. Кодировка на Windows
```python
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    # ...
```
Предотвращает краш при выводе кириллицы в консоль на Windows.

### 5. Логирование
Логи пишутся в два места:
```python
handlers=[
    logging.StreamHandler(sys.stdout),  # Консоль
    logging.FileHandler('logs/api_server.log', encoding='utf-8')  # Файл
]
```

**Уровни логов:**
- `INFO` — старт сервера, успешные запросы
- `WARNING` — предупреждения (файл не найден, моковые данные)
- `ERROR` — исключения, ошибки валидации

---

## 🔗 Интеграция с фронтендом

### Пример запроса из React (axios)

```javascript
// Получить задачу
const response = await axios.get('/api/game/task', {
  params: { user_id: '123456', world: 'addition' }
});
const task = response.data;

// Отправить ответ
const result = await axios.post('/api/game/check_answer', {
  user_id: '123456',
  answer: '42',
  task_id: task.id,
  expected_answer: task.correct_answer,
  island_id: task.island,
  operation_type: task.operation_type
});

if (result.data.correct) {
  showSuccess(`+${result.data.reward} очков!`);
} else {
  showError(result.data.message);
}
```

### Базовый URL для разработки
```
http://127.0.0.1:5001/api/...
```

### Базовый URL для продакшена (пример)
```
https://api.chislyandia.ru/api/...
```

---

## 🧪 Тестирование эндпоинтов

### Через curl

```bash
# Health check
curl http://127.0.0.1:5001/api/health

# Получить задачу
curl "http://127.0.0.1:5001/api/game/task?user_id=123&world=addition"

# Проверить ответ
curl -X POST http://127.0.0.1:5001/api/game/check_answer \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123",
    "answer": "8",
    "task_id": "add_001",
    "expected_answer": "8"
  }'

# Банк: депозит
curl -X POST http://127.0.0.1:5001/api/bank/123/deposit \
  -H "Content-Type: application/json" \
  -d '{"amount": 500}'
```

### Через Postman / Insomnia
1. Создать коллекцию "Chislyandia API"
2. Добавить базовый URL: `http://127.0.0.1:5001/api`
3. Протестировать каждый эндпоинт с примерами из документации

---

## 🛠 Расширение: добавление нового эндпоинта

Чтобы добавить новый метод (например, `/api/alchemy/craft`):

1. **Реализуйте логику в ядре** (`core/alchemy_manager.py` или в `ChislyandiaEngine`)
2. **Добавьте эндпоинт в `api_server.py`:**
```python
@app.route('/api/alchemy/craft', methods=['POST'])
def craft_item(user_id):
    try:
        data = request.get_json(silent=True) or {}
        item_id = data.get('item_id')
        if not item_id:
            return jsonify({"error": "item_id required"}), 400
        
        # Вызов ядра
        success, message = engine.craft_item(user_id, item_id)
        return jsonify({"success": success, "message": message})
    except Exception as e:
        logger.error(f"[ERROR] craft_item: {e}")
        return jsonify({"error": str(e)}), 500
```
3. **Протестируйте** через curl/Postman
4. **Обновите фронтенд** для вызова нового эндпоинта

---

## 🚀 Деплой

### Локальная разработка
```bash
# 1. Активировать venv
venv\Scripts\activate

# 2. Установить зависимости
pip install flask flask-cors

# 3. Запустить сервер
python web/api_server.py
```

### Продакшен (systemd-сервис, пример)

```ini
# /etc/systemd/system/chislyandia-api.service
[Unit]
Description=Chislyandia Web API
After=network.target

[Service]
User=chislyandia
WorkingDirectory=/opt/chislyandia
Environment="PATH=/opt/chislyandia/venv/bin"
ExecStart=/opt/chislyandia/venv/bin/python web/api_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Активировать:
sudo systemctl enable chislyandia-api
sudo systemctl start chislyandia-api
```

### Docker (опционально)

```dockerfile
# Dockerfile.api
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5001
CMD ["python", "web/api_server.py"]
```

---

*Документация актуальна для версии 1.0. Последнее обновление: `$(date)`*
```

---

## ✅ Что делать:

1. Создай файл `docs/WEB_API_SERVER.md` → вставь код выше → сохрани.

2. Закоммить:
   ```powershell
   git add docs/WEB_API_SERVER.md
   git commit -m "docs: add Web API Server documentation"
   ```

---

## 🔄 Что дальше?

Следующие кандидаты на документацию (по приоритету):

1. `database/schema.py` — схема базы данных: таблицы, миграции, индексы
2. `platforms/telegram_adapter.py` — адаптер Telegram: отправка сообщений, обработка обновлений
3. `frontend/src/api/chislyandia.js` — клиентская библиотека для React: запросы к API

Пришли код любого из этих файлов — сделаю документацию в том же формате.

Работаем медленно, но правильно. Жду твой выбор.