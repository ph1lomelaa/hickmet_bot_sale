import logging
import re
import time
from gspread.exceptions import WorksheetNotFound
from bull_project.bull_bot.config.settings import get_google_client

logger = logging.getLogger(__name__)

# Кэш списка таблиц, чтобы не ждать 3 секунды при каждом клике.
# Живёт TABLES_TTL секунд — новые таблицы подхватываются без перезапуска.
_tables_cache = None
_tables_cache_ts = 0.0
TABLES_TTL = 60 * 5

def get_accessible_tables(use_cache=True) -> dict:

    global _tables_cache, _tables_cache_ts

    # Импортируем константы
    from bull_project.bull_bot.config.constants import (
        USE_TEST_TABLE, TEST_SPREADSHEET_ID, TEST_SPREADSHEET_NAME
    )

    # 🧪 ТЕСТОВЫЙ РЕЖИМ: возвращаем только TEST таблицу
    if USE_TEST_TABLE:
        if not TEST_SPREADSHEET_ID:
            logger.error("❌ USE_TEST_TABLE=true, но TEST_SPREADSHEET_ID пуст!")
            return {}

        # Кэшируем тестовую таблицу
        if use_cache and _tables_cache:
            return _tables_cache

        result = {TEST_SPREADSHEET_NAME: TEST_SPREADSHEET_ID}
        _tables_cache = result
        logger.info(f"🧪 Используется тестовая таблица: {TEST_SPREADSHEET_NAME}")
        return result

    # 📊 PRODUCTION РЕЖИМ: возвращаем все таблицы
    if use_cache and _tables_cache and (time.time() - _tables_cache_ts < TABLES_TTL):
        return _tables_cache

    client = get_google_client()
    if not client:
        return _tables_cache or {}

    try:
        # Это тяжелый запрос, он занимает 1-3 секунды
        spreadsheets = client.openall()

        result = {}
        for ss in spreadsheets:
            # Можно добавить фильтр по названию, чтобы убрать мусор
            # if "2025" in ss.title:
            result[ss.title] = ss.id

        # Сохраняем в память
        _tables_cache = result
        _tables_cache_ts = time.time()
        logger.info(f"📊 Загружено {len(result)} production таблиц")
        return result
    except Exception as e:
        logger.error(f"❌ Ошибка получения списка таблиц: {e}")
        # Не теряем старый список из-за временной ошибки Google API
        return _tables_cache or {}

def get_sheet_names(spreadsheet_id: str) -> list:
    """
    Получает список листов (вкладок) по ID таблицы.
    Это быстрый запрос, он НЕ скачивает содержимое ячеек.
    """
    client = get_google_client()
    if not client: return []

    try:
        ss = client.open_by_key(spreadsheet_id)
        # worksheets() загружает только свойства листов (Title, ID), это быстро
        return [ws.title for ws in ss.worksheets()]
    except Exception as e:
        logger.error(f"❌ Ошибка получения листов: {e}")
        return []

def get_packages_from_sheet(spreadsheet_id: str, sheet_name: str) -> dict:
    """
    Скачивает содержимое (пакеты) ТОЛЬКО когда пользователь выбрал лист.
    Оптимизация: скачиваем только колонки A и B (диапазон A1:B200).
    """
    client = get_google_client()
    if not client: return {}

    try:
        ss = client.open_by_key(spreadsheet_id)
        ws = _get_worksheet_by_title(ss, sheet_name)
        data = ws.get('A1:J400')
        packages = extract_packages_from_rows(data)
        logger.info(f"📦 Пакеты листа '{sheet_name}': {list(packages.values())}")
        return packages

    except Exception as e:
        logger.error(f"❌ Ошибка поиска пакетов ({sheet_name}): {e}")
        return {}


# ===== Распознавание пакетов в листе =====
# Блок пакета в листе выглядит так:
#   06.01-13.01 ADDRESS        <- название (начинается с диапазона дат)
#   Manager:                   <- служебные строки
#   Guide NIYET:
#   № | TRAIN | ... | Type of room | Meal | Last Name | First Name | ...   <- шапка
#   1 | ... данные ...
# Название ищем ВЫШЕ шапки, а не по ключевым словам в любой строке:
# иначе «Guide NIYET:» (содержит niyet) принимается за пакет.

_PKG_DATE_START_RE = re.compile(
    r'^\s*\d{1,2}[./]\d{1,2}(?:[./]\d{2,4})?\s*[-–—]\s*\d{1,2}[./]\d{1,2}'
)
_PKG_DATE_ONLY_RE = re.compile(
    r'^\s*\d{1,2}[./]\d{1,2}(?:[./]\d{2,4})?(\s*[-–—]\s*\d{1,2}[./]\d{1,2}(?:[./]\d{2,4})?)?\s*$'
)
_PKG_LABEL_RE = re.compile(
    r'^\s*(manager|менеджер|guide|гид|№|итого|total|comment|коммент|примечан)',
    re.I,
)
_PKG_ROOM_HEADERS = ("type of room", "тип комнаты", "тип номера")
_PKG_NAME_HEADERS = ("last name", "lastname", "фамилия")
_PKG_FALLBACK_KEYWORDS = (
    "niyet", "hikma", "izi", "4u", "premium", "econom",
    "стандарт", "эконом", "акцион", "comfort",
    "ramadan", "рамадан", "ramazan",
    "itikaf", "7d", "10d", "millenium", "millennium",
)
_PKG_TITLE_LOOKUP = 6  # сколько строк выше шапки ищем название


def _cell(row, i) -> str:
    if not row or i >= len(row) or row[i] is None:
        return ""
    return str(row[i]).replace("\n", " ").replace("\r", " ").strip()


def _first_cell(row) -> str:
    for i in range(len(row or [])):
        val = _cell(row, i)
        if val:
            return val
    return ""


def _is_table_header(row) -> bool:
    cells = [_cell(row, i).lower() for i in range(len(row or []))]
    has_room = any(any(k in c for k in _PKG_ROOM_HEADERS) for c in cells)
    has_name = any(any(k in c for k in _PKG_NAME_HEADERS) for c in cells)
    return has_room and has_name


def _package_title_from_row(row) -> str:
    """Название из строки-заголовка; '' если строка не похожа на название пакета."""
    title = _first_cell(row)
    if not title or _PKG_LABEL_RE.match(title) or not _PKG_DATE_START_RE.match(title):
        return ""
    # «06.01-13.01» в A, а тип («ADDRESS») — в следующей ячейке
    if _PKG_DATE_ONLY_RE.match(title):
        start = next(i for i in range(len(row)) if _cell(row, i)) + 1
        for i in range(start, len(row)):
            extra = _cell(row, i)
            if extra and not _PKG_DATE_ONLY_RE.match(extra) and not _PKG_LABEL_RE.match(extra):
                title = f"{title} {extra}"
                break
    return re.sub(r"\s+", " ", title).strip()


def extract_packages_from_rows(rows) -> dict:
    """
    Возвращает {номер_строки (1-based): название пакета}.
    1) По структуре: шапка таблицы → ближайшая строка выше, начинающаяся с дат.
    2) Фолбэк (если шапок нет): ячейка A с датой и ключевым словом пакета.
    """
    rows = rows or []
    packages = {}

    header_idxs = [i for i, row in enumerate(rows) if _is_table_header(row)]
    prev_header = -1
    for h in header_idxs:
        lower = max(prev_header + 1, h - _PKG_TITLE_LOOKUP)
        for r in range(h - 1, lower - 1, -1):
            title = _package_title_from_row(rows[r])
            if title:
                packages[r + 1] = title
                break
        prev_header = h

    if not packages:
        for i, row in enumerate(rows):
            title = _package_title_from_row(row)
            if title and any(k in title.lower() for k in _PKG_FALLBACK_KEYWORDS):
                packages[i + 1] = title

    names = list(packages.values())
    dups = {n for n in names if names.count(n) > 1}
    if dups:
        logger.warning(f"⚠️ Одинаковые названия пакетов в листе: {sorted(dups)}")

    return packages

def get_sheet_data(sheet_id: str, sheet_name: str):
    """
    Полное скачивание (используется только при записи/Тетрисе).
    Здесь уже придется подождать, но это происходит в фоне.
    """
    client = get_google_client()
    if not client: return []
    try:
        ss = client.open_by_key(sheet_id)
        ws = _get_worksheet_by_title(ss, sheet_name)
        return ws.get_all_values()
    except Exception as e:
        logger.error(f"❌ Ошибка скачивания данных: {e}")
        return []

def _get_worksheet_by_title(spreadsheet, sheet_name: str):
    normalized = (sheet_name or "").strip()
    if not normalized:
        raise WorksheetNotFound("Sheet name is empty")

    try:
        return spreadsheet.worksheet(normalized)
    except WorksheetNotFound:
        normalized_lower = normalized.lower()
        for ws in spreadsheet.worksheets():
            if ws.title.strip().lower() == normalized_lower:
                return ws
        raise

def get_worksheet_by_title(spreadsheet, sheet_name: str):
    return _get_worksheet_by_title(spreadsheet, sheet_name)
