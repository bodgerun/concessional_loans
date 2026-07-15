# Concessional Loans — Document Check API

Скелет REST API для проверки пакетов документов по льготным кредитам.

## Стек

- Python 3.11 (см. `.python-version` и `Dockerfile`)
- FastAPI
- PostgreSQL 16 + SQLAlchemy 2 + Alembic
- Docker Compose
- pytest (тесты доменной логики)

## Что есть сейчас

- FastAPI-приложение (`GET /` → `{"status": "ok"}`);
- конфиг через переменные окружения (`app/core/config.py`);
- `Dockerfile` и `docker-compose.yml` (сервис API + PostgreSQL);
- `.env.example` с примером переменных;
- бизнес-логика в `app/domain/`:
  - определение типа документа по имени файла;
  - проверка формата и размера файла;
  - проверка комплектности пакета по программе;
  - формирование статуса и причины (`approved` / `rejected`);
- SQLAlchemy-модели: `checks`, `documents`, `issues` (`app/models/`);
- Alembic-миграция `0001_initial` (применяется при старте контейнера API);
- локальное файловое хранилище `app/services/storage.py`
  (`UPLOAD_DIR/{check_id}/{filename}`);
- оркестрация проверки `app/services/check_service.py`;
- эндпоинты:
  - `POST /api/checks` — загрузка пакета и запуск проверки (`201`);
  - `GET /api/checks` — список проверок (`200`);
  - `GET /api/checks/{id}` — полный результат конкретной проверки (`200`);
- HTTP-ошибки: `400` (нет файлов), `404` (проверка не найдена),
  `422` (невалидный `program` / UUID / форма);
- pytest-тесты для `app/domain/`, `app/services/` и `app/api/` в `tests/`.

## Запуск

```bash
cp .env.example .env
docker compose up --build
```

При старте API контейнер ждёт готовности PostgreSQL, затем выполняет
`alembic upgrade head` и поднимает uvicorn.

API: http://localhost:8000/

### Локальные миграции

Если нужно прогнать миграции вручную (из venv, с доступом к той же БД,
что в Compose):

```bash
alembic upgrade head
alembic current
```

## Тесты

Из корня репозитория (нужны зависимости из `requirements.txt`):

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest
```

Запуск только доменных тестов:

```bash
pytest tests/domain/
```

## Переменные окружения

| Переменная     | Описание                          |
|----------------|-----------------------------------|
| `DATABASE_URL` | URL подключения к PostgreSQL      |
| `APP_HOST`     | Хост приложения                   |
| `APP_PORT`     | Порт приложения                   |
| `UPLOAD_DIR`   | Каталог для загруженных файлов    |
