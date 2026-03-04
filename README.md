Carousel Generator + Editor (MVP)

Небольшой сервис для генерации каруселей для Instagram с помощью AI.

Пользователь может:
	•	создать карусель из текста или видео
	•	задать параметры (язык, количество слайдов, стиль)
	•	сгенерировать структуру слайдов через LLM
	•	отредактировать текст и дизайн
	•	экспортировать готовую карусель в ZIP с изображениями 1080×1350

Демо:
https://test.cakedevart.ru

⸻

Быстрый запуск

git clone <repo>
cd testMVP
cp .env.example .env
docker-compose up --build

Перед запуском нужно заполнить .env.

Файл .env не добавляется в git. Все секреты хранятся только там.

После запуска сервисы будут доступны примерно через 20–30 секунд.

**Автозапуск после перезагрузки сервера**

Контейнеры имеют `restart: unless-stopped` — Docker перезапустит их после ребута.

Чтобы проект поднимался автоматически при загрузке системы (если ещё не запущен):

```bash
sudo cp carousel.service /etc/systemd/system/
# Отредактируй WorkingDirectory в /etc/systemd/system/carousel.service
sudo systemctl daemon-reload
sudo systemctl enable carousel
sudo systemctl start carousel
```

сервис	адрес
Frontend	http://localhost:3090
Backend API	http://localhost:8090
Swagger	http://localhost:8090/docs
MinIO	http://localhost:9091


⸻

Переменные окружения

Основные настройки задаются через .env.

переменная	описание
POSTGRES_PASSWORD	пароль postgres
S3_ACCESS_KEY	ключ доступа MinIO
S3_SECRET_KEY	секретный ключ MinIO
LLM_BASE_URL	URL OpenAI-совместимого API
LLM_API_KEY	ключ LLM
BACKEND_PUBLIC_URL	публичный адрес backend
NUXT_PUBLIC_API_BASE	адрес API для фронтенда

Дополнительно:

переменная	описание
S3_BUCKET	bucket MinIO
LLM_MODEL	модель LLM
APP_API_KEY	защита API


⸻

Mock режим

Если LLM_API_KEY пустой или равен "mock", генерация работает без обращения к модели.

В этом режиме создаются тестовые слайды. Это позволяет проверить весь flow без реального LLM.

⸻

Авторизация

Если задан APP_API_KEY, все запросы к API должны содержать заголовок:

X-API-Key: ваш_ключ

Если переменная не задана, авторизация отключена.

⸻

Основные API

Карусели

Создать карусель

curl -X POST https://test.cakedevart.ru/api/carousels \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI в бизнесе",
    "source_type": "text",
    "source_payload": {
      "text": "Искусственный интеллект меняет бизнес."
    },
    "format": {
      "slides_count": 6,
      "language": "ru"
    }
  }'

Получить список каруселей

curl https://test.cakedevart.ru/api/carousels

Получить одну карусель

curl https://test.cakedevart.ru/api/carousels/{id}


⸻

Генерация

Запуск генерации

curl -X POST https://test.cakedevart.ru/api/generations \
  -H "Content-Type: application/json" \
  -d '{"carousel_id": "ID"}'

Проверка статуса

curl https://test.cakedevart.ru/api/generations/{id}

Статусы:

queued
running
done
failed


⸻

Слайды

Получить слайды

curl https://test.cakedevart.ru/api/carousels/{id}/slides

Редактировать слайд

curl -X PATCH https://test.cakedevart.ru/api/carousels/{id}/slides/{slide_id}


⸻

Экспорт

Запуск экспорта

curl -X POST https://test.cakedevart.ru/api/exports \
  -H "Content-Type: application/json" \
  -d '{"carousel_id": "ID"}'

Проверить статус

curl https://test.cakedevart.ru/api/exports/{id}

После завершения возвращается ссылка на ZIP.

ZIP содержит изображения:

slide_01.png
slide_02.png
slide_03.png
...

Каждый файл имеет размер 1080×1350.

⸻

Архитектура

Frontend (Nuxt)
        |
        v
Backend (FastAPI)
        |
   -------------------
   |        |        |
Postgres   MinIO    LLM
                     |
                 Playwright

Backend

Python 3.12 + FastAPI
SQLAlchemy async + Alembic

Frontend

Nuxt 3 (Vue)

Database

PostgreSQL

Storage

MinIO (S3 совместимое)

Render

Playwright (Chromium)

⸻

Структура проекта

testMVP
│
├ backend
│ ├ app
│ ├ models
│ ├ services
│ ├ api
│ └ templates
│
├ frontend
│ └ pages
│
└ docker-compose.yml


⸻

Что упрощено

Это MVP, поэтому некоторые вещи сделаны проще.

Видео не анализируется
Видео просто загружается и хранится. Транскрипция не реализована.

Нет пользователей
Система рассчитана на одного пользователя.

Дизайн слайдов минимальный
Есть только три шаблона.

BackgroundTasks вместо очереди
Для MVP используется встроенный механизм FastAPI.

Рендер последовательный
PNG генерируются по одному через Playwright.

⸻

Используемые технологии

Backend
	•	Python
	•	FastAPI
	•	SQLAlchemy
	•	Alembic

Frontend
	•	Nuxt 3
	•	Vue 3

Инфраструктура
	•	Docker
	•	PostgreSQL
	•	MinIO
	•	Playwright

LLM
	•	OpenAI-совместимый API

⸻

Production

Проект развёрнут на сервере с nginx и HTTPS.

Frontend
https://test.cakedevart.ru

API
https://test.cakedevart.ru/api/

Swagger
https://test.cakedevart.ru/api/docs
