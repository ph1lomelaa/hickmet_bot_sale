# Выгрузка продаж Bull Project

Вверху страницы аналитики появилось меню ⋮ → «Выгрузить все данные»:
CSV и Excel (.xlsx). Даты, выбранные в аналитике, не ограничивают выгрузку.

Экспорт включает все поля `bookings` и `open_date_bookings`, все статусы,
всю историю, данные групп в JSON и ФИО/Telegram менеджера. Одна строка —
одна запись бронирования; данные группы не превращаются в повторные продажи.
CSV объединяет записи с колонкой «Тип записи», Excel содержит листы «Продажи»
и «OPEN DATE». Пустые таблицы сохраняют заголовки.

## Что обновить

1. В API: `bull_project/bull_bot/api/routes/admin.py`, новый файл
   `bull_project/bull_bot/api/routes/sales_export.py`, новый файл
   `bull_project/bull_bot/core/sales_export.py`, оба файла requirements.
   Новая зависимость: `openpyxl==3.1.5`.
2. На сайте админки: `admin-panel.html` и новый `sales-export.js`
   из `bull_project/admin_webapp/`. Сейчас ссылка бота ведёт на GitHub Pages
   `https://ph1lomelaa.github.io/book/admin-panel.html`; обновление Docker само
   по себе эту страницу не обновляет. Файлы нужно положить рядом с существующими
   `config.js` и `access.js`.

В действующем `book/config.js` указан API `https://hickmet.duckdns.org`.
Он обслуживается Bull на сервере `65.21.188.181`.
Корень репозитория на сервере: `/root/bull_project_repo`.
Папка Docker Compose: `/root/bull_project_repo/bull_project`.
Данные PostgreSQL находятся отдельно: `/data/postgres17`.

В открытой SSH-сессии сервера выполнить весь блок. Если `git pull` завершится
ошибкой из-за локальных изменений, блок остановится и сохранит их:

```bash
set -e
cd /root/bull_project_repo
git pull --ff-only origin main
cd bull_project
docker compose up -d --build --no-deps api
docker compose ps api
curl --fail --retry 20 --retry-delay 3 --retry-connrefused http://127.0.0.1:8000/health
```

Команда пересоздаёт только API; PostgreSQL и его данные не пересоздаются.
Если API не запустился, посмотреть причину:

```bash
docker compose logs --tail=100 api
```

В репозитории `ph1lomelaa/book` рабочая ветка называется `none`.
В её корне публикуются `admin-panel.html` и `sales-export.js`.
После их обновления нужно дождаться публикации GitHub Pages и заново
открыть админку из Telegram.

## Проверка

Открыть аналитику через Telegram под администратором, нажать ⋮ и скачать
оба формата. Сменить период аналитики и убедиться, что выгрузка по-прежнему
включает всю историю. Эндпоинт: `GET /api/admin/export?format=csv` или `xlsx`.
Доступ использует существующую проверку роли администратора и Telegram-подписи.

Локальные тесты (FastAPI, httpx, SQLAlchemy, aiosqlite, greenlet, openpyxl):

```bash
python -m unittest discover -s tests -p test_sales_export.py -v
```

Выгрузка читает текущую БД API аналитики. Она не восстанавливает удалённую
историю, не объединяет другие базы и не импортирует Google Sheets.
Если в этой БД 65 броней, в листе «Продажи» будет 65 записей.
CSV использует UTF-8 с BOM и разделитель `;`; потенциальные формулы защищены
апострофом. В Excel телефоны и ИИН сохраняются текстом, с ведущими нулями.

Файлы паспорта не включаются в выгрузку: сохраняются их пути из записей БД.
