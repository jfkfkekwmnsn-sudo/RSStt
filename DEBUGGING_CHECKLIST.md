# Чеклист отладки - Бесконечная загрузка фронтенда

## Быстрая диагностика (выполните по порядку)

### 1. Проверьте логи контейнеров

```bash
# Логи фронтенда
docker-compose logs frontend -f

# Логи API
docker-compose logs api -f

# Проверьте статус всех контейнеров
docker-compose ps
```

### 2. Проверьте доступность API

```bash
# Проверьте, запущен ли API
curl http://localhost:8000/health

# Проверьте CORS
curl -i http://localhost:8000/api/v1/health
```

Должны быть заголовки:
```
Access-Control-Allow-Origin: *
```

### 3. Откройте браузер на сервере и проверьте консоль

1. Откройте http://localhost:3000
2. Нажмите **F12** (DevTools)
3. Перейдите на вкладку **Console**
4. Посмотрите на ошибки

### 4. Вкладка Network в DevTools

1. **F12** → **Network**
2. Перезагрузите страницу (Ctrl+R или Cmd+R)
3. **Ищите зависшие/красные запросы:**
   - `/api/v1/auth/me` → должен вернуть текущего пользователя
   - `/api/v1/analytics/summary` → должен вернуть статистику
   - `/api/v1/articles/queue` → должен вернуть очередь статей

4. **Для каждого запроса проверьте:**
   - **Статус**: 200 (OK), 401 (Unauthorized), 403 (Forbidden), 500 (Server Error)
   - **Time**: если > 30s, запрос зависает
   - **Size**: не должен быть 0

---

## Типичные проблемы и решения

### ❌ Проблема: Запросы идут в http://localhost:8000 вместо правильного адреса

**Причина**: VITE_API_URL не установлена при сборке Docker образа

**Решение**:

1. Убедитесь, что переменная окружения передана:
```bash
# docker-compose.prod.yml должен содержать:
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
    args:
      - VITE_API_URL=http://your-server.com/api/v1  # или HTTPS
```

2. Пересоберите образ:
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache frontend
docker-compose -f docker-compose.prod.yml up -d
```

---

### ❌ Проблема: 401 Unauthorized на всех запросах

**Причина**: Токен авторизации не сохранен или истёк

**Решение**:

1. Очистите localStorage браузера:
   - F12 → Application → Storage → Local Storage → Clear All
   - Или откройте в private/incognito режиме

2. Попробуйте авторизоваться заново
   - Перейдите на /login
   - Используйте учетные данные из базы данных

3. Проверьте, что `/auth/me` работает с токеном:
```bash
# Получите токен через логин
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  | jq -r '.access_token')

# Проверьте /me с токеном
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/auth/me
```

---

### ❌ Проблема: 403 Forbidden на запросе /analytics/summary

**Причина**: Пользователь не имеет роли "analyst"

**Решение**:

Подключитесь к БД и обновите роль пользователя:

```bash
# Подключитесь к PostgreSQL контейнеру
docker-compose exec db psql -U postgres -d news_aggregator

# Выполните SQL:
UPDATE "user" SET role = 'analyst' WHERE username = 'your_username';
-- или
UPDATE "user" SET is_superuser = true WHERE username = 'your_username';

# Выход: \q
```

---

### ❌ Проблема: 500 Internal Server Error

**Причина**: Ошибка на backend

**Решение**:

1. Проверьте логи API:
```bash
docker-compose logs api -f --tail=100
```

2. Проверьте подключение к БД:
```bash
docker-compose exec api python -c "
from app.database import engine
import asyncio
async def test():
    async with engine.begin() as conn:
        result = await conn.execute('SELECT 1')
        print('DB OK')
asyncio.run(test())
"
```

3. Проверьте миграции БД:
```bash
docker-compose exec api alembic current
docker-compose exec api alembic heads
```

---

### ❌ Проблема: CORS ошибка

**Типичное сообщение**:
```
Access to XMLHttpRequest at 'http://localhost:8000/api/v1/...' 
from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Причина**: backend не разрешает запросы с фронтенда

**Проверьте backend/app/main.py**:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Решение для разработки:**
- Убедитесь, что `DEBUG=true` в .env
- Или явно добавьте адрес фронтенда в `allow_origins`

**Решение для продакшена:**
- Добавьте ваш домен: `allow_origins=["https://yourdomain.com", "https://www.yourdomain.com"]`
- Пересоберите и перезагрузите контейнер

---

## Продвинутая отладка

### Включите verbose логирование на фронтенде

**Файл**: `frontend/src/api/client.ts`

Добавьте в `setupInterceptors()`:

```typescript
// Request interceptor
this.client.interceptors.request.use(
  (config) => {
    console.log('🔵 API Request:', config.method?.toUpperCase(), config.url);
    // ... rest of code
    return config;
  }
);

// Response interceptor
this.client.interceptors.response.use(
  (response) => {
    console.log('✅ API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('❌ API Error:', error.response?.status, error.config?.url, error.message);
    // ... rest of code
  }
);
```

### Включите verbose логирование на backend

**Файл**: `backend/app/config.py`

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Или при запуске:
```bash
docker-compose exec api pip install python-json-logger
```

---

## Контрольный список развёртывания

- [ ] Переменные окружения установлены в `.env`
- [ ] `VITE_API_URL` правильно указана в `docker-compose.prod.yml`
- [ ] Контейнеры запущены: `docker-compose ps` (all "Up")
- [ ] API доступен: `curl http://localhost:8000/health` возвращает 200
- [ ] Фронтенд доступен: `curl http://localhost:3000` возвращает HTML
- [ ] Можно авторизоваться: `/login` работает
- [ ] Dashboard загружается: `/` не показывает ошибки
- [ ] CORS заголовки присутствуют: `curl -i http://localhost:8000/api/v1/health`

---

## Команды для быстрого перезапуска

```bash
# Полный перезапуск со сборкой
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# Перезапуск только фронтенда
docker-compose -f docker-compose.prod.yml up -d --build frontend

# Очистка всего и свежий старт
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d

# Просмотр логов в реальном времени
docker-compose -f docker-compose.prod.yml logs -f
```

---

## Контакты для помощи

Если проблема не решена:

1. Соберите информацию:
   - Вывод `docker-compose ps`
   - Вывод `docker-compose logs api -n 50`
   - Вывод `docker-compose logs frontend -n 50`
   - Скриншот консоли браузера (F12 → Console)
   - Скриншот вкладки Network (F12 → Network)

2. Проверьте документацию: [README.md](README.md) или [QUICKSTART.md](QUICKSTART.md)
