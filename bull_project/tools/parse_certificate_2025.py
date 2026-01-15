#!/usr/bin/env python3
"""
Анализ листа Certificate 2025 - используется для OPEN DATE
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from bull_project.bull_bot.config.settings import get_google_client


def main():
    SPREADSHEET_ID = "1KA7IHRs4uI4thWX8O7zm2W5VHLQ01jfkqY59C4FaKSs"
    TARGET_SHEET = "Сertificate 2025"  # С кириллической 'С'

    print("=" * 80)
    print("📊 АНАЛИЗ ЛИСТА: Certificate 2025")
    print("=" * 80 + "\n")

    client = get_google_client()
    if not client:
        print("❌ Не удалось подключиться к Google Sheets")
        return

    try:
        ss = client.open_by_key(SPREADSHEET_ID)
        print(f"✅ Открыта таблица: {ss.title}\n")

        # Ищем нужный лист (проверяем с нормализацией кириллицы)
        ws = None
        print("Доступные листы:")
        for w in ss.worksheets():
            print(f"  - '{w.title}'")

        for w in ss.worksheets():
            title_norm = w.title.lower().replace("с", "c")  # кириллица -> латиница
            if "2025" in w.title and ("certif" in title_norm or "сертиф" in w.title.lower()):
                ws = w
                print(f"\n✅ Найден лист: '{w.title}'")
                print(f"   ID: {w.id}")
                print(f"   Строк: {w.row_count}")
                print(f"   Колонок: {w.col_count}\n")
                break

        if not ws:
            print("❌ Лист 'Certificate 2025' не найден")
            return

        print("=" * 80)
        print("📖 СОДЕРЖИМОЕ ЛИСТА")
        print("=" * 80 + "\n")

        all_values = ws.get_all_values()
        print(f"📊 Всего строк данных: {len(all_values)}\n")

        # Показываем первые 30 строк
        print("🔍 Первые 30 строк:")
        print("-" * 80)
        for idx in range(min(30, len(all_values))):
            row = all_values[idx]
            # Показываем первые 8 колонок
            cells = []
            for i, cell in enumerate(row[:8]):
                if cell.strip():
                    cells.append(f"{chr(65+i)}:{cell[:15]}")

            if cells:
                print(f"Строка {idx+1:3d}: {' | '.join(cells)}")
            else:
                print(f"Строка {idx+1:3d}: (пустая)")

        print("\n" + "=" * 80)
        print("🔍 ПОИСК ЗАГОЛОВКОВ")
        print("=" * 80 + "\n")

        header_keywords = ['фамилия', 'имя', 'male', 'female', 'иин', 'телефон', 'пол']
        header_row_idx = None

        for row_idx in range(min(15, len(all_values))):
            row = all_values[row_idx]
            row_text = " ".join([str(cell).lower() for cell in row])
            keyword_count = sum(1 for kw in header_keywords if kw in row_text)

            if keyword_count >= 2:
                header_row_idx = row_idx
                print(f"✅ Заголовки найдены в строке {row_idx + 1} (совпадений: {keyword_count})")
                print(f"   Содержимое:")
                for i, cell in enumerate(row[:12]):
                    if cell.strip():
                        print(f"      {chr(65+i)}: {cell}")
                break

        if header_row_idx is None:
            print("❌ Заголовки не найдены")
            return

        # Находим колонку с именем
        headers = all_values[header_row_idx]
        name_col = None
        for idx, header in enumerate(headers):
            h_lower = header.strip().lower()
            if ('фамилия' in h_lower and 'имя' in h_lower) or 'name' in h_lower:
                name_col = idx
                print(f"\n✅ Колонка 'Фамилия Имя': {chr(65+idx)} (индекс {idx})")
                break

        if name_col is None:
            print("\n❌ Колонка с именами не найдена")
            return

        print("\n" + "=" * 80)
        print("🔍 ПОИСК ПАЛОМНИКОВ")
        print("=" * 80 + "\n")

        # Ищем всех паломников
        pilgrims = []
        empty_gaps = []  # Пустые промежутки между паломниками

        last_pilgrim_row = None

        for row_idx in range(header_row_idx + 1, len(all_values)):
            row = all_values[row_idx]

            if row and len(row) > name_col:
                name_value = str(row[name_col]).strip()

                if name_value:
                    # Если был промежуток, сохраняем
                    if last_pilgrim_row is not None and row_idx - last_pilgrim_row > 1:
                        gap_size = row_idx - last_pilgrim_row - 1
                        empty_gaps.append({
                            'after_row': last_pilgrim_row,
                            'gap_size': gap_size,
                            'rows': list(range(last_pilgrim_row + 1, row_idx))
                        })

                    pilgrims.append({
                        'row': row_idx + 1,
                        'name': name_value,
                        'data': [cell[:20] for cell in row[:8]]
                    })
                    last_pilgrim_row = row_idx

        print(f"📊 Статистика:")
        print(f"   Заголовки: строка {header_row_idx + 1}")
        print(f"   Всего паломников: {len(pilgrims)}")
        if pilgrims:
            print(f"   Первый паломник: строка {pilgrims[0]['row']}")
            print(f"   Последний паломник: строка {pilgrims[-1]['row']}")
            print(f"   Новая запись будет: строка {pilgrims[-1]['row'] + 1}")

        print(f"\n   Пустых промежутков: {len(empty_gaps)}")

        # Показываем первых 5
        print("\n📋 Первые 5 паломников:")
        for p in pilgrims[:5]:
            print(f"   Строка {p['row']:4d}: {p['name']}")

        # Показываем последних 10
        print("\n📋 Последние 10 паломников:")
        for p in pilgrims[-10:]:
            print(f"   Строка {p['row']:4d}: {p['name']}")

        # Показываем пустые промежутки
        if empty_gaps:
            print("\n⚠️ ПУСТЫЕ ПРОМЕЖУТКИ МЕЖДУ ПАЛОМНИКАМИ:")
            for gap in empty_gaps[:5]:  # Первые 5
                print(f"   После строки {gap['after_row']}: {gap['gap_size']} пустых строк")

        # Анализ после последнего паломника
        if pilgrims:
            print("\n" + "=" * 80)
            print("🔍 СТРОКИ ПОСЛЕ ПОСЛЕДНЕГО ПАЛОМНИКА")
            print("=" * 80 + "\n")

            last_row = pilgrims[-1]['row'] - 1  # 0-indexed
            print(f"Последний паломник в строке {last_row + 1}")
            print(f"Проверяем следующие 15 строк:\n")

            for row_idx in range(last_row + 1, min(last_row + 16, len(all_values))):
                row = all_values[row_idx]
                row_content = " | ".join([cell[:20] for cell in row[:6] if cell.strip()])

                if row_content:
                    print(f"Строка {row_idx + 1:4d}: {row_content}")
                else:
                    print(f"Строка {row_idx + 1:4d}: (пустая)")

        print("\n" + "=" * 80)
        print("✅ АНАЛИЗ ЗАВЕРШЕН")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
