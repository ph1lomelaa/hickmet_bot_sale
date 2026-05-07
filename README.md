# Bull Project

Проект для бронирования и сопровождения паломников. Система состоит из Telegram-бота для менеджеров, FastAPI API для web/app-интерфейсов, слоя интеграции с Google Sheets, OCR-пайплайна для распознавания паспортов и PostgreSQL для хранения состояния бронирований.

README ниже написан как быстрый онбординг для новых разработчиков: что где находится, как это запускается и куда идти при изменениях.

## 1. Что делает система

Основные сценарии:

- менеджер оформляет бронь через Telegram-бота;
- система сохраняет бронь в БД;
- система пишет данные группы в Google Sheets;
- API обслуживает admin/care/webapp-интерфейсы;
- OCR-эндпоинты принимают фото или PDF паспорта, сохраняют файл и пытаются извлечь данные;
- админы получают заявки на отмену и перенос, подтверждают их через API и веб-интерфейсы;
- WebSocket-каналы рассылают новые телефоны и admin-request события в реальном времени.

## 2. Архитектура

### Контейнеры

Конфигурация контейнеров описана в `bull_project/docker-compose.yml`.

- `api`
  Запускает FastAPI-приложение из `bull_project/bull_bot/core/api_server.py`.
- `worker`
  Запускает Telegram-бота из `bull_project/bull_bot/main.py`.
- `db`
  PostgreSQL 17.
- `caddy`
  Reverse proxy / TLS.
- `dozzle`
  Просмотр Docker-логов.

Важно: `api` и `worker` собираются из одного Docker-образа через `bull_project/Dockerfile`. Различается только команда запуска и набор переменных окружения.

### Логическая схема

```text
Telegram manager
  -> aiogram worker
  -> database.requests
  -> PostgreSQL
  -> google_sheets.writer / allocator / client

Web interfaces
  -> FastAPI API
  -> database.requests
  -> PostgreSQL
  -> websocket_manager

Passport upload
  -> FastAPI /api/passport* endpoints
  -> tmp/uploads
  -> EasyOCR parser
  -> parsed fields -> booking flow
```

## 3. Структура репозитория

```text
bull_project/
  Dockerfile
  docker-compose.yml
  requirements.txt
  bull_bot/
    main.py                  # entrypoint Telegram-бота
    api/                     # FastAPI схемы, utils, routes
    config/                  # env/config/constants
    core/                    # API server, OCR, websockets, Google Sheets, utils
    database/                # SQLAlchemy models + запросы + init
    handlers/                # aiogram routers/handlers
    states/                  # FSM state definitions
    credentials/             # service_account.json для Google
    webapp/                  # HTML страницы для bot/web flows
  admin_webapp/              # admin UI assets
  care_webapp/               # care UI, отдаётся FastAPI как static
  assets/                    # общие assets
  tools/                     # OCR/annotation/training utilities
```

## 4. Основные точки входа

### API

`bull_project/bull_bot/core/api_server.py`

Что делает:

- создаёт FastAPI app;
- включает CORS без ограничений;
- подключает все route-модули;
- на startup вызывает `init_db()`;
- публикует `care_webapp` и `assets` как статические файлы;
- отдаёт `GET /health`;
- использует `catch-all`, чтобы фронтовые HTML-страницы открывались как SPA/static app.

### Telegram-бот

`bull_project/bull_bot/main.py`

Что делает:

- инициализирует БД;
- создаёт aiogram `Bot` и `Dispatcher`;
- подключает routers из `handlers/`;
- запускает polling.

## 5. Основные модули и ответственность

### `bull_bot/api/routes`

Слой HTTP/WebSocket API.

- `bookings.py`
  Создание бронирований, обновление, заявки на отмену/перенос.
- `passports.py`
  Загрузка и OCR-парсинг паспортов.
- `admin.py`
  Аналитика, менеджеры, выборки броней, экспорт паспортов.
- `admin_requests.py`
  Подтверждение и обработка cancel/reschedule заявок.
- `packages.py`
  Поиск пакетов по дате.
- `rooms.py`
  Поиск свободных комнат через данные Google Sheets.
- `websockets.py`
  Каналы `/ws/phones` и `/ws/admin-requests`.
- `open_date.py`
  OPEN DATE бронирования без конкретной даты.

### `bull_bot/database`

- `models.py`
  SQLAlchemy-модели.
- `requests.py`
  Почти весь CRUD и прикладные выборки.
- `setup.py`
  Engine/session/init_db.

Особенность проекта: здесь нет отдельной системы миграций Alembic. `init_db()` и часть helper-функций делают мягкие `ALTER TABLE` при старте. Это удобно для быстрых изменений, но для серьёзных schema changes требует аккуратности.

### `bull_bot/core/google_sheets`

Интеграция с Google Sheets:

- `client.py`
  Авторизация и доступ к spreadsheet/worksheet.
- `allocator.py`
  Поиск слотов, комнат, заголовков и пакетных диапазонов.
- `writer.py`
  Запись и обновление бронирований в таблицах.
- `table_parser.py`, `four_u_logic.py`
  Специализированная логика разбора таблиц.

Это критичный слой бизнеса: значительная часть логики размещения и записи живёт именно здесь, а не в БД.

### `bull_bot/core/parsers`

- `passport_parser.py`
  OCR и извлечение данных из паспорта.
- `pdf_generator.py`
  Генерация PDF/документов.
- `people_parser.py`, `package_parser.py`
  Разбор входных данных и пакетной информации.

### `bull_bot/handlers`

Telegram-обработчики по сценариям:

- `booking_handlers.py`
- `reschedule_handlers.py`
- `history_handlers.py`
- `care_handlers.py`
- `admin_handlers.py`
- `admin_applications.py`
- `admin_reports.py`
- `admin_4u.py`

Если поведение ломается только в Telegram, начинать поиск почти всегда стоит отсюда.

## 6. Модель данных

Ключевые сущности из `bull_bot/database/models.py`:

- `User`
  Telegram-пользователь с ролью `manager`, `admin`, `care`.
- `Booking`
  Основная бронь. Содержит менеджера, пакет, размещение, паспортные данные, телефон, статус, путь к файлу паспорта, `group_members`.
- `ApprovalRequest`
  Заявка на `cancel` или `reschedule`.
- `AdminRequestInbox`
  Привязка заявок к админам.
- `OpenDateBooking`
  Бронь без конкретной даты, с последующим ожиданием выбора даты.
- `AdminSettings`
  Настройки уведомлений админа.
- `Request4U`
  Отдельный сценарий заявок `4U`.

## 7. Поток бронирования

Упрощённый happy path:

1. Менеджер вводит данные в Telegram или веб-форме.
2. Если нужен паспорт, файл уходит в `passports.py`.
3. OCR сохраняет файл в `bull_bot/tmp/uploads` и пытается извлечь поля.
4. `bookings.py` валидирует payload и пишет бронь в БД через `database.requests`.
5. `google_sheets.writer.save_group_booking()` записывает группу в Google Sheets.
6. После успешной записи обновляется `sheet_row_number`.
7. WebSocket и/или Telegram-уведомления рассылают событие администраторам.

Отмена/перенос идут через `ApprovalRequest`: сначала создаётся заявка, потом админский API подтверждает её и синхронизирует изменения в Sheets и БД.

## 8. Конфигурация и окружение

Основные переменные находятся в `bull_project/bull_bot/config/constants.py` и подхватываются из `.env`.

Критичные переменные:

- `API_TOKEN`
  Telegram bot token.
- `DATABASE_URL`
  SQLite локально или PostgreSQL в Docker/production.
- `MOCK_MODE`
  Если `true`, Google Sheets отключается.
- `USE_TEST_TABLE`
  Ограничивает работу тестовой таблицей.
- `TEST_SPREADSHEET_ID`
  ID тестовой Google Sheets таблицы.
- `GOOGLE_CREDS_JSON`
  JSON сервисного аккаунта в env.
- `SKIP_BOT`
  Позволяет не поднимать Telegram-часть.
- `POPPLER_PATH`
  Нужен для `pdf2image`.
- `API_BASE_URL`
  Базовый URL API для внешних вызовов.

Google credentials берутся так:

1. из `GOOGLE_CREDS_JSON`, если переменная задана;
2. иначе из `bull_project/bull_bot/credentials/service_account.json`.

## 9. Где что менять

Если задача связана с конкретным сценарием:

- новая HTTP-ручка: `bull_bot/api/routes/`
- изменение Telegram-флоу: `bull_bot/handlers/`
- изменение структуры брони/статусов: `bull_bot/database/models.py` и `database/requests.py`
- изменение записи в Google Sheets: `bull_bot/core/google_sheets/`
- изменение OCR/паспортов: `bull_bot/core/parsers/` и `api/routes/passports.py`
- realtime/UI события: `bull_bot/core/websocket_manager.py`
- статика care/admin интерфейсов: `care_webapp/`, `admin_webapp/`, `bull_bot/webapp/`

## 10. Риски и технический долг

Новые разработчики должны знать это сразу:

- бизнес-логика заметно распределена между API, Telegram handlers, `database.requests` и Google Sheets writer;
- миграции делаются вручную и частично на старте приложения, полноценного migration framework нет;
- в коде много `print`/debug-логирования, а не централизованного structured logging;
- часть UI хранится как статические HTML/JS страницы, а не как отдельный современный frontend app;
- успешность ключевых бизнес-операций зависит от внешнего состояния Google Sheets.

## 11. Рекомендуемый порядок изучения проекта

Для нового разработчика лучший маршрут такой:

1. Прочитать `docker-compose.yml` и понять сервисы.
2. Прочитать `main.py` и `core/api_server.py`.
3. Прочитать `database/models.py` и `database/requests.py`.
4. Прочитать `api/routes/bookings.py` и `api/routes/passports.py`.
5. Прочитать `core/google_sheets/writer.py` и `allocator.py`.
6. Только после этого идти в Telegram handlers и статические webapp-файлы.

## 12. Полезные команды

Пересборка:

```bash
cd bull_project
docker compose up -d --build
```

Логи API:

```bash
cd bull_project
docker compose logs -f api
```

Логи бота:

```bash
cd bull_project
docker compose logs -f worker
```

Проверка контейнеров:

```bash
cd bull_project
docker compose ps
```

## 13. Что стоит улучшить дальше

Если проект будет активно развиваться, разумные следующие шаги:

- вынести конфиг в единый typed settings слой;
- внедрить Alembic для миграций;
- отделить бизнес-логику от route handlers;
- добавить тесты на booking flow и Google Sheets integration layer;
- вынести admin/care UI в отдельный фронтенд-пакет с нормальной сборкой;
- убрать секреты из репозитория и хранить их только в env/secret manager.
