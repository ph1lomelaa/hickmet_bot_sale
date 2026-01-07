import random
import colorsys
import re
from bull_project.bull_bot.core.google_sheets.client import (
    get_google_client,
    get_worksheet_by_title,
)
from bull_project.bull_bot.core.google_sheets.allocator import (
    check_has_train_column,
    find_package_row,
    find_headers_extended,
    get_room_size,
)

def row_col_to_a1(row, col):
    div = col
    string = ""
    while div > 0:
        module = (div - 1) % 26
        string = chr(65 + module) + string
        div = int((div - module) / 26)
    return string + str(row)

async def process_inf_passengers(ws, all_values, all_pilgrims, regular_pilgrims, saved_rows, cols, common_data, group_color):
    """
    Обрабатывает INF паломников - вставляет для них строки под родителями.

    🔥 НОВАЯ ЛОГИКА: Все INF записываются ПОСЛЕ обычных паломников,
    даже если INF идет первым в списке - он будет записан последним и возьмет тип комнаты от первого обычного.

    Args:
        ws: Worksheet объект
        all_values: Все значения таблицы
        all_pilgrims: ВСЕ паломники в исходном порядке (включая INF)
        regular_pilgrims: Только обычные паломники (не-INF)
        saved_rows: Строки где записаны обычные паломники
        cols: Карта колонок
        common_data: Общие данные брони
        group_color: Цвет группы

    Returns:
        list: Финальный список строк для ВСЕХ паломников (включая INF)
    """
    print(f"\n🍼 Обработка INF паломников...")

    # Проверяем есть ли INF паломники
    inf_count = sum(1 for p in all_pilgrims if p.get('is_infant', False))
    if inf_count == 0:
        print(f"   ℹ️ INF паломников нет, возвращаем исходные строки")
        return saved_rows

    print(f"   Найдено INF паломников: {inf_count}")

    # 🔥 НОВЫЙ ПОДХОД: Создаем карту индекс в all_pilgrims -> строка в таблице (только для обычных)
    pilgrim_idx_to_row = {}
    regular_idx = 0

    for i, pilgrim in enumerate(all_pilgrims):
        is_inf = pilgrim.get('is_infant', False)
        if not is_inf:
            pilgrim_idx_to_row[i] = saved_rows[regular_idx]
            regular_idx += 1

    print(f"   Карта обычных паломников: {pilgrim_idx_to_row}")

    # Результирующий список строк для ВСЕХ паломников
    final_rows = [None] * len(all_pilgrims)

    # Заполняем строки для обычных паломников
    for idx, row in pilgrim_idx_to_row.items():
        final_rows[idx] = row
        print(f"   ✅ Обычный паломник #{idx+1}: строка {row}")

    # 🔥 Обрабатываем INF паломников - ПОСЛЕ всех обычных
    # Сортируем по индексу чтобы обрабатывать в порядке от конца к началу
    # (чтобы вставки не сдвигали еще необработанных)
    inf_indices = [(i, p) for i, p in enumerate(all_pilgrims) if p.get('is_infant', False)]

    # Обрабатываем INF в обратном порядке (от конца к началу)
    for i, pilgrim in reversed(inf_indices):
        print(f"\n   🍼 INF паломник #{i+1} (из {len(all_pilgrims)}):")

        # Ищем ближайшего обычного паломника ПЕРЕД этим INF
        parent_idx = None
        for j in range(i - 1, -1, -1):
            if not all_pilgrims[j].get('is_infant', False):
                parent_idx = j
                break

        # Если не нашли обычного паломника перед INF, берем первого обычного паломника
        if parent_idx is None:
            print(f"      INF идет первым, используем первого обычного паломника")
            # Находим первого обычного паломника
            for j in range(len(all_pilgrims)):
                if not all_pilgrims[j].get('is_infant', False):
                    parent_idx = j
                    break

        if parent_idx is None:
            print(f"      ⚠️ Нет обычных паломников вообще - пропускаем INF")
            continue

        parent_row = pilgrim_idx_to_row[parent_idx]
        print(f"      Родитель: паломник #{parent_idx+1}, строка {parent_row}")

        def _get_cell_value(row_idx: int, col_zero_based: int) -> str:
            if row_idx <= 0:
                return ""
            if row_idx - 1 >= len(all_values):
                return ""
            row = all_values[row_idx - 1]
            if col_zero_based >= len(row):
                return ""
            return str(row[col_zero_based] or "").strip()

        def _col_letter(col_1_based: int) -> str:
            # row_col_to_a1(1, col) => "D1"
            return re.sub(r"\d+", "", row_col_to_a1(1, col_1_based))

        try:
            # Вставляем новую строку после parent_row
            new_row_idx = parent_row + 1

            # КРИТИЧНО: Вставляем пустую строку
            ws.insert_row(values=[""] * 50, index=new_row_idx)
            print(f"      ✅ Вставлена пустая строка {new_row_idx}")

            # Подготавливаем данные для INF паломника
            infant_data = {**common_data, **pilgrim}
            infant_data['meal_type'] = 'INF'  # 🔥 Тип питания = INF
            # На всякий случай: менеджер должен быть одинаковым для всех строк группы (включая INF)
            infant_data['manager_name_text'] = common_data.get('manager_name_text', infant_data.get('manager_name_text', ''))

            # Записываем данные младенца
            updates_infant = []
            price_tasks_infant = []
            _prepare_updates(updates_infant, price_tasks_infant, new_row_idx, cols, infant_data)

            # 🔥 Записываем "INF" в колонку "№"
            if 'num' in cols:
                num_col_a1 = row_col_to_a1(new_row_idx, cols['num'] + 1)
                updates_infant.append({'range': num_col_a1, 'values': [['INF']]})
                print(f"      ✅ Записали 'INF' в колонку №: {num_col_a1}")

            # Применяем обновления
            if updates_infant:
                ws.batch_update(updates_infant)
                print(f"      ✅ Данные младенца записаны")

            # 🔥 ОБЪЕДИНЯЕМ ячейку типа комнаты по вертикали с родителем
            if 'room' in cols:
                room_col_idx = cols['room'] + 1
                col_letter = _col_letter(room_col_idx)

                # Частый кейс: тип комнаты уже был объединён на несколько строк (QUAD/TRPL/DBL),
                # и вставленная строка не попадает в существующий merge. Тогда нужно расширить merge:
                # unmerge старого диапазона -> merge с +1 строкой.
                room_col_zero = cols['room']
                start_row = parent_row
                while start_row > 1 and _get_cell_value(start_row, room_col_zero) == "":
                    start_row -= 1

                room_value = _get_cell_value(start_row, room_col_zero)
                room_size = get_room_size(room_value) if room_value else 1
                end_row = start_row + max(1, room_size) - 1
                if parent_row > end_row:
                    end_row = parent_row

                new_end_row = max(end_row + 1, new_row_idx)
                old_range = f"{col_letter}{start_row}:{col_letter}{end_row}"
                new_range = f"{col_letter}{start_row}:{col_letter}{new_end_row}"

                try:
                    ws.unmerge_cells(old_range)
                except Exception:
                    pass

                try:
                    ws.merge_cells(new_range, merge_type='MERGE_ALL')
                    print(f"      ✅ Объединены ячейки типа комнаты: {new_range}")
                except Exception as e:
                    print(f"      ⚠️ Не удалось объединить ячейки: {e}")

            # Окрашиваем имя/фамилию младенца тем же цветом что и группа
            for key in ("last_name", "first_name"):
                if key in cols:
                    a1 = row_col_to_a1(new_row_idx, cols[key] + 1)
                    try:
                        ws.format(a1, {"backgroundColor": group_color, "textFormat": {"bold": False}})
                    except: pass

            # Сохраняем строку младенца в карте и в final_rows
            final_rows[i] = new_row_idx
            print(f"      ✅ INF паломник #{i+1} записан в строку {new_row_idx}")

            # 🔥 ВАЖНО: После вставки строки все последующие строки сдвигаются вниз!
            # Обновляем карту pilgrim_idx_to_row для всех паломников после вставленной строки
            for idx, row in pilgrim_idx_to_row.items():
                if row >= new_row_idx:
                    pilgrim_idx_to_row[idx] = row + 1
                    if final_rows[idx] is not None:
                        final_rows[idx] = row + 1

        except Exception as e:
            print(f"      ❌ Ошибка вставки строки для INF: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\n📊 Финальные строки для всех паломников: {final_rows}")
    return final_rows

async def save_group_booking(group_data: list, common_data: dict, placement_mode: str, specific_row=None, is_share=False):
    from bull_project.bull_bot.core.google_sheets.allocator import find_best_slot_for_group

    client = get_google_client()
    if not client:
        print("❌ Google client не инициализирован (get_google_client вернул None)")
        return []

    sheet_id = common_data.get('table_id')
    sheet_name = common_data.get('sheet_name')
    target_pkg = common_data['package_name']
    target_room = common_data['room_type']

    try:
        ss = client.open_by_key(sheet_id)
        ws = get_worksheet_by_title(ss, sheet_name)
        all_values = ws.get_all_values()

        saved_rows = []
        updates = []
        cols = None
        merge_tasks = []
        color_tasks = []
        price_tasks = []

        # 🔥 НОВАЯ ЛОГИКА: Разделяем паломников на обычных и INF
        regular_pilgrims = []  # Не-INF паломники (для размещения)
        all_pilgrims = []  # ВСЕ паломники в исходном порядке

        print(f"\n🔍 DEBUG: Проверка INF/CHD флагов для каждого паломника:")
        for idx, person in enumerate(group_data):
            is_inf = person.get('is_infant', False)
            is_chd = person.get('is_child', False)
            name = f"{person.get('Last Name', 'N/A')} {person.get('First Name', 'N/A')}"
            print(f"   Паломник {idx+1}: {name}")
            print(f"      is_infant: {is_inf} (тип: {type(is_inf)})")
            print(f"      is_child: {is_chd} (тип: {type(is_chd)})")
            all_pilgrims.append(person)
            if not is_inf:
                regular_pilgrims.append(person)

        print(f"\n📊 Обработка группы:")
        print(f"   Всего паломников: {len(all_pilgrims)}")
        print(f"   Обычных (для размещения): {len(regular_pilgrims)}")
        print(f"   INF (младенцев): {len(all_pilgrims) - len(regular_pilgrims)}")

        # Пастельный цвет для всей группы (один цвет на всех)
        seed_base = "".join([
            common_data.get("package_name", ""),
            common_data.get("room_type", ""),
            str(len(regular_pilgrims))  # 🔥 Используем количество обычных паломников
        ])
        rnd = random.Random(seed_base)
        h = rnd.random()
        s = 0.35
        v = 0.95
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        group_color = {"red": r, "green": g, "blue": b}

        # 🔥 ИСПРАВЛЕНИЕ: Используем групповое размещение для ОБЫЧНЫХ паломников (не-INF)
        if not specific_row and len(regular_pilgrims) > 0:
            # Используем функцию группового размещения только для обычных паломников
            saved_rows = find_best_slot_for_group(
                all_values,
                target_pkg,
                regular_pilgrims,  # 🔥 Передаем только не-INF паломников
                target_room,
                placement_mode
            )

            if not saved_rows or len(saved_rows) != len(regular_pilgrims):
                print(f"❌ Групповое размещение вернуло неполный список строк")
                print(f"   Ожидалось: {len(regular_pilgrims)}, получено: {len(saved_rows)}")
                return []

            # Получаем колонки для записи данных
            pkg_row = find_package_row(all_values, target_pkg)
            if pkg_row is not None:
                for r in range(pkg_row, min(pkg_row + 15, len(all_values))):
                    cols = find_headers_extended(all_values[r])
                    if cols: break

            if not cols:
                print(f"❌ Не найдены заголовки для пакета {target_pkg}")
                return []

            # Записываем данные для каждого ОБЫЧНОГО паломника
            for i, (person_passport, row_idx) in enumerate(zip(regular_pilgrims, saved_rows)):
                full_data = {**common_data, **person_passport}
                _prepare_updates(updates, price_tasks, row_idx, cols, full_data)
                # Планируем окраску имени/фамилии для группы (если в группе > 1 человека, включая INF)
                if len(all_pilgrims) > 1:
                    for key in ("last_name", "first_name"):
                        if key in cols:
                            a1 = row_col_to_a1(row_idx, cols[key] + 1)
                            color_tasks.append(a1)

        elif specific_row:
            # Старая логика для specific_row (ручное размещение)
            pkg_row = find_package_row(all_values, target_pkg)
            if pkg_row is not None:
                for r in range(pkg_row, min(pkg_row + 15, len(all_values))):
                    cols = find_headers_extended(all_values[r])
                    if cols: break
            if not cols: return []

            for i, person_passport in enumerate(group_data):
                row_idx = specific_row + i
                saved_rows.append(row_idx)
                full_data = {**common_data, **person_passport}
                _prepare_updates(updates, price_tasks, row_idx, cols, full_data)
                # Планируем окраску имени/фамилии для группы (если в группе > 1 человека, включая INF)
                if len(group_data) > 1:
                    for key in ("last_name", "first_name"):
                        if key in cols:
                            a1 = row_col_to_a1(row_idx, cols[key] + 1)
                            color_tasks.append(a1)
        else:
            print(f"❌ Пустой список паломников")
            return []

        if updates: ws.batch_update(updates)
        # Применяем окраску имен/фамилий (один цвет на группу)
        for a1 in color_tasks:
            try:
                ws.format(a1, {"backgroundColor": group_color, "textFormat": {"bold": False}})
            except Exception as e:
                print(f"⚠️ Не удалось окрасить {a1}: {e}")
        # Форматируем цену и оплату
        for row_idx, col_idx in price_tasks:
            a1 = row_col_to_a1(row_idx, col_idx)
            try:
                ws.format(a1, {"numberFormat": {"type": "CURRENCY", "pattern": "[$$]#,##0"}})
            except Exception as e:
                print(f"⚠️ Не удалось применить формат цены для {a1}: {e}")
        if merge_tasks:
            for m_range in merge_tasks:
                try: ws.merge_cells(m_range, merge_type='MERGE_ALL')
                except: pass

        # 🔥 ОБРАБОТКА INF ПАЛОМНИКОВ - вставка строк под родителями
        final_rows = await process_inf_passengers(
            ws, all_values, all_pilgrims, regular_pilgrims, saved_rows,
            cols, common_data, group_color
        )

        return final_rows

    except Exception as e:
        print(f"❌ Save error: {e}")
        import traceback
        traceback.print_exc()
        return []

def do_transform(ws, updates, merge_tasks, all_values, start_idx, r_col, col_letter, rows_count, values, merges):
    range_str = f"{col_letter}{start_idx}:{col_letter}{start_idx + rows_count - 1}"
    try: ws.unmerge_cells(range_str)
    except: pass

    updates.append({'range': range_str, 'values': values})

    for m_start, m_end in merges:
        merge_tasks.append(f"{col_letter}{start_idx + m_start}:{col_letter}{start_idx + m_end}")

    # Обновляем память бота (Тип комнаты)
    for k in range(rows_count):
        if start_idx - 1 + k < len(all_values):
            all_values[start_idx - 1 + k][r_col] = values[k][0]

def _prepare_updates(updates_list, price_tasks, row_idx, cols, data):
    # Используем правильные ключи, которые приходят из паспортных данных

    # 🔥 ЛОГИКА CHD: Если паломник помечен как CHD, меняем тип питания на "CHD"
    meal_type = data.get('meal_type', '')
    is_child = data.get('is_child', False)
    if is_child:
        meal_type = 'CHD'
        print(f"   🧒 CHD: meal_type установлен в 'CHD' для строки {row_idx}")

    mapping = {
        'last_name': data.get('Last Name', '') or data.get('guest_last_name', ''),
        'first_name': data.get('First Name', '') or data.get('guest_first_name', ''),
        'gender': data.get('Gender', '') or data.get('gender', ''),
        'dob': data.get('Date of Birth', '') or data.get('date_of_birth', ''),
        'doc_num': data.get('Document Number', '') or data.get('passport_num', ''),
        'doc_exp': data.get('Document Expiration', '') or data.get('passport_expiry', ''),
        'iin': data.get('IIN', '') or data.get('guest_iin', ''),
        'visa': data.get('visa_status', ''),
        'avia': data.get('avia', ''),
        'meal': meal_type,  # 🔥 Используем meal_type с учетом CHD
        'price': data.get('price', ''),
        'amount_paid': data.get('amount_paid', ''),
        'exchange_rate': data.get('exchange_rate', ''),
        'discount': data.get('discount', ''),
        'manager': data.get('manager_name_text', ''),
        'comment': data.get('comment', ''),
        'client_phone': data.get('client_phone', ''),
        'train': data.get('train', ''),
        'region': data.get('region', ''),
        'source': data.get('source', '')
    }

    # Отладка для train - проверяем есть ли колонка в таблице
    if "train" in mapping and "train" not in cols:
        print(f"⚠️ TRAIN: Колонка 'train' НЕ найдена в таблице! Доступные колонки: {list(cols.keys())}")
    elif "train" in mapping and "train" in cols:
        print(f"✅ TRAIN: Колонка 'train' найдена в таблице (индекс {cols['train']}), значение = '{mapping.get('train')}'")

    for col_key, value in mapping.items():
        if col_key in cols:
            val_str = str(value).strip()
            if not val_str or val_str in ["-", "skip", "None"]:
                # Отладка для train
                if col_key == "train":
                    print(f"⚠️ TRAIN пропущен: значение = '{val_str}'")
                continue
            # Отладка для train
            if col_key == "train":
                print(f"✅ TRAIN будет записан: значение = '{val_str}'")
            # Цена и оплата — записываем как число и отмечаем для форматирования
            if col_key in ("price", "amount_paid"):
                clean = val_str.replace("$", "").replace(" ", "").replace(",", "")
                try:
                    num_val = float(clean)
                    price_tasks.append((row_idx, cols[col_key] + 1))
                    updates_list.append({'range': f"{row_col_to_a1(row_idx, cols[col_key] + 1)}", 'values': [[num_val]]})
                except:
                    updates_list.append({'range': f"{row_col_to_a1(row_idx, cols[col_key] + 1)}", 'values': [[val_str]]})
            else:
                updates_list.append({'range': f"{row_col_to_a1(row_idx, cols[col_key] + 1)}", 'values': [[val_str]]})

async def save_booking_smart(booking_data):
    passport_data = {
        'Last Name': booking_data.get('last_name'), 'First Name': booking_data.get('first_name'),
        'Gender': booking_data.get('gender'), 'Date of Birth': booking_data.get('dob'),
        'Document Number': booking_data.get('passport_num'), 'Document Expiration': booking_data.get('passport_exp')
    }
    rows = await save_group_booking([passport_data], booking_data, 'separate')
    return rows[0] if rows else False

async def check_train_exists(sheet_id, sheet_name, package_name):
    client = get_google_client()
    if not client: return False
    try:
        ss = client.open_by_key(sheet_id); ws = get_worksheet_by_title(ss, sheet_name); all_values = ws.get_all_values()
        return check_has_train_column(all_values, package_name)
    except: return False

async def clear_booking_in_sheets(sheet_id, sheet_name, row_number, package_name):
    client = get_google_client()
    if not client or not row_number: return False
    try:
        ss = client.open_by_key(sheet_id); ws = get_worksheet_by_title(ss, sheet_name); all_values = ws.get_all_values()
        pkg_row = find_package_row(all_values, package_name); cols = None
        if pkg_row is not None:
            for r in range(pkg_row, min(pkg_row + 30, len(all_values))):
                cols = find_headers_extended(all_values[r])
                if cols: break
        if not cols: return False
        fields_to_clear = ['last_name', 'first_name', 'gender', 'dob', 'doc_num', 'doc_exp', 'price', 'comment', 'manager', 'train', 'client_phone']
        updates = []
        for key in fields_to_clear:
            if key in cols: updates.append({'range': f"{row_col_to_a1(row_number, cols[key] + 1)}", 'values': [['']]})
        if updates: ws.batch_update(updates); return True
        return False
    except: return False

def find_last_content_row(all_values):
    """Находит последнюю строку с содержимым на листе"""
    for r in range(len(all_values) - 1, -1, -1):
        row_text = "".join([str(c).strip() for c in all_values[r]])
        if len(row_text) > 2:  # Есть какой-то контент
            return r + 1  # +1 потому что индексы с 0
    return len(all_values)

async def write_cancelled_booking_red(sheet_id, sheet_name, package_name, guest_name):
    from bull_project.bull_bot.core.google_sheets.allocator import get_package_block
    client = get_google_client()
    if not client:
        print("❌ Google client не инициализирован")
        return False

    try:
        ss = client.open_by_key(sheet_id)
        ws = get_worksheet_by_title(ss, sheet_name)
        all_values = ws.get_all_values()

        # Находим блок пакета (нужно для получения колонки)
        _, _, cols = get_package_block(all_values, package_name)
        if not cols:
            print(f"❌ Не найден блок пакета {package_name}")
            return False

        # 🔥 НАХОДИМ ПОСЛЕДНЮЮ СТРОКУ НА ВСЕМ ЛИСТЕ
        last_row = find_last_content_row(all_values)
        # Отступаем 15 строк от конца ВСЕГО листа
        cancelled_row = last_row + 15

        print(f"📝 Записываем отмену в строку {cancelled_row} (последняя строка листа: {last_row})")

        # Находим колонку для записи имени
        name_col = cols.get('last_name')
        if not name_col:
            print("❌ Не найдена колонка для имени")
            return False

        # Записываем имя
        cell_range = row_col_to_a1(cancelled_row, name_col + 1)
        ws.update(cell_range, [[f"❌ ОТМЕНЕНО: {guest_name}"]])

        # Форматируем красным цветом
        ws.format(cell_range, {
            "backgroundColor": {
                "red": 1.0,
                "green": 0.8,
                "blue": 0.8
            },
            "textFormat": {
                "foregroundColor": {
                    "red": 0.8,
                    "green": 0.0,
                    "blue": 0.0
                },
                "fontSize": 11,
                "bold": True
            }
        })

        print(f"✅ Отмена записана красным в строку {cancelled_row}")
        return True

    except Exception as e:
        print(f"❌ Ошибка записи отмены: {e}")
        import traceback
        traceback.print_exc()
        return False

async def write_rescheduled_booking_red(sheet_id, sheet_name, package_name, guest_name):
    """Записывает перенос красным цветом внизу блока пакета"""
    from bull_project.bull_bot.core.google_sheets.allocator import get_package_block
    client = get_google_client()
    if not client:
        print("❌ Google client не инициализирован")
        return False

    try:
        ss = client.open_by_key(sheet_id)
        ws = get_worksheet_by_title(ss, sheet_name)
        all_values = ws.get_all_values()

        # Находим блок пакета (нужно для получения колонки)
        _, _, cols = get_package_block(all_values, package_name)
        if not cols:
            print(f"❌ Не найден блок пакета {package_name}")
            return False

        # 🔥 НАХОДИМ ПОСЛЕДНЮЮ СТРОКУ НА ВСЕМ ЛИСТЕ
        last_row = find_last_content_row(all_values)
        # Отступаем 15 строк от конца ВСЕГО листа
        rescheduled_row = last_row + 15

        print(f"📝 Записываем перенос в строку {rescheduled_row} (последняя строка листа: {last_row})")

        # Находим колонку для записи имени
        name_col = cols.get('last_name')
        if not name_col:
            print("❌ Не найдена колонка для имени")
            return False

        # Записываем имя
        cell_range = row_col_to_a1(rescheduled_row, name_col + 1)
        ws.update(cell_range, [[f"♻️ ПЕРЕНОС: {guest_name}"]])

        # Форматируем красным цветом (как отмена)
        ws.format(cell_range, {
            "backgroundColor": {
                "red": 1.0,
                "green": 0.8,
                "blue": 0.8
            },
            "textFormat": {
                "foregroundColor": {
                    "red": 0.8,
                    "green": 0.0,
                    "blue": 0.0
                },
                "fontSize": 11,
                "bold": True
            }
        })

        print(f"✅ Перенос записан красным в строку {rescheduled_row}")
        return True

    except Exception as e:
        print(f"❌ Ошибка записи переноса: {e}")
        import traceback
        traceback.print_exc()
        return False
