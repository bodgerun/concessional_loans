# Concessional Loans

REST API для проверки пакетов документов по льготным кредитным программам (`federal` / `regional`): 
- загрузка файлов;
- валидация комплектности и форматов;
- сохранение результата и истории в PostgreSQL.

## Быстрый старт

Запуск:

```bash
cp .env.example .env
docker compose up --build
```

При старте контейнер API дожидается готовности PostgreSQL, выполняет `alembic upgrade head` и поднимает uvicorn.

| Сервис | URL |
|--------|-----|
| API | http://localhost:8000/ |
| OpenAPI (Swagger) | http://localhost:8000/docs |

Остановка:

```bash
docker compose down
```

## API

| Метод | Путь | Описание | Коды |
|-------|------|----------|------|
| `POST` | `/api/checks` | Загрузка пакета (`multipart/form-data`: `program`, `files`) и запуск проверки | `201`, `400`, `422` |
| `GET` | `/api/checks` | Список проверок (id, дата, программа, статус, число документов) | `200` |
| `GET` | `/api/checks/{id}` | Полный результат конкретной проверки | `200`, `404`, `422` |

Пример запроса:

```bash
curl -X POST "http://localhost:8000/api/checks" \
  -F "program=federal" \
  -F "files=@договор.pdf" \
  -F "files=@спецификация.pdf" \
  -F "files=@счёт.pdf" \
  -F "files=@акт.pdf"
```

Правила проверки (кратко):

- тип документа определяется по имени файла (RU/EN: договор/contract, спецификация/spec, счёт/invoice, акт/УПД/act);
- `federal` — обязательны договор, спецификация, счёт, акт; `regional` — договор, счёт, акт;
- допустимые форматы: PDF, DOCX, JPG, PNG; размер файла ≤ 20 МБ;
- нераспознанное имя → `warning`; нарушения формата/размера/комплектности → `error`;
- итог: `approved` (нет ошибок) или `rejected` (есть хотя бы одна ошибка).

## Тесты

Тесты не требуют Docker и PostgreSQL: доменная логика, сервисы и HTTP-слой покрыты pytest с in-memory/fixtures.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest
```

Выборочный запуск:

```bash
pytest tests/domain/          # определение типа документа, комплектность, статус
pytest tests/services/        # storage и оркестрация проверки
pytest tests/api/             # эндпоинты и маппинг ответов
```

## Переменные окружения

Шаблон: [`.env.example`](.env.example). 
При запуске через `docker compose up` значения можно не задавать вручную — в `docker-compose.yml` есть разумные defaults.

| Переменная | Описание | Пример |
|------------|----------|--------|
| `DATABASE_URL` | URL PostgreSQL для SQLAlchemy (`psycopg2`) | `postgresql+psycopg2://postgres:postgres@db:5432/concessional_loans` |
| `APP_HOST` | Хост, на котором слушает uvicorn | `0.0.0.0` |
| `APP_PORT` | Порт API (снаружи Compose пробрасывается как `${APP_PORT:-8000}:8000`) | `8000` |
| `UPLOAD_DIR` | Каталог локального хранилища загрузок | `uploads` |

Заметки:

- PostgreSQL доступен API внутри сети Compose по адресу `db:5432` и не публикуется на хост, чтобы не конфликтовать с локальной БД;
- для запуска API вне Docker нужна отдельно доступная PostgreSQL и соответствующий `DATABASE_URL` (например, с `localhost:5432`);
- файлы сохраняются как `UPLOAD_DIR/{check_id}/{original_filename}`; каталог `uploads/` монтируется в контейнер API.

## Архитектура

Три слоя сверху вниз: HTTP, оркестрация, доменная логика. 
Диск и PostgreSQL — внешние хранилища (взаимодействие через `services/`).

```text
Клиент
  │
  ▼
api/ + schemas/     HTTP: маршруты, коды, multipart, контракты ответа
  │
  ▼
services/           оркестрация: CheckService + локальный storage
  │
  ├──► domain/      правила без I/O: тип файла, комплектность, статус
  ├──► uploads/     файлы: UPLOAD_DIR/{check_id}/{filename}
  └──► PostgreSQL   метаданные: checks, documents, issues
```

Примечания:
- `domain/` не знает про HTTP, диск и БД. 
- `api/` не пишет в БД напрямую — только через `CheckService`.

Каталоги:

```text
app/
  api/        # routes, deps, errors, mappers
  schemas/    # Pydantic-контракты
  domain/     # бизнес-логика (без I/O)
  services/   # CheckService + сохранение файлов
  models/     # ORM: checks, documents, issues
  db/         # engine, session
  core/       # Settings (.env)
alembic/      # миграции (при старте: alembic upgrade head)
tests/        # domain / services / api
```

Потоки:
- `POST /api/checks`: принять файлы → сохранить на диск → проверить в `domain` → записать метаданные в PostgreSQL → ответить `201` (при сбое персистенции файлы пакета удаляются).
- `GET` отдаёт только метаданные из БД, не содержимое файлов.

## Используемые технологии

| Технология | Комментарий |
|------------|--------|
| **FastAPI** | web-фреймворк |
| **Pydantic** | валидация тел ответов и конфигурации из `.env` |
| **SQLAlchemy** | ORM для истории проверок в PostgreSQL |
| **Alembic** | миграции / изменение схемы БД |
| **PostgreSQL** | система управления БД (DBMS) |
| **psycopg2** | драйвер PostgreSQL для SQLAlchemy |
| **python-multipart** | разбор загрузок файлов |
| **Uvicorn** | ASGI-сервер |
| **Docker Compose** | запуск API + БД одной командой |
| **pytest + httpx** | тесты домена и HTTP-слоя |

Зависимости: [`requirements.txt`](requirements.txt); управление пакетами — pip.

## Ограничения и упрощения

Сознательно вынесено за рамки MVP тестового задания:

- **Нет AI/OCR**: поле `extracted` в ответе зарезервировано (`null`); извлечение реквизитов из содержимого файлов не реализовано.
- **Синхронная проверка**: статус `check_in_progress` зарезервирован под будущий асинхронный сценарий и сейчас не выставляется.
- **Локальное файловое хранилище**: не S3/MinIO (для офлайн-сценария этого достаточно).
- **Нет аутентификации и ролей**, нет версионности повторных загрузок одного документа.
- **Тип документа только по имени файла**, не по содержимому.
- **Нет отдельного эндпоинта скачивания файлов** (хранение нужно для аудита и последующих AI-модулей).

Эти ограничения оставляют понятные точки расширения под полный TO BE-процесс из кейса.
