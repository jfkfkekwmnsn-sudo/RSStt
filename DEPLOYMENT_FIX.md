# Исправление проблемы бесконечной загрузки фронтенда

## Основные причины

### 1. 🔴 Проблема конфигурации API URL
**Симптом**: Фронтенд загружается, но затем зависает
**Причина**: VITE_API_URL не установлена при сборке Docker образа

### 2. 🔴 Проблема доступа к API (/analytics)
**Симптом**: Dashboard пытается загрузить аналитику и зависает
**Причина**: Запрос требует роль "analyst", но пользователь может не иметь её

### 3. 🔴 Отсутствие таймаутов в запросах
**Симптом**: Зависшие запросы никогда не прерываются
**Причина**: Axios не имеет настройки timeout

---

## Исправления

### Вариант 1: Исправить docker-compose.yml (РЕКОМЕНДУЕТСЯ для продакшена)

**Файл**: `docker-compose.prod.yml`

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
    args:
      VITE_API_URL: "http://api:8000/api/v1"  # Или ваш prod URL
  ports:
    - "3000:80"
  environment:
    - VITE_API_URL=http://api:8000/api/v1
  depends_on:
    - api
```

### Вариант 2: Обновить Dockerfile фронтенда

**Файл**: `frontend/Dockerfile`

```dockerfile
# Build stage
FROM node:20-alpine as build

WORKDIR /app

# Принимаем API_URL как аргумент сборки
ARG VITE_API_URL=/api/v1

COPY package*.json ./
RUN npm ci

COPY . .

# Устанавливаем переменную окружения
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Вариант 3: Добавить таймауты в API клиент

**Файл**: `frontend/src/api/client.ts`

Измените конструктор:

```typescript
constructor() {
  this.client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,  // 10 секунд таймаут для всех запросов
    headers: {
      'Content-Type': 'application/json',
    },
  });

  this.setupInterceptors();
}
```

### Вариант 4: Исправить проблему с require_analyst

**Файл**: `backend/app/api/deps.py`

Проверьте зависимость `require_analyst`:

```python
async def require_analyst(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require user to have analyst role"""
    if not current_user.is_superuser and current_user.role not in ['analyst', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst role required"
        )
    return current_user
```

Также оберните analyticsApi в try-catch на фронтенде:

**Файл**: `frontend/src/pages/Dashboard.tsx`

```typescript
// Используйте enabled: !!isAuthenticated
const { data: analytics, isLoading: analyticsLoading } = useAnalyticsSummary();

// Или добавьте обработку ошибок:
export function useAnalyticsSummary(dateFrom?: string, dateTo?: string) {
  return useQuery({
    queryKey: ['analytics', 'summary', dateFrom, dateTo],
    queryFn: () => analyticsApi.summary(dateFrom, dateTo),
    retry: 1,
    staleTime: 60000,
  });
}
```

---

## Шаги развёртывания на продакшене

1. **Убедитесь, что .env правильно заполнен:**
   ```bash
   cp .env.example .env
   # Отредактируйте .env с правильными значениями
   ```

2. **Используйте docker-compose.prod.yml:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Проверьте логи контейнеров:**
   ```bash
   docker-compose logs frontend
   docker-compose logs api
   ```

4. **Проверьте, что API доступен:**
   ```bash
   curl http://localhost:3000/api/v1/health
   ```

5. **Проверьте консоль браузера** (F12 → Console):
   - Ищите ошибки CORS
   - Ищите ошибки сетевых запросов
   - Проверьте вкладку Network → XHR/fetch

---

## Отладка в реальном времени

### Если фронтенд все ещё зависает:

1. **Откройте консоль браузера (F12)**
   - Вкладка **Network** → посмотрите какие запросы зависли
   - Вкладка **Console** → ищите ошибки JavaScript

2. **Проверьте логи API:**
   ```bash
   docker-compose logs api -f
   ```

3. **Проверьте доступность API:**
   ```bash
   curl -v http://localhost:8000/api/v1/health
   ```

4. **Проверьте CORS в ответе API:**
   Ответ должен содержать:
   ```
   Access-Control-Allow-Origin: *
   Access-Control-Allow-Methods: *
   Access-Control-Allow-Headers: *
   ```

---

## Рекомендуемое решение для продакшена

1. Отредактируйте `docker-compose.prod.yml` (Вариант 1)
2. Обновите `frontend/src/api/client.ts` (Вариант 3)
3. Переразверните:
   ```bash
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d --build
   ```
