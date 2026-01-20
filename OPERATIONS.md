# 🚀 Deployment & Operations

## Быстрое развертывание

### Development (5 минут)
```bash
cp .env.example .env
docker-compose up -d
docker-compose exec api alembic upgrade head
# API: localhost:8000, Frontend: localhost:3000
```

### Production (30 минут)
```bash
# 1. Подготовка
cp .env.example .env.prod
nano .env.prod  # Отредактируйте все переменные

# 2. Запуск
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# 3. Проверка
curl https://yourdomain.com/health
```

## Переменные окружения

**Критические (обязательны):**
```
SECRET_KEY=your-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-key-min-32-chars
DATABASE_URL=postgresql+asyncpg://postgres:pass@db:5432/news_db
REDIS_URL=redis://redis:6379/0
```

**Интеграции:**
```
TELEGRAM_BOT_TOKEN=123456:ABC...
OPENAI_API_KEY=sk-...  # опционально
```

**Безопасность (production):**
```
DEBUG=False
CORS_ORIGINS=https://yourdomain.com
```

**Опционально:**
```
SENTRY_DSN=...
S3_ENDPOINT=http://minio:9000
```

## Pre-launch Checklist

- [ ] `.env.prod` создан и заполнен
- [ ] `DEBUG=False`
- [ ] Новые SECRET_KEY и JWT_SECRET_KEY (32+ символов)
- [ ] Database и Redis доступны
- [ ] Telegram bot token действителен
- [ ] SSL сертификаты установлены
- [ ] CORS domains актуальны
- [ ] Backups настроены
- [ ] Healthchecks работают

## Команды управления

```bash
# Просмотр статуса
docker-compose ps
docker-compose -f docker-compose.prod.yml ps

# Логи
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f db

# Перезагрузка
docker-compose restart api
docker-compose restart worker

# Остановка
docker-compose down
docker-compose -f docker-compose.prod.yml down

# Миграции
docker-compose exec api alembic upgrade head
docker-compose exec api alembic downgrade -1

# Backup БД
docker-compose exec db pg_dump -U postgres news_db > backup.sql

# Restore БД
docker-compose exec -T db psql -U postgres news_db < backup.sql
```

## Мониторинг

```bash
# Health check API
curl http://localhost:8000/health

# Celery статус
docker-compose exec worker celery -A app.workers.celery_app inspect active

# Redis статус
redis-cli ping
redis-cli dbsize

# Database статус
docker-compose exec db psql -U postgres -c "SELECT version();"
```

## SOS: Если всё упало

### API недоступен
```bash
# 1. Проверьте контейнер
docker-compose logs api | tail -50

# 2. Проверьте БД
docker-compose exec db psql -U postgres -d news_db -c "\dt"

# 3. Перезагрузите
docker-compose restart api
```

### БД недоступна
```bash
# 1. Проверьте статус
docker-compose logs db

# 2. Проверьте volume
docker volume ls | grep postgres

# 3. Восстановите из backup
docker-compose down
# Восстановите данные
docker-compose up -d
```

### Celery worker не работает
```bash
# 1. Проверьте Redis
redis-cli ping

# 2. Проверьте логи
docker-compose logs worker

# 3. Перезагрузите
docker-compose restart worker
```

## Обновление приложения

```bash
# 1. Остановка
docker-compose -f docker-compose.prod.yml down

# 2. Обновление кода
git pull origin main

# 3. Rebuild образов
docker-compose -f docker-compose.prod.yml build

# 4. Запуск
docker-compose -f docker-compose.prod.yml up -d

# 5. Миграции
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

## Масштабирование

```bash
# Увеличение workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=3

# Увеличение API
docker-compose -f docker-compose.prod.yml up -d --scale api=2
```

---

**Вопросы?** Смотрите README.md или логи контейнеров.
