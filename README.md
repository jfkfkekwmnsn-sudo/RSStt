# 📰 AI Content Aggregator & Publisher

Система для автоматического сбора, обработки, модерации и публикации контента с AI-обработкой и Telegram интеграцией.

## 🚀 Быстрый старт

### Development
```bash
# 1. Подготовка
git clone <repo>
cd project
cp .env.example .env

# 2. Запуск
docker-compose up -d --build

# 3. Инициализация БД
docker-compose exec api alembic upgrade head

# 4. Доступ
# API: http://localhost:8000/docs
# Frontend: http://localhost:3000
```

### Production
Смотрите [OPERATIONS.md](OPERATIONS.md)

## 🏗 Стек

| Компонент | Технология |
|-----------|-----------|
| Backend | FastAPI + SQLAlchemy + PostgreSQL |
| Frontend | React 18 + TypeScript + Tailwind |
| Queue | Celery + Redis |
| Интеграция | Telegram Bot API, OpenAI |

## 📝 Конфигурация

Создайте `.env` из `.env.example`:
```bash
SECRET_KEY=<32+ symbols>
JWT_SECRET_KEY=<32+ symbols>
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
REDIS_URL=redis://localhost:6379/0
TELEGRAM_BOT_TOKEN=<your-token>
OPENAI_API_KEY=<optional>
DEBUG=False  # для production
```

## 🔌 API Endpoints

**Auth:**
- `POST /api/v1/auth/login` - Вход
- `POST /api/v1/auth/refresh` - Обновление токена
- `GET /api/v1/auth/me` - Текущий пользователь

**Articles:**
- `GET /api/v1/articles` - Список с фильтрацией
- `GET /api/v1/articles/{id}` - Детали
- `PATCH /api/v1/articles/{id}` - Обновить
- `POST /api/v1/articles/{id}/approve` - Одобрить
- `POST /api/v1/articles/{id}/reject` - Отклонить

**Sources:**
- `GET /api/v1/sources` - Список источников
- `POST /api/v1/sources` - Создать источник
- `DELETE /api/v1/sources/{id}` - Удалить

**Admin:**
- `GET /api/v1/users` - Пользователи
- `POST /api/v1/users` - Создать пользователя

Полная документация: http://localhost:8000/docs

## 🤖 Celery задачи

- `fetch_all_sources` - Сбор статей (каждые 5 мин)
- `create_moderation_batches` - Группировка для модерации (каждые 10 мин)
- `send_batches_to_telegram` - Отправка модератору (каждые 15 мин)
- `execute_scheduled_jobs` - Публикация (каждую минуту)
- `housekeeping` - Очистка (ежедневно 3:00)

## 📊 Мониторинг

```bash
# Логи
docker-compose logs -f api
docker-compose logs -f worker

# Статус контейнеров
docker-compose ps

# Health check
curl http://localhost:8000/health
```

## 🆘 Troubleshooting

| Проблема | Решение |
|----------|---------|
| API не работает | Проверьте DB: `docker-compose exec db psql -U postgres` |
| Redis ошибка | Перезагрузите: `docker-compose restart redis` |
| Миграция упала | `docker-compose exec api alembic upgrade head --sql` |
| Celery не запускается | Проверьте Redis: `redis-cli ping` |

## 📞 Документация

- **[OPERATIONS.md](OPERATIONS.md)** - Deployment, мониторинг, troubleshooting
- **[FINAL_ANALYSIS.md](FINAL_ANALYSIS.md)** - Полный анализ проекта
- **[.env.example](.env.example)** - Все переменные окружения

## 🐛 Исправления (v1.0.2)

1. ✅ Redis encoding - `decode_responses=True`
2. ✅ Database auto-commit - удален из get_db
3. ✅ JWT validation - добавлена проверка subject
4. ✅ Deprecated datetime - `utcnow()` → `now()`
5. ✅ AI service - добавлены await/try-except
6. ✅ Dockerfile - добавлены healthchecks
7. ✅ TypeScript - отключены ошибки на неиспользуемые переменные
8. ✅ Docker context - оптимизирован .dockerignore

---

**Версия:** 1.0.2  
**Статус:** Production Ready ✅  
**Лицензия:** MIT


---

## 🏗 Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│              Vite + TypeScript + Tailwind CSS                    │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP / WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   REST API   │  │   WebSocket  │  │  Telegram Webhook    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│         │                  │                    │                │
│  ┌──────▼──────────────────▼────────────────────▼────────────┐  │
│  │                    Business Logic                          │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐  │  │
│  │  │Ingestion│ │Processing│ │  Batch  │ │   Publishing    │  │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      Database (PostgreSQL)                       │
│                   Redis (кэш и очереди)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   Celery Workers                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Ingestion   │  │  Processing  │  │     Publishing       │  │
│  │    Worker    │  │    Worker    │  │       Worker         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Технологический стек

### Backend
| Технология | Назначение |
|------------|------------|
| Python 3.11+ | Основной язык разработки |
| FastAPI | Веб-фреймворк |
| SQLAlchemy 2.0 | ORM для работы с БД |
| Alembic | Миграции базы данных |
| Celery | Фоновые задачи |
| Redis | Брокер сообщений и кэш |
| Pydantic | Валидация данных |
| Python-JOSE | JWT-токены |
| Passlib | Хеширование паролей |
| AIOHTTP | HTTP-клиент |
| Feedparser | Парсинг RSS/Atom |
| AIogram 3 | Telegram бот |

### Frontend
| Технология | Назначение |
|------------|------------|
| React 18 | UI-фреймворк |
| TypeScript | Типизация |
| Vite | Сборка |
| Tailwind CSS | Стилизация |
| React Router | Роутинг |
| TanStack Query | Состояние данных |
| React Hook Form | Формы |
| React Hot Toast | Уведомления |
| Lucide React | Иконки |
| Recharts | Графики |

### Инфраструктура
| Технология | Назначение |
|------------|------------|
| Docker | Контейнеризация |
| Docker Compose | Оркестрация |
| PostgreSQL | Основная БД |
| Redis | Кэш и очереди |
| Nginx | Обратный прокси |

---

## 🚀 Быстрый старт

### Предварительные требования

- Docker 24+
- Docker Compose 2.20+
- Git

### Установка

1. **Клонирование репозитория**
   ```bash
   git clone <repository-url>
   cd content-aggregator
   ```

2. **Настройка окружения**
   ```bash
   cp .env.example .env
   # Отредактируйте .env под ваши needs
   ```

3. **Запуск системы**
   ```bash
   docker-compose up -d
   ```

4. **Проверка статуса**
   ```bash
   docker-compose ps
   ```

5. **Доступ к приложениям**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Flower (мониторинг Celery): http://localhost:5555

---

## ⚙️ Конфигурация

### Переменные окружения

#### Общие
| Переменная | Обязательная | По умолчанию | Описание |
|------------|--------------|--------------|----------|
| `ENVIRONMENT` | Нет | `development` | Режим работы |
| `DEBUG` | Нет | `true` | Режим отладки |
| `SECRET_KEY` | Да | - | Секретный ключ для JWT |
| `ALGORITHM` | Нет | `HS256` | Алгоритм JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Нет | `30` | Время жизни токена |

#### База данных
| Переменная | Обязательная | По умолчанию | Описание |
|------------|--------------|--------------|----------|
| `DATABASE_URL` | Да | - | URL для подключения к PostgreSQL |
| `REDIS_URL` | Да | - | URL для подключения к Redis |

#### Telegram
| Переменная | Обязательная | По умолчанию | Описание |
|------------|--------------|--------------|----------|
| `TELEGRAM_BOT_TOKEN` | Да | - | Токен Telegram бота |
| `TELEGRAM_MODERATION_CHAT_ID` | Да | - | ID чата для модерации |

#### OpenAI (опционально)
| Переменная | Обязательная | По умолчанию | Описание |
|------------|--------------|--------------|----------|
| `OPENAI_API_KEY` | Нет | - | API ключ OpenAI |
| `OPENAI_MODEL` | Нет | `gpt-4` | Модель для AI-обработки |

### Пример `.env`

```env
# Общие
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# База данных
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/content_aggregator
REDIS_URL=redis://localhost:6379/0

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_MODERATION_CHAT_ID=-1001234567890

# OpenAI (опционально)
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4
```

---

## 📁 Структура проекта

```
content-aggregator/
├── Backend/                     # Backend приложение
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI приложение
│   │   ├── config.py            # Настройки
│   │   ├── database.py          # Подключение к БД
│   │   │
│   │   ├── api/                 # REST API
│   │   │   ├── __init__.py
│   │   │   ├── router.py        # Роутер
│   │   │   ├── deps.py          # Зависимости
│   │   │   └── health.py        # Health check
│   │   │
│   │   ├── models/              # SQLAlchemy модели
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Base класс
│   │   │   ├── user.py          # Пользователи
│   │   │   ├── source.py        # Источники
│   │   │   ├── article.py       # Статьи
│   │   │   ├── batch.py         # Пачки
│   │   │   ├── publish_target.py
│   │   │   └── publish_job.py
│   │   │
│   │   ├── schemas/             # Pydantic схемы
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── source.py
│   │   │   ├── article.py
│   │   │   ├── batch.py
│   │   │   ├── publish_target.py
│   │   │   └── publish_job.py
│   │   │
│   │   ├── services/            # Бизнес-логика
│   │   │   ├── __init__.py
│   │   │   ├── ingestion_service.py
│   │   │   ├── processing_service.py
│   │   │   ├── publishing_service.py
│   │   │   ├── batch_service.py
│   │   │   └── ai_service.py
│   │   │
│   │   ├── workers/             # Celery задачи
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py
│   │   │   └── tasks.py
│   │   │
│   │   ├── telegram/            # Telegram бот
│   │   │   ├── __init__.py
│   │   │   ├── handler.py
│   │   │   └── callbacks.py
│   │   │
│   │   └── utils/               # Утилиты
│   │       ├── __init__.py
│   │       ├── redis.py
│   │       ├── url.py
│   │       └── logging.py
│   │
│   ├── migrations/              # Alembic миграции
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                    # Frontend приложение
│   ├── src/
│   │   ├── api/                 # API клиент
│   │   ├── assets/              # Статические файлы
│   │   ├── components/          # Компоненты
│   │   │   ├── layout/          # Layout компоненты
│   │   │   └── ui/              # UI компоненты
│   │   ├── hooks/               # React хуки
│   │   ├── pages/               # Страницы
│   │   ├── types/               # TypeScript типы
│   │   ├── utils/               # Утилиты
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── vite.config.ts
│
├── docker-compose.yml           # Docker Compose
├── Dockerfile
├── .env.example
└── README.md
```

---

## 📚 API документация

### Аутентификация

Все защищённые эндпоинты требуют JWT-токен в заголовке:
```
Authorization: Bearer <token>
```

### Эндпоинты

#### Аутентификация
| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/auth/register` | Регистрация |
| POST | `/api/auth/login` | Вход |
| POST | `/api/auth/refresh` | Обновление токена |
| GET | `/api/auth/me` | Текущий пользователь |

#### Источники
| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/sources` | Список источников |
| POST | `/api/sources` | Создание источника |
| GET | `/api/sources/{id}` | Получить источник |
| PUT | `/api/sources/{id}` | Обновить источник |
| DELETE | `/api/sources/{id}` | Удалить источник |
| POST | `/api/sources/{id}/fetch` | Запустить сбор |
| GET | `/api/sources/{id}/runs` | История сборов |

#### Статьи
| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/articles` | Список статей |
| POST | `/api/articles` | Создать статью |
| GET | `/api/articles/{id}` | Получить статью |
| PUT | `/api/articles/{id}` | Обновить статью |
| DELETE | `/api/articles/{id}` | Удалить статью |
| POST | `/api/articles/{id}/process` | Обработать статью |
| POST | `/api/articles/{id}/rewrite` | AI-переписывание |
| GET | `/api/articles/{id}/versions` | Версии статьи |

#### Пачки
| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/batches` | Список пачек |
| GET | `/api/batches/{id}` | Получить пачку |
| PUT | `/api/batches/{id}/send` | Отправить в Telegram |
| POST | `/api/batches/{article_id}/approve` | Одобрить статью |
| POST | `/api/batches/{article_id}/reject` | Отклонить статью |

#### Публикация
| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/targets` | Список целей |
| POST | `/api/targets` | Создать цель |
| GET | `/api/jobs` | Список заданий |
| POST | `/api/jobs/{id}/execute` | Выполнить публикацию |

#### Админ
| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/admin/stats` | Статистика |
| POST | `/api/admin/batches/create` | Создать пачки |
| POST | `/api/admin/sources/fetch-all` | Сбор со всех источников |

---

## ⚡ Celery задачи

### Периодические задачи

| Задача | Расписание | Описание |
|--------|------------|----------|
| `fetch_all_sources` | `*/5 * * * *` | Сбор со всех источников каждые 5 минут |
| `create_moderation_batches` | `*/10 * * * *` | Создание пачек каждые 10 минут |
| `execute_scheduled_jobs` | `* * * * *` | Выполнение запланированных публикаций |
| `housekeeping` | `0 3 * * *` | Очистка каждый день в 3:00 |
| `update_source_reputations` | `0 0 * * *` | Обновление репутации источников |

### API задачи

| Задача | Описание |
|--------|----------|
| `fetch_source_task` | Сбор с одного источника |
| `process_article_task` | Обработка одной статьи |
| `send_batches_to_telegram` | Отправка пачек в Telegram |
| `execute_publish_job_task` | Выполнение публикации |
| `ai_rewrite_task` | AI-переписывание статьи |
| `send_alert` | Отправка уведомления |

### Мониторинг задач

Flower доступен по адресу: http://localhost:5555

---

## 🤖 Telegram бот

### Команды

| Команда | Описание |
|---------|----------|
| `/start` | Начало работы |
| `/help` | Помощь |
| `/status` | Статус системы |
| `/stats` | Статистика |

### Модерация

Модерация осуществляется через Telegram-чат:

1. Пачка статей отправляется в чат модерации
2. Модератор просматривает статьи
3. Нажимает кнопку "Одобрить" или "Отклонить"
4. После модерации статьи публикуются

---

## 👨‍💻 Разработка

### Backend

1. **Создание виртуального окружения**
   ```bash
   cd Backend
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # или
   .\venv\Scripts\activate   # Windows
   ```

2. **Установка зависимостей**
   ```bash
   pip install -r requirements.txt
   ```

3. **Запуск в режиме разработки**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Миграции базы данных**
   ```bash
   # Создать миграцию
   alembic revision --autogenerate -m "description"

   # Применить миграции
   alembic upgrade head
   ```

5. **Запуск Celery**
   ```bash
   celery -A app.workers.celery_app worker --loglevel=info
   ```

### Frontend

1. **Установка зависимостей**
   ```bash
   cd frontend
   npm install
   ```

2. **Запуск в режиме разработки**
   ```bash
   npm run dev
   ```

3. **Сборка для production**
   ```bash
   npm run build
   ```

### Тесты

```bash
# Backend тесты
cd Backend
pytest

# Frontend тесты
cd frontend
npm run test
```

---

## 🚀 Развёртывание

### Docker Compose (рекомендуется)

```bash
# Сборка и запуск
docker-compose up -d --build

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### Проверка работоспособности

```bash
# Backend health check
curl http://localhost:8000/health

# Frontend
curl http://localhost:5173

# Celery workers
docker-compose exec backend celery -A app.workers.celery_app inspect ping
```

---

## � Развёртывание в Production

### Использование docker-compose.prod.yml

```bash
# 1. Копируем конфигурацию
cp .env.example .env.prod

# 2. Обновляем критические переменные:
# - SECRET_KEY и JWT_SECRET_KEY (минимум 32 символа)
# - DATABASE_URL на реальный хост БД
# - REDIS_URL на реальный хост Redis
# - TELEGRAM_BOT_TOKEN
# - DEBUG=False
# - VITE_API_URL=https://yourdomain.com

# 3. Запуск в production
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 4. Применяем миграции
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### Чеклист перед развертыванием

- [x] Файл [.env.example](.env.example) создан
- [x] Файл [DEPLOYMENT.md](DEPLOYMENT.md) с подробными инструкциями
- [x] Файл [docker-compose.prod.yml](docker-compose.prod.yml) для production
- [x] Файл [nginx.conf](nginx.conf) для reverse proxy
- [x] GitHub Actions workflow для CI/CD

Детальная инструкция находится в **[DEPLOYMENT.md](DEPLOYMENT.md)** 📖

---

## �📊 Мониторинг

### Health checks

| Сервис | URL |
|--------|-----|
| Backend | `http://localhost:8000/health` |
| API Docs | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| Flower | `http://localhost:5555` |

### Логи

```bash
# Все логи
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f worker
```

### Метрики

Flower предоставляет:
- Статистику выполнения задач
- Историю задач
- Нагрузку на воркеры
- Active задачи

---

## 🔒 Безопасность

1. **Аутентификация**: JWT-токены с настраиваемым временем жизни
2. **Авторизация**: RBAC на основе ролей пользователей
3. **Хеширование**:bcrypt для паролей
4. **Валидация**: Pydantic схемы для всех входных данных
5. **CORS**: Настроенные заголовки для frontend

---

## 📝 Лицензия

MIT License

---

## 🤝 Вклад в проект

1. Fork репозитория
2. Создание feature ветки
3. Коммит изменений
4. Push в ветку
5. Создание Pull Request

---

## 📧 Контакты

Для вопросов и предложений создавайте Issues в репозитории.