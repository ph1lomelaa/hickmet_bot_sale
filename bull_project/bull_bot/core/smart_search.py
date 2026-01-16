import time
import asyncio
from datetime import datetime
from typing import Dict, List, Tuple

from bull_project.bull_bot.core.google_sheets.client import (
    get_accessible_tables, get_sheet_names, get_packages_from_sheet
)

SHEETS_CACHE: Dict[str, Tuple[float, List[str]]] = {}
SHEETS_TTL = 60 * 30  
DATE_CACHE: Dict[str, Tuple[float, List[dict]]] = {}
DATE_TTL = 60  

def _norm_ddmm(s: str) -> str:
    s = (s or "").strip().replace("/", ".").replace(",", ".")
    parts = s.split(".")
    if len(parts) < 2:
        return s
    dd = parts[0].zfill(2)[:2]
    mm = parts[1].zfill(2)[:2]
    return f"{dd}.{mm}"

async def _get_target_tables_current_next_year() -> Dict[str, str]:
    now = datetime.now()
    years = [str(now.year), str(now.year + 1)]
    all_tables = get_accessible_tables()

    target = {}
    for t_name, t_id in all_tables.items():
        if any(y in t_name for y in years):
            target[t_name] = t_id

    return target

async def _get_sheet_names_cached(table_id: str, force: bool = False) -> List[str]:
    ts, cached = SHEETS_CACHE.get(table_id, (0, []))
    if (not force) and cached and (time.time() - ts < SHEETS_TTL):
        return cached

    names = get_sheet_names(table_id)
    SHEETS_CACHE[table_id] = (time.time(), names or [])
    # маленькая пауза против 429
    await asyncio.sleep(0.3)
    return names or []

async def get_packages_by_date(date_part: str, force: bool = False) -> dict:
    date_part = _norm_ddmm(date_part)
    ts, cached = DATE_CACHE.get(date_part, (0, []))
    if (not force) and cached and (time.time() - ts < DATE_TTL):
        return {"found": True, "data": cached}

    try:
        target_tables = await _get_target_tables_current_next_year()
        if not target_tables:
            return {"found": False, "error": "Нет таблиц текущего/следующего года"}

        print(f"🔍 [DEBUG] Поиск пакетов для даты: {date_part}")
        print(f"📚 [DEBUG] Найдено таблиц: {len(target_tables)} - {list(target_tables.keys())}")

        # Сначала собираем все пакеты БЕЗ суффиксов
        temp_collected: List[dict] = []

        for t_name, t_id in target_tables.items():
            try:
                sheet_names = await _get_sheet_names_cached(t_id, force=False)
                print(f"📋 [DEBUG] Таблица '{t_name}': {len(sheet_names)} листов")
                print(f"   Первые 10 листов: {sheet_names[:10]}")

                # выбираем только листы нужной даты
                # Поддерживаем варианты: "07.03", "7.03", "07.3"
                matched = []

                # Создаем варианты даты для поиска
                parts = date_part.split(".")
                if len(parts) == 2:
                    dd, mm = parts
                    # Варианты: "07.03", "7.03", "07.3", "7.3"
                    date_variants = [
                        f"{dd}.{mm}",           # 07.03
                        f"{int(dd)}.{mm}",      # 7.03
                        f"{dd}.{int(mm)}",      # 07.3
                        f"{int(dd)}.{int(mm)}"  # 7.3
                    ]
                else:
                    date_variants = [date_part]

                print(f"🔎 [DEBUG] Варианты даты для поиска: {date_variants}")

                for sheet_name in sheet_names:
                    clean = (sheet_name or "").strip()
                    # Проверяем все варианты даты
                    for variant in date_variants:
                        if clean.startswith(variant):
                            matched.append(sheet_name)
                            print(f"✅ [DEBUG] Найден лист: '{sheet_name}' (совпадает с '{variant}')")
                            break  # Нашли совпадение, переходим к следующему листу

                # если в этой таблице на дату нет листов — идём дальше
                if not matched:
                    print(f"⚠️ [DEBUG] Нет совпадений в таблице '{t_name}'")
                    continue

                # читаем пакеты только из совпавших листов
                for sheet_name in matched:
                    await asyncio.sleep(0.1)  # микро-пауза
                    packages_map = get_packages_from_sheet(t_id, sheet_name)

                    if not packages_map:
                        continue

                    for _, pkg_name in packages_map.items():
                        # Пока собираем без суффиксов - добавим их позже только если нужно
                        temp_collected.append({
                            "d": date_part,
                            "n": pkg_name,  # Оригинальное название без суффикса
                            "s": sheet_name,
                            "t": t_id,
                            "table_name": t_name  # Сохраняем название ТАБЛИЦЫ для суффикса
                        })

            except Exception as e:
                # не валим весь поиск из-за одной таблицы
                print(f"Ошибка чтения таблицы {t_name}: {e}")
                continue

        if not temp_collected:
            return {"found": False, "error": "Рейсы не найдены."}

        from collections import defaultdict
        date_occurrences = defaultdict(list)
        for item in temp_collected:
            pkg_name = item["n"]
            # Вытаскиваем дату из начала названия (до первого пробела или тире)
            date_prefix = pkg_name.split()[0] if pkg_name.split() else pkg_name
            key = (item["s"], item["t"])  # (sheet_name, table_id)
            date_occurrences[date_prefix].append((pkg_name, key))

        packages_with_duplicates = set()
        for date_prefix, items in date_occurrences.items():
            # Получаем уникальные комбинации (sheet_name, table_id) для этой даты
            unique_locations = set(key for _, key in items)
            if len(unique_locations) > 1:  # Дата встречается на разных листах
                # Добавляем ВСЕ пакеты с этой датой в список дубликатов
                for pkg_name, _ in items:
                    packages_with_duplicates.add(pkg_name)
                print(f"   📅 Дата '{date_prefix}' на {len(unique_locations)} разных листах")

        print(f"📦 [DEBUG] Найдено пакетов с дубликатами по дате: {len(packages_with_duplicates)}")

        collected: List[dict] = []
        for item in temp_collected:
            pkg_name = item["n"]
            table_name = item["table_name"]
            sheet_name = item["s"]

            if pkg_name in packages_with_duplicates:
                sheet_suffix = (sheet_name or "").replace(date_part, "").strip(" -.|")
                if not sheet_suffix:
                    sheet_suffix = sheet_name

                display_name = f"{pkg_name} [{table_name} / {sheet_suffix}]"
                print(f"   🔄 Дубликат по дате: '{pkg_name}' → '{display_name}'")
            else:
                # Уникальный пакет (дата встречается только на одном листе) - оставляем как есть
                display_name = pkg_name

            collected.append({
                "d": item["d"],
                "n": display_name,
                "s": item["s"],
                "t": item["t"]
            })

        DATE_CACHE[date_part] = (time.time(), collected)
        return {"found": True, "data": collected}

    except Exception as e:
        return {"found": False, "error": str(e)}
