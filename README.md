# Concessional Loans — Document Check API

Скелет REST API для проверки пакетов документов по льготным кредитам.

## Стек

- Python 3.11 (см. `.python-version` и `Dockerfile`)
- FastAPI
- PostgreSQL
- Docker Compose

## Что есть сейчас

- пустое FastAPI-приложение (`GET /` → `{"status": "ok"}`);
- конфиг через переменные окружения (`app/core/config.py`);
- `Dockerfile` и `docker-compose.yml` (сервис API + PostgreSQL);
- `.env.example` с примером переменных;
- бизнес-логика в `app/domain/`:
  - определение типа документа по имени файла;
  - проверка формата и размера файла;
  - проверка комплектности пакета по программе;
  - формирование статуса и причины (`approved` / `rejected`).

Эндпоинты `/api/checks`, модели БД, миграции и тесты пока не реализованы.

## Запуск

```bash
cp .env.example .env
docker compose up --build
```

API: http://localhost:8000/

## Переменные окружения

| Переменная     | Описание                          |
|----------------|-----------------------------------|
| `DATABASE_URL` | URL подключения к PostgreSQL      |
| `APP_HOST`     | Хост приложения                   |
| `APP_PORT`     | Порт приложения                   |
| `UPLOAD_DIR`   | Каталог для загруженных файлов    |
