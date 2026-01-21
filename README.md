# 📰 AI Content Aggregator & Publisher

Полнофункциональная система для сбора, обработки, модерации и публикации контента с интеграцией AI и Telegram.

## 🎯 Возможности

- 📥 **Сбор** - RSS, веб-скрейпинг, API источники
- 🤖 **AI обработка** - переписывание (OpenAI), категоризация, анализ
- ✅ **Модерация** - ручная проверка в Telegram, правила фильтрации
- 📤 **Публикация** - Telegram каналы, вебхуки, API
- 📊 **Аналитика** - статистика по источникам, качеству, пользователям
- 🔐 **Безопасность** - JWT, RBAC, защита от SQL-injection

## 🏗 Стек технологий

| Компонент | Технология |
|-----------|-----------|
| Backend | FastAPI 0.109 + SQLAlchemy 2.0 |
| Frontend | React 18 + TypeScript + Tailwind |
| Database | PostgreSQL 16 + Alembic |
| Cache/Queue | Redis 7 + Celery |
| Bot | Aiogram 3.4 (Telegram) |
| AI | OpenAI API |

## 🚀 Быстрый старт

**Подробная инструкция:** [QUICKSTART.md](QUICKSTART.md)

```bash
# Клонирование
git clone <repo> && cd project

# Конфигурация
cp .env.example .env
# ⚠️ Отредактируйте .env (SECRET_KEY, TELEGRAM_BOT_TOKEN и т.д.)

# Запуск
docker-compose up -d --build
docker-compose exec api alembic upgrade head

# Доступ
# API Docs:  http://localhost:8000/docs
# Frontend:  http://localhost:3000
# Health:    http://localhost:8000/health
```

## 🌐 Доступ к приложениям

| Сервис | URL | Описание |
|--------|-----|---------|
| **API Swagger** | http://localhost:8000/docs | Интерактивная документация |
| **Frontend** | http://localhost:3000 | Веб-интерфейс |
| **Health Check** | http://localhost:8000/health | Статус системы |
| **ReDoc** | http://localhost:8000/redoc | Альтернативная документация |

## 📚 Основные документы

- **[QUICKSTART.md](QUICKSTART.md)** - Полное руководство по развертыванию
- **.env.example** - Все переменные окружения с описанием

## 📊 API - Основные эндпоинты

### Аутентификация
```
POST   /api/v1/auth/login              # Вход
POST   /api/v1/auth/refresh            # Обновление токена
GET    /api/v1/auth/me                 # Текущий пользователь
```

### Статьи
```
GET    /api/v1/articles                # Список с фильтрацией
GET    /api/v1/articles/{id}           # Детали
PATCH  /api/v1/articles/{id}           # Обновить
POST   /api/v1/articles/{id}/approve   # Одобрить
POST   /api/v1/articles/{id}/reject    # Отклонить
```

### Источники
```
GET    /api/v1/sources                 # Список источников
POST   /api/v1/sources                 # Создать
PATCH  /api/v1/sources/{id}            # Обновить
DELETE /api/v1/sources/{id}            # Удалить
GET    /api/v1/sources/{id}/runs       # История запусков
```

### Аналитика
```
GET    /api/v1/analytics/summary       # Общая статистика
GET    /api/v1/analytics/categories    # По категориям
GET    /api/v1/analytics/sources       # По источникам
```

**Полная документация:** http://localhost:8000/docs

## 🤖 Автоматические задачи (Celery Beat)

| Задача | Периодичность | Описание |
|--------|---------------|---------|
| `fetch_all_sources` | каждые 5 мин | Сбор новых статей |
| `create_moderation_batches` | каждые 10 мин | Группировка для модерации |
| `send_batches_to_telegram` | каждые 15 мин | Отправка в Telegram |
| `execute_scheduled_jobs` | каждую минуту | Публикация запланированного |
| `update_source_reputations` | каждый день 4:00 | Обновление рейтинга |
| `housekeeping` | каждый день 3:00 | Очистка старых данных |

## 🔧 Основные команды

```bash
# Просмотр логов
docker-compose logs -f api              # API сервер
docker-compose logs -f worker           # Celery worker
docker-compose logs -f frontend         # Frontend

# Управление сервисами
docker-compose ps                       # Статус контейнеров
docker-compose restart api              # Перезагрузка API
docker-compose down                     # Остановка всех

# Работа с БД
docker-compose exec api alembic upgrade head      # Применить миграции
docker-compose exec api alembic downgrade -1      # Откатить миграцию
docker-compose exec db psql -U postgres -d news_aggregator  # Подключиться

# Масштабирование
docker-compose up -d --scale worker=3   # 3 worker процесса
```

## ⚙️ Важные переменные окружения

```env
# Безопасность
SECRET_KEY=<32+ символа>                # ⚠️ Обязательна!
JWT_SECRET_KEY=<32+ символа>            # ⚠️ Обязательна!
DEBUG=false                              # Для production

# Базы данных
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/news_aggregator
REDIS_URL=redis://redis:6379/0

# Telegram
TELEGRAM_BOT_TOKEN=<ваш токен>          # Для bot интеграции
TELEGRAM_MODERATION_CHAT_ID=<ID>        # Чат для модерации

# AI (опционально)
OPENAI_API_KEY=sk-...                   # Для переписывания
OPENAI_MODEL=gpt-4o-mini
AI_ENABLED=true

# Сбор контента
DEFAULT_FETCH_INTERVAL_MINUTES=15       # Интервал проверки
MAX_ARTICLES_PER_FETCH=50              # Max статей за раз
ARTICLE_FRESHNESS_DAYS=7               # Максимальный возраст
```

Все переменные: см. [.env.example](.env.example)

## 🐛 Быстрое решение проблем

| Проблема | Решение |
|----------|---------|
| API не запускается | `docker-compose logs api` и проверьте DB |
| БД не инициализирована | `docker-compose exec api alembic upgrade head` |
| Worker не обрабатывает задачи | `docker-compose restart worker` |
| Redis ошибка | `docker-compose restart redis` |
| Frontend не загружается | `docker-compose logs frontend` |

Подробный troubleshooting: [QUICKSTART.md](QUICKSTART.md#-troubleshooting)

## 📁 Структура проекта

```
backend/
├── app/
│   ├── api/              # 12 API роутеров
│   ├── models/           # 11 SQLAlchemy моделей
│   ├── services/         # 13 сервисов бизнес-логики
│   ├── workers/          # Celery задачи
│   ├── telegram/         # Telegram bot
│   └── utils/            # Утилиты (Redis, logging)
├── alembic/              # Миграции БД
└── Dockerfile

frontend/
├── src/
│   ├── components/       # React компоненты (20+)
│   ├── pages/           # Страницы приложения (11)
│   ├── hooks/           # Custom hooks (5)
│   ├── types/           # TypeScript типы (30+)
│   ├── api/             # API клиент
│   └── store/           # Zustand хранилище
└── Dockerfile

docker-compose.yml       # 5 сервисов (api, worker, scheduler, db, redis)
.env.example            # Переменные окружения
```

## 🔐 Безопасность

- ✅ JWT-токены для аутентификации
- ✅ Хеширование паролей (bcrypt)
- ✅ RBAC (роли: Admin, Editor, Analyst, Moderator)
- ✅ SQL-injection защита (SQLAlchemy ORM)
- ✅ CORS конфигурация
- ✅ Валидация входных данных (Pydantic)

## 📞 Поддержка и документация

- **Полное руководство:** [QUICKSTART.md](QUICKSTART.md)
- **Переменные окружения:** [.env.example](.env.example)
- **API документация:** http://localhost:8000/docs

## 📋 История исправлений

v1.0.3 (текущая):
- ✅ Исправлены все `datetime.utcnow()` → `datetime.now()`
- ✅ Удалена дублирующаяся папка `backend/app/app/`
- ✅ Нормализирована структура проекта
- ✅ Оптимизирована документация

---

**Версия:** 1.0.3  
**Статус:** ✅ Production Ready  
**Последнее обновление:** 2026-01-21  
**Лицензия:** MIT
