#!/usr/bin/env python3
"""
Тестовый скрипт для парсинга таблицы Certificate
Показывает структуру таблицы и логику поиска последнего паломника
"""

import sys
import os

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from bull_project.bull_bot.config.settings import get_google_client


def parse_certificate_table():
    """Парсит таблицу Certificate и показывает структуру"""

    # ID таблицы из ссылки
    SPREADSHEET_ID = "1KA7IHRs4uI4thWX8O7zm2W5VHLQ01jfkqY59C4FaKSs"

    print("=" * 80)
    print("📊 ПАРСИНГ ТАБЛИЦЫ CERTIFICATE")
    print("=" * 80)

    # Получаем клиент
    client = get_google_client()
    if not client:
        print("❌ Не удалось подключиться к Google Sheets")
        return

    print("✅ Google Sheets клиент подключен\n")

    # Открываем таблицу
    try:
        ss = client.open_by_key(SPREADSHEET_ID)
        print(f"📋 Таблица: {ss.title}")
        print(f"   URL: {ss.url}\n")

        # Получаем все листы
        worksheets = ss.worksheets()
        print(f"📄 Найдено листов: {len(worksheets)}")
        for idx, ws in enumerate(worksheets, 1):
            print(f"   {idx}. {ws.title} (ID: {ws.id}, строк: {ws.row_count})")

        print("\n" + "=" * 80)

        # Ищем лист Certificate 2025
        certificate_keywords = ["certificate", "сертификат", "cert"]
        target_ws = None

        for ws in worksheets:
            title_lower = ws.title.lower()
            if any(kw in title_lower for kw in certificate_keywords):
                target_ws = ws
                print(f"✅ Найден лист Certificate: '{ws.title}'")
                break

        if not target_ws:
            print("❌ Не найден лист Certificate")
            # Пробуем взять первый лист
            target_ws = worksheets[0]
            print(f"   Используем первый лист: '{target_ws.title}'")

        print("\n" + "=" * 80)
        print(f"📖 АНАЛИЗ ЛИСТА: {target_ws.title}")
        print("=" * 80 + "\n")

        # Получаем все данные
        all_values = target_ws.get_all_values()
        print(f"📊 Всего строк в листе: {len(all_values)}\n")

        # Показываем первые 20 строк
        print("🔍 Первые 20 строк (для анализа структуры):")
        print("-" * 80)
        for idx, row in enumerate(all_values[:20], 1):
            # Показываем только первые 5 колонок для читаемости
            row_preview = " | ".join(str(cell)[:20] for cell in row[:5])
            if not any(cell.strip() for cell in row[:5]):
                row_preview = "(пустая строка)"
            print(f"Строка {idx:3d}: {row_preview}")

        print("\n" + "=" * 80)
        print("🔍 ПОИСК ЗАГОЛОВКОВ В ПЕРВЫХ 10 СТРОКАХ")
        print("=" * 80 + "\n")

        # Ищем заголовки
        header_keywords = ['фамилия', 'имя', 'male', 'female', 'иин', 'телефон']
        header_row_idx = None

        for row_idx in range(min(10, len(all_values))):
            row = all_values[row_idx]
            row_text = " ".join([str(cell).lower() for cell in row])

            # Проверяем есть ли хотя бы 2 ключевых слова
            keyword_count = sum(1 for kw in header_keywords if kw in row_text)

            if keyword_count >= 2:
                header_row_idx = row_idx
                print(f"✅ Заголовки найдены в строке {row_idx + 1}")
                print(f"   Совпадений ключевых слов: {keyword_count}")
                print(f"   Содержимое:")
                for idx, cell in enumerate(row[:15], 1):
                    if cell.strip():
                        print(f"      Колонка {idx}: {cell}")
                break

        if header_row_idx is None:
            print("❌ Заголовки не найдены в первых 10 строках")
            return

        # Определяем колонку с именами
        headers = all_values[header_row_idx]
        name_col = None

        for idx, header in enumerate(headers):
            header_lower = header.strip().lower()
            if 'фамилия' in header_lower and 'имя' in header_lower:
                name_col = idx
                print(f"\n✅ Колонка 'Фамилия Имя' найдена: индекс {idx} (колонка {chr(65 + idx)})")
                break
            elif 'name' in header_lower:
                name_col = idx
                print(f"\n✅ Колонка 'Name' найдена: индекс {idx} (колонка {chr(65 + idx)})")
                break

        if name_col is None:
            print("\n❌ Не найдена колонка с именами")
            return

        print("\n" + "=" * 80)
        print("🔍 ПОИСК ПОСЛЕДНЕГО ПАЛОМНИКА")
        print("=" * 80 + "\n")

        # Ищем последнего паломника
        last_row = header_row_idx + 1
        pilgrims = []

        for row_idx in range(header_row_idx + 1, len(all_values)):
            row_data = all_values[row_idx]

            if row_data and len(row_data) > name_col:
                cell_value = str(row_data[name_col]).strip()

                if cell_value and cell_value != '':
                    last_row = row_idx + 1  # +1 для Google Sheets нумерации

                    # Сохраняем информацию о паломнике
                    pilgrim_info = {
                        'row': row_idx + 1,
                        'name': cell_value,
                        'data': row_data[:10]  # Первые 10 колонок
                    }
                    pilgrims.append(pilgrim_info)

        print(f"📊 Статистика:")
        print(f"   Всего паломников найдено: {len(pilgrims)}")
        print(f"   Заголовки в строке: {header_row_idx + 1}")
        print(f"   Первый паломник в строке: {pilgrims[0]['row'] if pilgrims else 'нет'}")
        print(f"   Последний паломник в строке: {last_row}")
        print(f"   Новая запись будет в строке: {last_row + 1}")

        # Показываем первых 5 паломников
        print("\n📋 Первые 5 паломников:")
        for idx, p in enumerate(pilgrims[:5], 1):
            print(f"   {idx}. Строка {p['row']}: {p['name']}")

        # Показываем последних 5 паломников
        if len(pilgrims) > 5:
            print("\n📋 Последние 5 паломников:")
            for idx, p in enumerate(pilgrims[-5:], len(pilgrims) - 4):
                print(f"   {idx}. Строка {p['row']}: {p['name']}")

        # Проверяем есть ли пустые строки после последнего паломника
        print("\n" + "=" * 80)
        print("🔍 АНАЛИЗ СТРОК ПОСЛЕ ПОСЛЕДНЕГО ПАЛОМНИКА")
        print("=" * 80 + "\n")

        empty_rows_after = []
        for row_idx in range(last_row, min(last_row + 20, len(all_values))):
            row_data = all_values[row_idx]

            # Проверяем все ячейки в строке
            row_content = " ".join(str(cell).strip() for cell in row_data)

            if not row_content:
                empty_rows_after.append(row_idx + 1)
            else:
                print(f"Строка {row_idx + 1}: {row_content[:100]}")

        if empty_rows_after:
            print(f"\n✅ Пустых строк после последнего паломника: {len(empty_rows_after)}")
            print(f"   Строки: {empty_rows_after[:5]}")

        print("\n" + "=" * 80)
        print("✅ АНАЛИЗ ЗАВЕРШЕН")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    parse_certificate_table()
