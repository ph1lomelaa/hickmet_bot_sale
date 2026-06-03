import re
from bull_project.bull_bot.core.parsers.people_parser import _norm_room_kind

def normalize(text):
    return str(text).replace("\n", " ").replace("\r", " ").strip().lower()


_PACKAGE_DATE_RANGE_RE = re.compile(r"\b(\d{1,2}[./]\d{1,2})\s*[-–—]\s*(\d{1,2}[./]\d{1,2})\b")
_PACKAGE_FAMILY_PATTERNS = {
    "niyet": (r"\bniyet\b", r"\bниет\b"),
    "hikma": (r"\bhikma\b", r"\bхикма\b"),
    "izi": (r"\bizi\b",),
    "4u": (r"\b4u\b", r"\b4\s*u\b", r"\b4\s*you\b"),
    "amal": (r"\bamal\b", r"\bамал\b"),
    "aroya": (r"\baroya\b", r"\bароя\b"),
    "aa": (r"\baa\b",),
}
_PACKAGE_VARIANT_PATTERNS = {
    "econom": (r"\beconomy\b", r"\beconom\b", r"\bэконом\b"),
    "comfort": (r"\bcomfort\b", r"\bкомфорт\b"),
    "premium": (r"\bpremium\b", r"\bпремиум\b"),
    "7d": (r"\b7\s*d\b", r"\b7\s*days\b", r"/\s*7\s*d\b"),
    "10d": (r"\b10\s*d\b", r"\b10\s*days\b", r"/\s*10\s*d\b"),
}
_PACKAGE_TEXT_REPLACEMENTS = (
    (re.compile(r"\b4\s*you\b", re.I), "4u"),
    (re.compile(r"\b4\s*u\b", re.I), "4u"),
    (re.compile(r"\b7\s*days\b", re.I), "7d"),
    (re.compile(r"\b10\s*days\b", re.I), "10d"),
    (re.compile(r"/\s*7\s*d\b", re.I), " 7d"),
    (re.compile(r"/\s*10\s*d\b", re.I), " 10d"),
    (re.compile(r"\beconomy\b", re.I), "econom"),
    (re.compile(r"\bэконом\b", re.I), "econom"),
)


def _normalize_package_text(text):
    return re.sub(r"[\s\u00A0\u202F]+", " ", str(text).replace("\n", " ").replace("\r", " ")).strip().lower()


def _normalize_package_date(value):
    raw = str(value or "").strip().replace("/", ".")
    parts = raw.split(".")
    if len(parts) != 2:
        return raw
    day, month = parts
    if not (day.isdigit() and month.isdigit()):
        return raw
    return f"{int(day):02d}.{int(month):02d}"


def _extract_package_signature(text):
    normalized = _normalize_package_text(text)
    match = _PACKAGE_DATE_RANGE_RE.search(normalized)

    date_range = None
    tail = normalized
    if match:
        date_range = f"{_normalize_package_date(match.group(1))}-{_normalize_package_date(match.group(2))}"
        tail = f"{normalized[:match.start()]} {normalized[match.end():]}"

    tail = re.sub(r"[\[\](){},;|]+", " ", tail)
    for pattern, replacement in _PACKAGE_TEXT_REPLACEMENTS:
        tail = pattern.sub(replacement, tail)
    tail = _normalize_package_text(tail)

    family = None
    for family_name, patterns in _PACKAGE_FAMILY_PATTERNS.items():
        if any(re.search(pattern, tail, re.I) for pattern in patterns):
            family = family_name
            break

    variants = {
        variant_name
        for variant_name, patterns in _PACKAGE_VARIANT_PATTERNS.items()
        if any(re.search(pattern, tail, re.I) for pattern in patterns)
    }

    return {
        "raw": normalized,
        "date": date_range,
        "tail": tail,
        "family": family,
        "variants": variants,
    }


def _package_signatures_match(candidate, target):
    if target["date"] and candidate["date"] and candidate["date"] != target["date"]:
        return False
    if target["family"] and candidate["family"] and candidate["family"] != target["family"]:
        return False
    if candidate["variants"] != target["variants"]:
        return False
    if target["tail"]:
        return candidate["tail"] == target["tail"]
    return False


def _package_signatures_compatible(candidate, target):
    if target["date"] and candidate["date"] and candidate["date"] != target["date"]:
        return False
    if target["family"] and candidate["family"] and candidate["family"] != target["family"]:
        return False
    if candidate["variants"] != target["variants"]:
        return False
    if target["tail"]:
        return target["tail"] in candidate["tail"]
    return False

# === КАРТА ЗАГОЛОВКОВ ===
HEADER_MAP = {
    "last_name": ["last name", "lastname", "фамилия", "names"],
    "first_name": ["first name", "firstname", "имя"],
    "gender": ["gender", "sex", "пол"],
    "room": ["type of room", "room", "тип номера", "комната"],
    "meal": ["meal", "meal a day", "питание"],
    "dob": ["date of birth", "dob", "дата рождения", "д.р."],
    "doc_num": ["document number", "passport", "номер паспорта", "passport number", "doc num"],
    "doc_exp": ["document expiration", "expiration", "expiry", "срок действия", "годен до", "valid until"],
    "iin": ["iin", "ИИН", "иин"],
    "visa": ["visa", "виза"],
    "avia": ["avia", "авиа", "рейс", "flight"],
    "price": ["price", "цена", "стоимость"],
    "comment": ["comment", "комментарий", "примечание", "сomment"],
    "manager": ["manager", "менеджер"],
    "train": ["train", "поезд", "жд"],
    "client_phone": ["contact", "phone", "телефон", "номер", "контакты"],
    "source": ["source", "источник"],
    "amount_paid": ["paid", "оплачено", "внесено"],
    "region": ["region", "регион"],
    "num": ["№", "num", "number", "n", "#"],  # Колонка для номера
}

ROOM_FALLBACKS = {
    "quad": ["quad", "dbl"],
    "trpl": ["trpl", "quad", "dbl"],
    "dbl": ["dbl", "quad", "trpl"],
    "sgl": ["sgl", "dbl", "trpl"],
    "quin": ["quin", "quad", "dbl"],
}

def normalize_room_value(value):
    """Нормализует тип комнаты, приходящий от пользователя."""
    print(f"\n🔧 normalize_room_value вызвана с: '{value}'")
    if not value:
        print(f"   ❌ Значение пустое, возвращаем ''")
        return ""
    normalized = _norm_room_kind(str(value), None)
    print(f"   📊 _norm_room_kind вернула: '{normalized}'")
    if normalized:
        print(f"   ✅ Возвращаем normalized: '{normalized}'")
        return normalized
    fallback = normalize(value)
    print(f"   ⚠️ normalized пустой, возвращаем fallback: '{fallback}'")
    return fallback

def find_package_row(all_rows, target_pkg_name):
    """Поиск строки с названием пакета"""
    target = normalize(target_pkg_name)
    target_signature = _extract_package_signature(target_pkg_name)
    print(f"🔍 Ищем пакет: '{target}'")
    print(
        "   Сигнатура пакета:",
        f"date={target_signature['date']!r}, family={target_signature['family']!r},",
        f"variants={sorted(target_signature['variants'])}, tail={target_signature['tail']!r}"
    )

    # 🔥 ОТЛАДКА: Показываем первые 30 строк с датами
    print(f"📋 Первые строки таблицы (отладка):")
    for i, row in enumerate(all_rows[:30]):
        row_text = normalize(" ".join(row[:10]))  # Смотрим первые 10 колонок
        # Показываем строки которые начинаются с цифр (возможные пакеты)
        if row_text and len(row_text) > 3 and row_text[0].isdigit():
            print(f"  Строка {i+1}: {row_text[:120]}")

    # 1. Сначала ищем точное совпадение нормализованного названия пакета.
    for i, row in enumerate(all_rows):
        row_text = _normalize_package_text(" ".join(row[:10]))
        row_signature = _extract_package_signature(row_text)
        if _package_signatures_match(row_signature, target_signature):
            print(f"✅ Найден пакет по точной сигнатуре в строке {i+1}: {row_text[:100]}")
            return i

    # 2. Fallback: совместимое совпадение по тексту без конфликта по типу пакета.
    for i, row in enumerate(all_rows):
        row_text = _normalize_package_text(" ".join(row[:10]))
        row_signature = _extract_package_signature(row_text)
        if target in row_text and _package_signatures_compatible(row_signature, target_signature):
            print(f"✅ Найден пакет по совместимому совпадению в строке {i+1}: {row_text[:100]}")
            return i

    # 3. Последний fallback: по ключевому слову, но всё ещё без конфликта по сигнатуре.
    parts = target.split()
    if len(parts) > 1:
        keyword = parts[-1]
        for i, row in enumerate(all_rows):
            row_text = _normalize_package_text(" ".join(row[:10]))  # 🔥 Расширили поиск
            row_signature = _extract_package_signature(row_text)
            if (
                keyword in row_text
                and any(c.isdigit() for c in row_text)
                and _package_signatures_compatible(row_signature, target_signature)
            ):
                print(f"✅ Найден пакет (по ключевому слову) в строке {i+1}: {row_text[:80]}")
                return i

    print(f"❌ Пакет '{target}' не найден!")
    print(f"   Искали: '{target}'")
    return None

def find_headers_extended(row):
    """Поиск заголовков таблицы"""
    cols = {}
    row_clean = [normalize(c) for c in row]

    # Проверяем наличие хотя бы одного из ключевых заголовков
    has_name_col = any(kw in " ".join(row_clean) for kw in ["last name", "фамилия", "names", "name"])

    if not has_name_col:
        return None

    for col_idx, val in enumerate(row_clean):
        if not val:
            continue
        for key, keywords in HEADER_MAP.items():
            if key not in cols and any(k == val or k in val for k in keywords):
                cols[key] = col_idx

    # Должна быть колонка "room" и хотя бы одна из: last_name/first_name/gender
    if "room" in cols and any(key in cols for key in ("last_name", "first_name", "gender")):
        print(f"✅ Заголовки найдены: {list(cols.keys())}")
        return cols

    return None


def _is_probable_room_data_row(row) -> bool:
    """
    Фолбэк: некоторые таблицы/пакеты содержат данные без строки заголовков.
    Тогда пытаемся распознать "первую строку комнаты" по паттерну:
    [№] [тип комнаты] [питание] [Фамилия] [Имя] [M/F] ...
    """
    if not row or len(row) < 6:
        return False
    c0 = normalize(row[0])
    c1 = normalize(row[1])
    c2 = normalize(row[2])
    c5 = normalize(row[5])

    if not c0 or not c0[0].isdigit():
        return False

    room_kw = ("quad", "quadro", "double", "dbl", "triple", "trpl", "single", "sgl", "1", "2", "3", "4")
    if not any(k in c1 for k in room_kw):
        return False

    meal_kw = ("hb", "bb", "fb", "ro", "inf", "chd")
    if c2 and not any(k == c2 or k in c2 for k in meal_kw):
        return False

    if c5 not in ("m", "f"):
        return False

    return True


def _fallback_cols_for_room_table(row) -> dict:
    """
    Дефолтная раскладка колонок, когда заголовков нет (частый кейс в Google Sheets).
    """
    # [0]=№, [1]=room, [2]=meal, [3]=last, [4]=first, [5]=gender, [6]=dob, [7]=doc_num, [8]=doc_exp, [9]=iin
    cols = {
        "num": 0,
        "room": 1,
        "meal": 2,
        "last_name": 3,
        "first_name": 4,
        "gender": 5,
        "dob": 6,
        "doc_num": 7,
        "doc_exp": 8,
        "iin": 9,
    }
    # если строка короче — безопасно оставим только то, что точно есть
    max_idx = len(row) - 1
    return {k: v for k, v in cols.items() if v <= max_idx}

def get_package_block(all_rows, pkg_name):
    """Получение границ блока пакета"""
    start_row = find_package_row(all_rows, pkg_name)
    if start_row is None:
        print(f"❌ Пакет '{pkg_name}' не найден в таблице")
        return None, None, None

    header_row = None
    cols = None

    # Ищем заголовки в пределах 15 строк после названия пакета
    for r in range(start_row, min(start_row + 15, len(all_rows))):
        cols = find_headers_extended(all_rows[r])
        if cols:
            header_row = r
            print(f"✅ Заголовки найдены в строке {r+1}")
            break

    if header_row is None:
        # Фолбэк: если заголовков нет — пробуем определить колонки по первой строке данных
        for r in range(start_row + 1, min(start_row + 40, len(all_rows))):
            if _is_probable_room_data_row(all_rows[r]):
                header_row = r - 1  # чтобы данные начинались с header_row+1
                cols = _fallback_cols_for_room_table(all_rows[r])
                print(f"✅ Заголовки не найдены — использую фолбэк по данным (первая строка: {r+1})")
                break

    if header_row is None or not cols:
        print(f"❌ Заголовки не найдены для пакета '{pkg_name}'")
        return None, None, None

    # Определяем конец блока
    end_row = len(all_rows)
    empty_streak = 0

    for r in range(header_row + 1, len(all_rows)):
        row_text = "".join([str(c).strip() for c in all_rows[r]])
        if len(row_text) < 2:
            empty_streak += 1
            if empty_streak >= 3:
                end_row = r - empty_streak + 1
                break
        else:
            empty_streak = 0
            norm_text = normalize(row_text)
            # Новый пакет начинается если строка НАЧИНАЕТСЯ с паттерна DD.MM-DD.MM
            # (например "13.07-20.07 izi/7d"). Данные строки начинаются с цифры + буква,
            # поэтому _PACKAGE_DATE_RANGE_RE.match ложно не срабатывает на них.
            if _PACKAGE_DATE_RANGE_RE.match(norm_text):
                end_row = r
                break

    print(f"📦 Блок пакета: строки {header_row+1} - {end_row}")
    return header_row, end_row, cols

def check_has_train_column(all_rows, pkg_name):
    _, _, cols = get_package_block(all_rows, pkg_name)
    return cols and 'train' in cols

def get_room_size(room_text):
    """Определение размера комнаты"""
    t = normalize(room_text)
    if 'quad' in t or '4' in t: return 4
    if 'trip' in t or 'trpl' in t or '3' in t: return 3
    if 'doub' in t or 'dbl' in t or '2' in t: return 2
    if 'sing' in t or 'sgl' in t or '1' in t: return 1
    return 1

def is_row_occupied(row, col_last, col_first=None):
    """Проверка занятости строки"""
    l_name = row[col_last] if col_last < len(row) else ""
    f_name = row[col_first] if col_first and col_first < len(row) else ""
    return len(normalize(l_name)) > 0 or len(normalize(f_name)) > 0

def check_rows_are_empty(all_rows, start_idx, count, col_last, col_first=None):
    """Проверка, что N строк подряд пустые"""
    for i in range(count):
        r_idx = start_idx + i
        if r_idx >= len(all_rows):
            return False
        if is_row_occupied(all_rows[r_idx], col_last, col_first):
            return False
    return True

def find_share_slot_for_type(all_rows, header_row, end_row, cols, room_type, target_gender, require_existing=False):
    """Поиск свободного места в комнатах указанного типа"""
    col_room = cols.get("room")
    col_last = cols.get("last_name")
    col_first = cols.get("first_name")
    col_gender = cols.get("gender")

    if col_room is None or col_last is None:
        return None

    target_gen = normalize(target_gender).upper()

    for i in range(header_row + 1, end_row):
        row = all_rows[i]
        raw_room = normalize(row[col_room]) if col_room < len(row) else ""
        if not raw_room:
            continue

        current_room = _norm_room_kind(raw_room, None)
        if current_room != room_type:
            continue

        room_size = get_room_size(raw_room)
        first_free_idx = None
        room_gender = None
        has_guests = False
        compatible = True

        for k in range(room_size):
            curr_idx = i + k
            if curr_idx >= len(all_rows):
                break

            c_row = all_rows[curr_idx]
            occupied = is_row_occupied(c_row, col_last, col_first)
            gen = c_row[col_gender] if col_gender and col_gender < len(c_row) else ""
            norm_gen = normalize(gen).upper() if gen else ""

            if occupied:
                has_guests = True
                if norm_gen and room_gender and room_gender != norm_gen:
                    compatible = False
                    break
                if norm_gen:
                    room_gender = norm_gen
                if norm_gen and norm_gen not in ['M', 'F']:
                    room_gender = norm_gen
                if norm_gen and target_gen in ['M', 'F'] and norm_gen != target_gen:
                    compatible = False
                    break
            else:
                if first_free_idx is None:
                    first_free_idx = curr_idx

        if not compatible or first_free_idx is None:
            continue
        if require_existing and not has_guests:
            continue

        return first_free_idx + 1

    return None

# ==================== 🔥 ГЛАВНЫЙ ПОИСК С ПОДДЕРЖКОЙ ГРУППОВОГО РАЗМЕЩЕНИЯ ====================

def find_best_slot_for_group(all_rows, target_pkg_name, group_data, target_room_type, placement_type="separate"):
    """
    Поиск места для группы паломников

    Args:
        all_rows: Все строки таблицы
        target_pkg_name: Название пакета
        group_data: Список словарей с данными паломников (должны содержать 'Gender')
        target_room_type: Тип комнаты
        placement_type: "family" (вместе) или "separate" (по полу)

    Returns:
        tuple: (rows: list[int], pending_transforms: list[dict])
            rows — список строк для каждого паломника
            pending_transforms — список {"start_row": int, "mode": str} для применения в writer
    """
    print(f"\n{'='*60}")
    print(f"🔍 ГРУППОВОЕ РАЗМЕЩЕНИЕ")
    print(f"   Пакет: {target_pkg_name}")
    print(f"   Количество: {len(group_data)}")
    print(f"   Тип комнаты: {target_room_type}")
    print(f"   Режим: {placement_type}")
    print(f"{'='*60}\n")

    header_row, end_row, cols = get_package_block(all_rows, target_pkg_name)
    if header_row is None:
        print("❌ Не удалось найти блок пакета")
        return [], []

    col_room = cols.get("room")
    col_last = cols.get("last_name")
    col_first = cols.get("first_name")
    col_gender = cols.get("gender")

    if col_room is None or col_last is None:
        print(f"❌ Отсутствуют необходимые колонки")
        return [], []

    target_room = normalize_room_value(target_room_type)
    group_size = len(group_data)
    fallback_types = ROOM_FALLBACKS.get(target_room, [target_room])

    # Разделяем группу по полу
    males = [p for p in group_data if normalize(p.get('Gender', '')).upper() == 'M']
    females = [p for p in group_data if normalize(p.get('Gender', '')).upper() == 'F']

    # Если есть паломники без пола — не размещаем, нужно спросить пользователя
    if len(males) + len(females) != len(group_data):
        print("❌ В группе есть паломники без указания пола. Требуется запросить пол перед размещением.")
        return [], []
    
    print(f"👥 Состав группы: {len(males)} мужчин, {len(females)} женщин")

    result_rows = []
    pending_transforms = []  # список {"start_row": int, "mode": str}

    if placement_type == "family":
        # РЕЖИМ "СЕМЬЯ" - размещаем всех вместе, не смотря на пол
        print("\n👪 Режим 'СЕМЬЯ' - ищем место для всей группы вместе")

        # Ищем свободную комнату нужного размера
        room_capacity = get_room_size(target_room)

        # СПЕЦИАЛЬНЫЙ СЛУЧАЙ: если 1 человек, пытаемся сначала подселить ТОЛЬКО в точный тип
        if group_size == 1:
            print("\n🔍 Один человек - пытаемся найти свободное место")
            person_gender = group_data[0].get('Gender', 'M') if group_data else 'M'
            gender_norm = normalize(person_gender).upper()

            # ШАГ 1: Ищем свободное место ТОЛЬКО в точном типе комнаты (quad)
            print(f"   Шаг 1: Поиск свободного места в комнатах типа {target_room}")
            share_slot = find_share_slot_for_type(
                all_rows, header_row, end_row, cols, target_room, gender_norm, require_existing=False
            )
            if share_slot:
                print(f"   ✅ Найдено место в комнате {target_room} в строке {share_slot}")
                result_rows.append(share_slot)
                idx = share_slot - 1
                if idx < len(all_rows):
                    all_rows[idx][col_last] = "RESERVED"
                    if col_gender:
                        all_rows[idx][col_gender] = gender_norm
                print(f"\n✅ Группа размещена! Строки: {result_rows}")
                return result_rows, pending_transforms

            # ШАГ 2: Ищем пустую комнату точного типа
            print(f"   Шаг 2: Поиск пустой комнаты типа {target_room}")
            empty_slot = find_empty_room_slot(all_rows, header_row, end_row, cols, target_room)
            if empty_slot:
                print(f"   ✅ Найдена пустая комната {target_room} в строке {empty_slot}")
                result_rows.append(empty_slot)
                idx = empty_slot - 1
                if idx < len(all_rows):
                    all_rows[idx][col_last] = "RESERVED"
                    if col_gender:
                        all_rows[idx][col_gender] = gender_norm
                print(f"\n✅ Группа размещена! Строки: {result_rows}")
                return result_rows, pending_transforms

            # ШАГ 3: НЕТ СВОБОДНЫХ QUAD - пробуем трансформацию или fallback
            print(f"   ❌ Нет свободных мест в комнатах типа {target_room}")
            print(f"   Шаг 3: Пробуем трансформацию или fallback типы")
            fallback_slot, _, mode = find_best_slot(all_rows, target_pkg_name, gender_norm, target_room_type)
            if fallback_slot and mode.startswith("trans_"):
                result_rows.append(fallback_slot)
                idx = fallback_slot - 1
                if idx < len(all_rows):
                    all_rows[idx][col_last] = "RESERVED"
                    if col_gender:
                        all_rows[idx][col_gender] = gender_norm
                pending_transforms.append({"start_row": fallback_slot, "mode": mode})
                print(f"   ✅ Трансформация {mode}: строка {fallback_slot}")
                print(f"\n✅ Группа размещена! Строки: {result_rows}")
                return result_rows, pending_transforms

            print("   ❌ Не удалось найти место даже через трансформацию")
            return [], []

        if group_size > room_capacity:
            print(f"⚠️ Группа ({group_size}) больше вместимости комнаты ({room_capacity})")
            needed_rooms = (group_size + room_capacity - 1) // room_capacity
            print(f"   Требуется комнат: {needed_rooms}")

            placed_count = 0
            for _ in range(needed_rooms):
                slot = find_empty_room_slot(all_rows, header_row, end_row, cols, target_room)
                if not slot:
                    # Нет пустой комнаты — пробуем трансформацию
                    first_gender = normalize(group_data[placed_count].get('Gender', 'M')).upper() if placed_count < len(group_data) else 'M'
                    fallback_slot, _, mode = find_best_slot(all_rows, target_pkg_name, first_gender, target_room_type)
                    if fallback_slot and mode.startswith("trans_"):
                        slot = fallback_slot
                        pending_transforms.append({"start_row": slot, "mode": mode})
                        print(f"   ✅ Трансформация {mode}: строка {slot}")
                    else:
                        print(f"❌ Не удалось найти свободную комнату (включая трансформации)")
                        return [], []

                people_in_this_room = min(room_capacity, group_size - placed_count)
                for j in range(people_in_this_room):
                    result_rows.append(slot + j)
                placed_count += people_in_this_room
                for j in range(people_in_this_room):
                    if (slot + j - 1) < len(all_rows):
                        all_rows[slot + j - 1][col_last] = "RESERVED"
        else:
            # Группа помещается в одну комнату
            slot = find_empty_room_slot(all_rows, header_row, end_row, cols, target_room)
            if not slot:
                # Нет пустого DBL/TRPL/etc — пробуем трансформацию (напр. QUAD → 2 DBL)
                print(f"   Нет пустых {target_room}, пробуем трансформацию...")
                first_gender = normalize(group_data[0].get('Gender', 'M')).upper() if group_data else 'M'
                fallback_slot, _, mode = find_best_slot(all_rows, target_pkg_name, first_gender, target_room_type)
                if fallback_slot and mode.startswith("trans_"):
                    slot = fallback_slot
                    pending_transforms.append({"start_row": slot, "mode": mode})
                    print(f"   ✅ Трансформация {mode}: строка {slot}")
                else:
                    print(f"❌ Нет свободных мест даже с трансформацией")
                    return [], []

            for j in range(group_size):
                result_rows.append(slot + j)
                if (slot + j - 1) < len(all_rows):
                    all_rows[slot + j - 1][col_last] = "RESERVED"

    else:
        # РЕЖИМ "РАЗДЕЛЬНО" - размещаем по полу
        print("\n🚻 Режим 'РАЗДЕЛЬНО' - размещаем мужчин и женщин отдельно")

        # 🔥 ИСПРАВЛЕНИЕ: Сохраняем индексы каждого человека в исходном списке
        male_indices = []
        female_indices = []

        for idx, person in enumerate(group_data):
            gender = normalize(person.get('Gender', 'M')).upper()
            if gender == 'M':
                male_indices.append(idx)
            else:
                female_indices.append(idx)

        # Размещаем мужчин
        male_rows = []
        if males:
            print(f"\n👨 Размещаем {len(males)} мужчин:")
            male_rows, male_transforms = place_gender_group(
                all_rows, header_row, end_row, cols, males, 'M', target_room, target_pkg_name
            )
            if not male_rows or len(male_rows) != len(males):
                print(f"❌ Не удалось разместить всех мужчин")
                return [], []
            pending_transforms.extend(male_transforms)

        # Размещаем женщин
        female_rows = []
        if females:
            print(f"\n👩 Размещаем {len(females)} женщин:")
            female_rows, female_transforms = place_gender_group(
                all_rows, header_row, end_row, cols, females, 'F', target_room, target_pkg_name
            )
            if not female_rows or len(female_rows) != len(females):
                print(f"❌ Не удалось разместить всех женщин")
                return [], []
            pending_transforms.extend(female_transforms)

        # 🔥 ИСПРАВЛЕНИЕ: Восстанавливаем правильный порядок строк
        # Создаем список нужного размера
        result_rows = [None] * len(group_data)

        # Размещаем мужчин на их исходные позиции
        for i, original_idx in enumerate(male_indices):
            result_rows[original_idx] = male_rows[i]

        # Размещаем женщин на их исходные позиции
        for i, original_idx in enumerate(female_indices):
            result_rows[original_idx] = female_rows[i]

        print(f"\n✅ Порядок восстановлен:")
        for idx, (person, row) in enumerate(zip(group_data, result_rows)):
            gender = person.get('Gender', 'M')
            print(f"   {idx+1}. Пол {gender} → строка {row}")

    print(f"\n✅ Группа размещена! Строки: {result_rows}")
    return result_rows, pending_transforms


def place_gender_group(all_rows, header_row, end_row, cols, people, gender, target_room, target_pkg_name=None):
    """
    Размещение группы одного пола.

    Returns:
        tuple: (result_rows: list[int], pending_transforms: list[dict])
    """
    col_room = cols.get("room")
    col_last = cols.get("last_name")
    col_first = cols.get("first_name")
    col_gender = cols.get("gender")

    result_rows = []
    pending_transforms = []
    people_placed = 0
    group_size = len(people)
    room_capacity = get_room_size(target_room)

    print(f"   Ищем места для {group_size} человек пола {gender}")

    # Если вся группа помещается в одну комнату — сначала ищем строго пустую комнату
    if group_size <= room_capacity:
        strict_empty_slot = find_empty_room_slot(
            all_rows, header_row, end_row, cols, target_room,
            required_gender=None, empty_only=True
        )
        if strict_empty_slot:
            for j in range(group_size):
                result_rows.append(strict_empty_slot + j)
                all_rows[strict_empty_slot + j - 1][col_last] = "RESERVED"
                if col_gender:
                    all_rows[strict_empty_slot + j - 1][col_gender] = gender
                people_placed += 1
                print(f"   ✅ Вся группа размещена в пустой комнате, строка {strict_empty_slot + j}")
            return result_rows, pending_transforms

        # Пустой комнаты точного типа нет — пробуем трансформацию
        if target_pkg_name:
            print(f"   Нет пустых {target_room} для пола {gender}, пробуем трансформацию...")
            fallback_slot, _, mode = find_best_slot(all_rows, target_pkg_name, gender, target_room)
            if fallback_slot and mode.startswith("trans_"):
                for j in range(group_size):
                    result_rows.append(fallback_slot + j)
                    idx = fallback_slot - 1 + j
                    if idx < len(all_rows):
                        all_rows[idx][col_last] = "RESERVED"
                        if col_gender:
                            all_rows[idx][col_gender] = gender
                pending_transforms.append({"start_row": fallback_slot, "mode": mode})
                print(f"   ✅ Трансформация {mode}: строка {fallback_slot}")
                return result_rows, pending_transforms

    # Сначала пытаемся подселить в существующие комнаты
    for i in range(header_row + 1, end_row):
        if people_placed >= group_size:
            break

        row = all_rows[i]
        raw_room = normalize(row[col_room]) if col_room < len(row) else ""

        if raw_room:
            prev_room_type = _norm_room_kind(raw_room, None)
            room_size = get_room_size(raw_room)

            if prev_room_type == target_room:
                room_gender = None
                free_slots = []

                for k in range(room_size):
                    curr_idx = i + k
                    if curr_idx >= len(all_rows):
                        break
                    c_row = all_rows[curr_idx]
                    occupied = is_row_occupied(c_row, col_last, col_first)
                    if occupied:
                        gen = c_row[col_gender] if col_gender and col_gender < len(c_row) else ""
                        if gen:
                            room_gender = normalize(gen).upper()
                    else:
                        free_slots.append(curr_idx)

                if free_slots and (room_gender is None or room_gender == gender):
                    for slot_idx in free_slots:
                        if people_placed >= group_size:
                            break
                        result_rows.append(slot_idx + 1)
                        all_rows[slot_idx][col_last] = "RESERVED"
                        if col_gender:
                            all_rows[slot_idx][col_gender] = gender
                        people_placed += 1
                        print(f"   ✅ Подселение в строку {slot_idx + 1}")

    # Если не все размещены, ищем пустые комнаты (с трансформацией при необходимости)
    while people_placed < group_size:
        slot = find_empty_room_slot(all_rows, header_row, end_row, cols, target_room, required_gender=gender)
        if not slot:
            # Нет пустых комнат — пробуем трансформацию (только trans_*, не share)
            if target_pkg_name:
                print(f"   Нет пустых {target_room} для пола {gender}, пробуем трансформацию...")
                fallback_slot, _, mode = find_best_slot(all_rows, target_pkg_name, gender, target_room)
                if fallback_slot and mode.startswith("trans_"):
                    slot = fallback_slot
                    pending_transforms.append({"start_row": slot, "mode": mode})
                    print(f"   ✅ Трансформация {mode}: строка {slot}")
                else:
                    print(f"   ❌ Нет свободных мест для пола {gender} (включая трансформации)")
                    return [], []
            else:
                print(f"   ❌ Не найдено свободных комнат для пола {gender}")
                return [], []

        room_size = get_room_size(target_room)
        people_in_room = min(room_size, group_size - people_placed)

        for j in range(people_in_room):
            result_rows.append(slot + j)
            all_rows[slot + j - 1][col_last] = "RESERVED"
            if col_gender:
                all_rows[slot + j - 1][col_gender] = gender
            people_placed += 1
            print(f"   ✅ Новая комната, строка {slot + j}")

    return result_rows, pending_transforms


def find_empty_room_slot(all_rows, header_row, end_row, cols, target_room, required_gender=None, empty_only=False):
    """Поиск пустой комнаты (или комнаты с людьми нужного пола).
    empty_only=True — возвращает только полностью пустые комнаты."""
    col_room = cols.get("room")
    col_last = cols.get("last_name")
    col_first = cols.get("first_name")
    col_gender = cols.get("gender")
    target_room_norm = normalize_room_value(target_room)
    room_capacity = get_room_size(target_room_norm)

    for i in range(header_row + 1, end_row):
        row = all_rows[i]
        raw_room = normalize(row[col_room]) if col_room < len(row) else ""

        if raw_room:
            prev_room_type = _norm_room_kind(raw_room, None)

            if prev_room_type == target_room_norm:
                # Проверяем все места в комнате
                room_genders = set()
                all_empty = True
                has_free_slots = False

                for k in range(room_capacity):
                    curr_idx = i + k
                    if curr_idx >= len(all_rows):
                        break

                    c_row = all_rows[curr_idx]
                    occupied = is_row_occupied(c_row, col_last, col_first)

                    if occupied:
                        all_empty = False
                        # Определяем пол
                        gen = c_row[col_gender] if col_gender and col_gender < len(c_row) else ""
                        if gen:
                            room_genders.add(normalize(gen).upper())
                    else:
                        has_free_slots = True

                # Комната подходит если:
                # 1. Полностью пустая (всегда)
                # 2. ИЛИ (empty_only=False) в комнате только люди нужного пола (если пол указан) И есть свободные места
                if all_empty:
                    print(f"   🏨 Найдена пустая комната в строке {i + 1}")
                    return i + 1
                elif not empty_only and required_gender and has_free_slots and len(room_genders) == 1 and required_gender in room_genders:
                    # В комнате уже есть люди того же пола И есть свободные места
                    print(f"   🏨 Найдена комната с людьми пола {required_gender} (есть свободные места) в строке {i + 1}")
                    return i + 1

    return None


def find_best_slot(all_rows, target_pkg_name, target_gender, target_room_type):
    """Поиск лучшего места для размещения ОДНОГО человека (обратная совместимость)"""
    print(f"\n{'='*60}")
    print(f"🔍 ПОИСК МЕСТА ДЛЯ РАЗМЕЩЕНИЯ")
    print(f"   Пакет: {target_pkg_name}")
    print(f"   Пол: {target_gender}")
    print(f"   Тип комнаты: {target_room_type}")
    print(f"{'='*60}\n")

    header_row, end_row, cols = get_package_block(all_rows, target_pkg_name)
    if header_row is None:
        print("❌ Не удалось найти блок пакета")
        return None, None, "error"

    col_room = cols.get("room")
    col_last = cols.get("last_name")
    col_first = cols.get("first_name")
    col_gender = cols.get("gender")

    if col_room is None or col_last is None:
        print(f"❌ Отсутствуют необходимые колонки: room={col_room}, last_name={col_last}")
        return None, None, "error"

    target_room = normalize_room_value(target_room_type)
    target_gen = normalize(target_gender).upper()
    if target_gen not in ['M', 'F']:
        target_gen = 'M'

    print(f"📊 Диапазон поиска: строки {header_row+1} - {end_row}")
    print(f"🎯 Ищем: {target_room} для пола {target_gen}\n")

    # 1. ПОИСК СВОБОДНОГО МЕСТА (ПОДСЕЛЕНИЕ)
    # Шаг 1: подселение ТОЛЬКО в точный тип комнаты.
    # Fallback-типы (QUAD вместо DBL и т.д.) идут в шаг 4 — ПОСЛЕ трансформации.
    print("🔍 ШАГ 1: Поиск свободного места в существующих комнатах (точный тип)...")
    share_slot = find_share_slot_for_type(
        all_rows, header_row, end_row, cols, target_room, target_gen, require_existing=False
    )
    if share_slot:
        print(f"✅ Найдено свободное место (подселение) в строке {share_slot}")
        return share_slot, cols, "share"

    print("   ❌ Свободных мест для подселения не найдено\n")

    # 2. ПОИСК ВАРИАНТОВ ТРАНСФОРМАЦИИ (как в старой логике)
    print("🔍 ШАГ 2: Поиск возможностей для трансформации...\n")

    # A. Нужен DOUBLE
    if target_room in ['dbl', 'double']:
        print("   Ищем трансформации для DOUBLE:")

        # 1 QUAD -> 2 DOUBLE
        for i in range(header_row + 1, end_row):
            raw = normalize(all_rows[i][col_room]) if col_room < len(all_rows[i]) else ""
            if 'quad' in raw or '4' in raw:
                if check_rows_are_empty(all_rows, i, 4, col_last, col_first):
                    print(f"   ✅ Найден пустой QUAD в строке {i+1} (1 QUAD -> 2 DOUBLE)")
                    return i + 1, cols, "trans_1quad_2dbl"

        # 2 TRIPLE -> 3 DOUBLE
        for i in range(header_row + 1, end_row - 3):
            raw1 = normalize(all_rows[i][col_room]) if col_room < len(all_rows[i]) else ""
            if 'trip' in raw1 or 'trpl' in raw1:
                if i + 3 < end_row:
                    raw2 = normalize(all_rows[i+3][col_room]) if col_room < len(all_rows[i+3]) else ""
                    if 'trip' in raw2 or 'trpl' in raw2:
                        if check_rows_are_empty(all_rows, i, 6, col_last, col_first):
                            print(f"   ✅ Найдены 2 пустых TRIPLE в строках {i+1} и {i+4} (2 TRIPLE -> 3 DOUBLE)")
                            return i + 1, cols, "trans_2trpl_3dbl"

    # B. Нужен TRIPLE
    elif target_room in ['trpl', 'triple']:
        print("   Ищем трансформации для TRIPLE:")

        # 2 QUAD -> 2 TRIPLE + 1 DOUBLE
        for i in range(header_row + 1, end_row - 4):
            raw1 = normalize(all_rows[i][col_room]) if col_room < len(all_rows[i]) else ""
            if 'quad' in raw1 or '4' in raw1:
                if i + 4 < end_row:
                    raw2 = normalize(all_rows[i+4][col_room]) if col_room < len(all_rows[i+4]) else ""
                    if 'quad' in raw2 or '4' in raw2:
                        if check_rows_are_empty(all_rows, i, 8, col_last, col_first):
                            print(f"   ✅ Найдены 2 пустых QUAD в строках {i+1} и {i+5} (2 QUAD -> 2 TRIPLE + DOUBLE)")
                            return i + 1, cols, "trans_2quad_mix"

        # 3 DOUBLE -> 2 TRIPLE
        for i in range(header_row + 1, end_row - 4):
            raw1 = normalize(all_rows[i][col_room]) if col_room < len(all_rows[i]) else ""
            if 'dbl' in raw1 or 'doub' in raw1:
                if i + 2 < end_row:
                    raw2 = normalize(all_rows[i+2][col_room]) if col_room < len(all_rows[i+2]) else ""
                    if 'dbl' in raw2 or 'doub' in raw2:
                        if i + 4 < end_row:
                            raw3 = normalize(all_rows[i+4][col_room]) if col_room < len(all_rows[i+4]) else ""
                            if 'dbl' in raw3 or 'doub' in raw3:
                                if check_rows_are_empty(all_rows, i, 6, col_last, col_first):
                                    print(f"   ✅ Найдены 3 пустых DOUBLE (3 DOUBLE -> 2 TRIPLE)")
                                    return i + 1, cols, "trans_3dbl_2trpl"

    # C. Нужен QUADRO
    elif target_room in ['quad', 'quadro']:
        print("   Ищем трансформации для QUADRO:")

        # 2 DOUBLE -> 1 QUAD
        for i in range(header_row + 1, end_row - 2):
            raw1 = normalize(all_rows[i][col_room]) if col_room < len(all_rows[i]) else ""
            if 'dbl' in raw1 or 'doub' in raw1:
                if i + 2 < end_row:
                    raw2 = normalize(all_rows[i+2][col_room]) if col_room < len(all_rows[i+2]) else ""
                    if 'dbl' in raw2 or 'doub' in raw2:
                        if check_rows_are_empty(all_rows, i, 4, col_last, col_first):
                            print(f"   ✅ Найдены 2 пустых DOUBLE (2 DOUBLE -> 1 QUAD)")
                            return i + 1, cols, "trans_2dbl_1quad"

    # D. Нужен SINGLE
    elif target_room in ['sing', 'single', 'sgl']:
        print("   Ищем трансформации для SINGLE:")

        # 1 DOUBLE -> 2 SINGLE
        for i in range(header_row + 1, end_row):
            raw = normalize(all_rows[i][col_room]) if col_room < len(all_rows[i]) else ""
            if 'dbl' in raw or 'doub' in raw:
                if check_rows_are_empty(all_rows, i, 2, col_last, col_first):
                    print(f"   ✅ Найден пустой DOUBLE (1 DOUBLE -> 2 SINGLE)")
                    return i + 1, cols, "trans_1dbl_2sgl"

        # 1 TRIPLE -> 1 DOUBLE + 1 SINGLE
        for i in range(header_row + 1, end_row):
            raw = normalize(all_rows[i][col_room]) if col_room < len(all_rows[i]) else ""
            if 'trip' in raw or 'trpl' in raw:
                if check_rows_are_empty(all_rows, i, 3, col_last, col_first):
                    print(f"   ✅ Найден пустой TRIPLE (1 TRIPLE -> 1 DOUBLE + 1 SINGLE)")
                    return i + 1, cols, "trans_1trpl_mix"

    # 3. ПОИСК ПУСТОЙ КОМНАТЫ
    print("🔍 ШАГ 3: Поиск пустой комнаты...")
    slot = find_empty_room_slot(all_rows, header_row, end_row, cols, target_room)
    if slot:
        print(f"✅ Найдена пустая комната в строке {slot}")
        return slot, cols, "new_room"

    # 4. ПОСЛЕДНИЙ РЕЗЕРВ: подселение в комнату другого типа (fallback).
    # Только если трансформация невозможна.
    print("🔍 ШАГ 4: Подселение в комнату другого типа (последний резерв)...")
    for fallback_code in ROOM_FALLBACKS.get(target_room, [])[1:]:  # пропускаем первый (это сам target_room)
        share_slot = find_share_slot_for_type(
            all_rows, header_row, end_row, cols, fallback_code, target_gen, require_existing=True
        )
        if share_slot:
            print(f"✅ Подселение в {fallback_code} в строке {share_slot} (fallback)")
            return share_slot, cols, "share_fallback"

    print("❌ Не найдено подходящих мест для размещения\n")
    return None, cols, "no_space"


def get_open_rooms_for_manual_selection(all_rows, pkg_name, needed_count=1, needed_type=None, target_gender=None):
    """Получение списка свободных мест для ручного выбора"""
    print(f"\n{'='*60}")
    print(f"🔍 GET_OPEN_ROOMS вызван:")
    print(f"   Пакет: '{pkg_name}'")
    print(f"   Нужно мест: {needed_count}")
    print(f"   Тип комнаты: '{needed_type}'")
    print(f"   Пол: '{target_gender}'")
    print(f"{'='*60}\n")

    header_row, end_row, cols = get_package_block(all_rows, pkg_name)
    if header_row is None:
        print(f"❌ Пакетный блок не найден!")
        return []

    print(f"✅ Блок найден: строки {header_row+1}-{end_row}")
    print(f"   Колонки: {list(cols.keys())}\n")

    col_room = cols.get("room")
    col_last = cols.get("last_name")
    col_first = cols.get("first_name")
    col_gender = cols.get("gender")

    if col_room is None or col_last is None:
        print(f"❌ Не хватает колонок: room={col_room}, last_name={col_last}")
        return []

    rooms_list = []
    target_type_norm = normalize_room_value(needed_type) if needed_type else None
    target_gender_norm = normalize(target_gender).upper() if target_gender else None
    accepted_types = None
    if target_type_norm:
        accepted_types = ROOM_FALLBACKS.get(target_type_norm, [target_type_norm])
    print(f"🎯 Ищем тип: '{target_type_norm}', допускаем: {accepted_types or 'все'}, пол: '{target_gender_norm}'\n")

    i = header_row + 1
    rooms_checked = 0

    while i < end_row and rooms_checked < 100:
        row = all_rows[i]
        raw_room = normalize(row[col_room]) if col_room < len(row) else ""

        if not raw_room:
            i += 1
            continue

        room_type = _norm_room_kind(raw_room, None)
        size = get_room_size(raw_room)
        rooms_checked += 1

        print(f"📍 Строка {i+1}: тип='{room_type}', размер={size}, raw='{raw_room}'")

        if accepted_types and room_type not in accepted_types:
            print(f"   ⏭️  Пропускаем (не подходит по типу)")
            i += size
            continue

        guests: list[str] = []
        genders = set()
        free_count = 0
        first_free_offset = -1

        for k in range(size):
            curr_idx = i + k
            if curr_idx >= end_row:
                break

            c_row = all_rows[curr_idx]
            occupied = is_row_occupied(c_row, col_last, col_first)
            name_val = c_row[col_last] if col_last < len(c_row) else ""
            gen = c_row[col_gender] if col_gender and col_gender < len(c_row) else ""

            if occupied:
                guest_name = name_val.split()[0] if name_val else "Турист"
                guests.append(guest_name)
                if gen:
                    genders.add(normalize(gen).upper())
            else:
                free_count += 1
                if first_free_offset == -1:
                    first_free_offset = k

        is_partially_occupied = len(guests) > 0
        is_completely_empty = (len(guests) == 0 and free_count > 0)
        print(f"   Результат: guests={len(guests)}, free={free_count}, partially_occupied={is_partially_occupied}, completely_empty={is_completely_empty}")

        # Добавляем комнату если есть достаточно свободных мест
        # Для полностью пустой комнаты first_free_offset будет 0 (первая строка комнаты)
        if free_count >= needed_count:
            room_gender = (
                list(genders)[0]
                if len(genders) == 1
                else ("MIX" if len(genders) > 1 else "Empty")
            )

            gender_ok = True
            if target_gender_norm in ['M', 'F']:
                if room_gender in ['M', 'F'] and room_gender != target_gender_norm:
                    gender_ok = False
                elif room_gender == "MIX":
                    gender_ok = False

            if not gender_ok:
                print("   ⏭️  Пропускаем (не подходит по полу)")
                i += size
                continue

            display_guests = ", ".join(guests) if guests else "Свободно"
            last_guest = guests[-1] if guests else "Свободно"
            room_label = f"{room_type.upper()} · {last_guest} (Свободно: {free_count})"

            # Для полностью пустой комнаты начинаем с первой строки (first_free_offset будет 0)
            # Для частично занятой - начинаем с первого свободного места
            actual_offset = 0 if is_completely_empty else first_free_offset

            room_info = {
                'row': i + 1 + actual_offset,
                'type': room_type.title(),
                'guests': display_guests,
                'free': free_count,
                'gender': room_gender if room_gender != "Empty" else (target_gender_norm or 'Empty'),
                'last_guest': last_guest,
                'label': room_label,
            }
            print(f"   ✅ ДОБАВЛЯЕМ комнату: {room_info}")
            rooms_list.append(room_info)

        i += size

    print(f"\n   ИТОГО найдено комнат: {len(rooms_list)}")
    return rooms_list
