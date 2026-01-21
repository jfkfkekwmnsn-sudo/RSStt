# 🚀 Гайд по развертыванию и запуску

Полное пошаговое руководство для запуска проекта локально и на production сервере.

## 📋 Содержание

1. [Локальный запуск](#-локальный-запуск)
2. [Production развертывание](#-production-развертывание)
3. [Команды управления](#-команды-управления)
4. [Troubleshooting](#-troubleshooting)

---

## 💻 Локальный запуск

### Требования

- Docker 24+ и Docker Compose 2.20+
- 2GB свободной памяти
- Порты 8000, 3000, 5432, 6379 свободны

### Шаг 1: Подготовка

```bash
# Клонирование репозитория
git clone <repository-url>
cd project

# Копирование конфигурации
cp .env.example .env
```

### Шаг 2: Настройка .env

Отредактируйте `.env` файл. **Обязательные переменные:**

```env
SECRET_KEY=your-super-secret-key-32-chars-min-change-this
JWT_SECRET_KEY=your-jwt-secret-key-32-chars-min-change-this
DEBUG=true
```

**Дополнительно (опционально):**

```env
# Telegram (если нужна bot интеграция)
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_MODERATION_CHAT_ID=-1001234567890

# OpenAI (если нужна AI обработка)
OPENAI_API_KEY=sk-your-key
```

### Шаг 3: Запуск контейнеров

```bash
# Сборка и запуск
docker-compose up -d --build

# Ожидание инициализации (~30 сек)
echo "Ожидаем инициализацию БД..."
sleep 30

# Проверка статуса
docker-compose ps
```

Все контейнеры должны быть в статусе **Up**.

### Шаг 4: Инициализация БД

```bash
# Применение миграций
docker-compose exec api alembic upgrade head

# Успешный результат:
# INFO  [alembic.runtime.migration] Running upgrade ... 
# Done
```

### Шаг 5: Проверка

```bash
# Health check
curl http://localhost:8000/health
# Результат: {"status":"ok"}

# Доступ к приложению
echo "Frontend:  http://localhost:3000"
echo "API Docs:  http://localhost:8000/docs"
echo "Health:    http://localhost:8000/health"
```

✅ **Готово!** Приложение запущено локально.

---

## 🌐 Production развертывание

### Требования

- Linux сервер (Ubuntu 20.04+, CentOS 7+)
- Docker и Docker Compose
- Минимум 2GB RAM, 20GB disk space
- Белый IP адрес

### Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt-get update && sudo apt-get upgrade -y

# Установка Docker (если не установлен)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Проверка установки
docker --version
docker-compose --version
```

### Шаг 2: Клонирование проекта

```bash
# Переход в рабочую директорию
cd /opt
sudo git clone <repository-url> news-aggregator
cd news-aggregator

# Настройка прав доступа
sudo chown -R $USER:$USER /opt/news-aggregator
```

### Шаг 3: Конфигурация

```bash
# Копирование конфигурации
cp .env.example .env

# Редактирование для production
nano .env
```

**Важные изменения для production:**

```env
# Безопасность
DEBUG=false                 # ⚠️ ОБЯЗАТЕЛЬНО false!
SECRET_KEY=<очень-длинный-случайный-ключ-64-символа>
JWT_SECRET_KEY=<очень-длинный-случайный-ключ-64-символа>

# База данных (если не используется Docker)
DATABASE_URL=postgresql+asyncpg://user:password@db-host:5432/news_aggregator
REDIS_URL=redis://redis-host:6379/0

# API (внешний URL)
VITE_API_URL=https://yourdomain.com

# Telegram (обязательно)
TELEGRAM_BOT_TOKEN=<ваш-боток>
TELEGRAM_MODERATION_CHAT_ID=<ID-чата>

# OpenAI (опционально)
OPENAI_API_KEY=<ваш-ключ>
```

**Генерация безопасных ключей:**

```bash
# SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Шаг 4: Запуск в production

```bash
# Очистка старых образов (если переразворачиваете)
sudo docker-compose down
sudo docker system prune -f

# Запуск production конфигурации
sudo docker-compose up -d --build

# Проверка статуса
docker-compose ps
```

### Шаг 5: Инициализация БД

```bash
# Применение миграций
docker-compose exec api alembic upgrade head

# Проверка логов
docker-compose logs api | tail -20
```

### Шаг 6: Настройка Nginx (опционально)

Если используется reverse proxy:

```bash
# Редактирование nginx конфигурации
sudo nano /etc/nginx/sites-available/news-aggregator
```

Пример конфигурации:

```nginx
upstream backend {
    server api:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    client_max_body_size 20M;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Шаг 7: SSL сертификат (рекомендуется)

```bash
# Установка Certbot
sudo apt-get install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot certonly --nginx -d yourdomain.com
```

### Шаг 8: Проверка production

```bash
# Health check
curl https://yourdomain.com/health

# API документация
curl https://yourdomain.com/docs

# Логи
docker-compose logs -f api
```

✅ **Production развернут!**

---

## 🛠 Команды управления

### Просмотр статуса

```bash
# Статус всех контейнеров
docker-compose ps

# Объем используемых ресурсов
docker stats

# Список сетей
docker network ls
```

### Логи

```bash
# Все логи
docker-compose logs

# Последние 100 строк
docker-compose logs --tail=100

# Реальное время (API)
docker-compose logs -f api

# Реальное время (все)
docker-compose logs -f

# Только ошибки
docker-compose logs | grep ERROR
```

### Управление сервисами

```bash
# Перезагрузка конкретного сервиса
docker-compose restart api
docker-compose restart worker
docker-compose restart frontend

# Остановка
docker-compose stop

# Запуск
docker-compose start

# Полная переборка
docker-compose down -v && docker-compose up -d --build
```

### Работа с БД

```bash
# Подключение к PostgreSQL
docker-compose exec db psql -U postgres -d news_aggregator

# Внутри psql:
\dt                    # Список таблиц
SELECT * FROM "user";  # Просмотр пользователей
\q                     # Выход

# Применение миграций
docker-compose exec api alembic upgrade head

# Откат последней миграции
docker-compose exec api alembic downgrade -1

# Откат всех миграций
docker-compose exec api alembic downgrade base

# Просмотр истории миграций
docker-compose exec api alembic history
```

### Масштабирование

```bash
# Увеличение worker процессов
docker-compose up -d --scale worker=3

# Проверка
docker-compose ps | grep worker
```

---

## 🐛 Troubleshooting

### Проблема: "API не запускается"

**Симптомы:**
```bash
docker-compose ps
# api - Exit Code 1
```

**Решение:**

```bash
# 1. Проверьте логи
docker-compose logs api

# 2. Проверьте что БД готова
docker-compose logs db

# 3. Перезагрузите оба контейнера
docker-compose restart db api
sleep 30

# 4. Попробуйте снова инициализировать
docker-compose exec api alembic upgrade head
```

### Проблема: "connection refused" (БД не отвечает)

**Решение:**

```bash
# 1. Проверьте что контейнер БД запущен
docker-compose ps db

# 2. Проверьте логи БД
docker-compose logs db

# 3. Подождите, пока БД инициализируется (30-60 сек)
sleep 60

# 4. Попробуйте подключиться к БД
docker-compose exec db psql -U postgres -c "SELECT 1"
```

### Проблема: "Worker не обрабатывает задачи"

**Решение:**

```bash
# 1. Проверьте что Redis запущен
docker-compose exec redis redis-cli ping
# Результат: PONG

# 2. Проверьте логи worker
docker-compose logs worker

# 3. Перезагрузите worker
docker-compose restart worker

# 4. Проверьте статус Celery
docker-compose exec worker celery -A app.workers.celery_app inspect active
```

### Проблема: "Frontend не загружается"

**Решение:**

```bash
# 1. Проверьте логи frontend
docker-compose logs frontend

# 2. Проверьте что файлы собраны
docker-compose exec frontend ls -la /usr/share/nginx/html/

# 3. Проверьте конфигурацию nginx
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf

# 4. Перезагрузите frontend
docker-compose restart frontend
```

### Проблема: "Port already in use"

**Решение:**

```bash
# Найдите процесс на порту
sudo lsof -i :8000
sudo lsof -i :3000

# Убейте процесс (если не Docker)
sudo kill -9 <PID>

# Или измените порты в docker-compose.yml
# Или используйте другие порты:
docker-compose up -d -p 9000:8000 -p 9001:3000
```

### Проблема: "Out of memory"

**Решение:**

```bash
# Проверьте использование памяти
docker stats

# Очистите неиспользуемые образы
docker image prune -a

# Очистите контейнеры
docker container prune

# Увеличьте лимит в docker-compose.yml
# services:
#   api:
#     mem_limit: 2g
#     memswap_limit: 4g
```

### Проблема: "Миграция упала"

**Решение:**

```bash
# 1. Посмотрите что пошло не так
docker-compose logs api | grep -i error

# 2. Откатитесь назад на одну миграцию
docker-compose exec api alembic downgrade -1

# 3. Проверьте состояние
docker-compose exec api alembic current

# 4. Попробуйте миграцию заново
docker-compose exec api alembic upgrade head
```

---

## ✅ Чек-лист перед запуском

### Локально

- [ ] Docker и Docker Compose установлены
- [ ] Порты 8000, 3000, 5432, 6379 свободны
- [ ] `.env` скопирован из `.env.example`
- [ ] `SECRET_KEY` и `JWT_SECRET_KEY` установлены
- [ ] Все контейнеры запущены (`docker-compose ps`)
- [ ] БД инициализирована (`alembic upgrade head`)
- [ ] Health check успешен (`curl http://localhost:8000/health`)

### Production

- [ ] Linux сервер подготовлен
- [ ] Docker установлен и работает
- [ ] Проект клонирован в `/opt`
- [ ] `.env` создан с production значениями
- [ ] `SECRET_KEY` и `JWT_SECRET_KEY` - 64+ символа
- [ ] `TELEGRAM_BOT_TOKEN` установлен
- [ ] `DEBUG=false`
- [ ] Все контейнеры запущены
- [ ] БД инициализирована
- [ ] SSL сертификат установлен
- [ ] Nginx конфигурирован
- [ ] Health check успешен

---

## 📞 Дополнительная помощь

### Полезные ссылки

- **API Документация:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Flower (Celery мониторинг):** http://localhost:5555 (если включен)

### Команды для debug

```bash
# Подключиться в контейнер API
docker-compose exec api bash

# Запустить Python интерпретатор
docker-compose exec api python

# Вывести текущие переменные окружения
docker-compose exec api env

# Проверить импорты Python
docker-compose exec api python -c "import app.models; print('OK')"
```

### Логирование

```bash
# Если нужны подробные логи, отредактируйте .env
DEBUG=true              # Включить debug режим
LOG_LEVEL=DEBUG        # Если есть в приложении
```

---

**Версия:** 1.0.3  
**Последнее обновление:** 2026-01-21  
**Автор:** AI Assistant

Если у вас есть вопросы - создавайте Issues в репозитории! 🚀
