import logging
from gspread.exceptions import WorksheetNotFound
from bull_project.bull_bot.config.settings import get_google_client

logger = logging.getLogger(__name__)

# Простой кэш для списка таблиц, чтобы не ждать 3 секунды при каждом клике
# Он сбросится при перезапуске бота
_tables_cache = None

def get_accessible_tables(use_cache=True) -> dict:

    global _tables_cache

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
    if use_cache and _tables_cache:
        return _tables_cache

    client = get_google_client()
    if not client:
        return {}

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
        logger.info(f"📊 Загружено {len(result)} production таблиц")
        return result
    except Exception as e:
        logger.error(f"❌ Ошибка получения списка таблиц: {e}")
        return {}

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

        # ОПТИМИЗАЦИЯ: Расширили до F чтобы захватить названия пакетов в разных колонках
        data = ws.get('A1:F200')

        packages = {}

        # СПОСОБ 1 (ПРИОРИТЕТ): Старая логика - поиск по ключевым словам
        package_keywords = [
            "niyet", "hikma", "izi", "4u", "premium", "econom",
            "стандарт", "эконом", "comfort",
            "ramadan", "рамадан", "ramazan", "ramad",
            "park", "regis", "ala", "jed"  # Добавили новые отели
        ]

        for idx, row in enumerate(data, start=1):
            if not row:
                continue

            text_full = " ".join([str(x) for x in row]).lower()

            if any(k in text_full for k in package_keywords):
                raw_name = row[0] if row and row[0] else (row[1] if len(row) > 1 else "Unknown")
                clean_name = str(raw_name).strip().replace("\n", " ")
                if len(clean_name) > 3:
                    packages[idx] = clean_name

        # СПОСОБ 2 (ФОЛЛБЭК): Если ничего не нашли - ищем по заголовкам
        if not packages:
            import re
            header_keywords = ["№", "avia", "visa", "type of room", "тип комнаты"]
            # Паттерн даты: dd.mm или d.mm или dd.m
            date_pattern = re.compile(r'^\d{1,2}\.\d{1,2}')

            for idx, row in enumerate(data, start=1):
                if not row:
                    continue

                text_full = " ".join([str(x) for x in row]).lower()

                # Если нашли строку с заголовками
                if any(k in text_full for k in header_keywords):
                    # Ищем название пакета выше (1-3 строки)
                    for offset in range(1, 4):
                        if idx - offset < 1:
                            break
                        prev_row = data[idx - offset - 1]
                        if prev_row and prev_row[0]:
                            raw_name = str(prev_row[0]).strip()
                            # Проверяем что название начинается с даты
                            if date_pattern.match(raw_name):
                                clean_name = raw_name.replace("\n", " ")
                                packages[idx] = clean_name
                                break

        return packages

    except Exception as e:
        logger.error(f"❌ Ошибка поиска пакетов: {e}")
        return {}

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
    """
    Пытается найти лист, игнорируя лишние пробелы/регистр.
    """
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
    """Публичная обертка для других модулей."""
    return _get_worksheet_by_title(spreadsheet, sheet_name)
