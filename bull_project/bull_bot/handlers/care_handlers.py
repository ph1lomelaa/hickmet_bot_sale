import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest
from contextlib import suppress

# Импорты
from bull_project.bull_bot.database.requests import (
    search_tourist_by_name,
    get_all_bookings_in_package,
    get_db_packages_list,
    get_booking_by_id
)
from bull_project.bull_bot.core.passport_storage import resolve_passport_file_path
from bull_project.bull_bot.core.google_sheets.client import (
    get_accessible_tables, get_sheet_names
)
from bull_project.bull_bot.config.keyboards import (
    get_menu_by_role, kb_select_table, kb_select_sheet, care_kb
)

router = Router()

class CareFlow(StatesGroup):
    waiting_search_query = State()
    choosing_table = State()
    choosing_sheet = State()
    choosing_pkg = State()

# ==================== 🔍 1. ПОИСК ТУРИСТА ====================

@router.callback_query(F.data == "care_search")
async def start_search(call: CallbackQuery, state: FSMContext):
    # Удаляем старое меню, чтобы не мусорить
    with suppress(TelegramBadRequest):
        await call.message.delete()

    await call.message.answer(
        "🔎 <b>Поиск туриста</b>\n\n"
        "Напишите Фамилию или Имя (можно частично):\n"
        "<i>Например: Zubanov или Зубанов</i>",
        parse_mode="HTML"
    )
    await state.set_state(CareFlow.waiting_search_query)
    await call.answer()

@router.message(CareFlow.waiting_search_query)
async def process_search(message: Message, state: FSMContext):
    query = message.text.strip()
    results = await search_tourist_by_name(query)

    if not results:
        await message.answer("❌ Никого не нашел. Попробуйте по-другому.", reply_markup=care_kb())
        await state.clear()
        return

    # Если нашли одного - сразу показываем карточку
    if len(results) == 1:
        b = results[0]
        await show_tourist_card(message, b)
        await state.clear()
    else:
        # Если много - даем кнопки
        kb = []
        for b in results:
            btn_text = f"{b.guest_last_name} {b.guest_first_name} | {b.package_name[:10]}..."
            kb.append([InlineKeyboardButton(text=btn_text, callback_data=f"care_view:{b.id}")])

        await message.answer(
            f"🔎 Найдено {len(results)} туристов. Выберите:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )
        await state.clear()

@router.callback_query(F.data.startswith("care_view:"))
async def view_specific_tourist(call: CallbackQuery):
    bid = int(call.data.split(":")[1])
    b = await get_booking_by_id(bid)

    # Удаляем меню выбора
    with suppress(TelegramBadRequest):
        await call.message.delete()

    if b:
        await show_tourist_card(call.message, b)
    else:
        await call.answer("Бронь не найдена", show_alert=True)
        # Если не нашли, вернем меню
        await call.message.answer("👋 Меню Заботы", reply_markup=care_kb())

    await call.answer()

async def show_tourist_card(message: Message, b):
    """
    Показывает карточку.
    ЕСЛИ есть фото паспорта -> Шлет фото с описанием.
    ЕСЛИ нет -> Шлет текст.
    """
    # Формируем текст (Манифест)
    text = (
        f"👤 <b>{b.guest_last_name} {b.guest_first_name}</b>\n"
        f"──────────────────\n"
        f"📞 <b>ТЕЛЕФОН:</b> <code>{b.client_phone}</code>\n"
        f"──────────────────\n"
        f"🛂 Паспорт: {b.passport_num} (до {b.passport_expiry})\n"
        f"📅 Пакет: {b.package_name}\n"
        f"📍 Дата: {b.sheet_name}\n"
        f"🏨 Номер: {b.room_type} | 🍽 Питание: {b.meal_type}\n"
        f"👤 Менеджер: {b.manager_name_text}\n"
        f"📝 Коммент: {b.comment}\n"
        f"🚆 Поезд: {b.train}"
    )

    passport_path = resolve_passport_file_path(getattr(b, "passport_image_path", None))
    bk_rows = []
    if passport_path:
        bk_rows.append([InlineKeyboardButton(text="📎 Скачать паспорт", callback_data=f"care_passport:{b.id}")])
    bk_rows.append([InlineKeyboardButton(text="🔙 В меню", callback_data="care_menu")])
    bk = InlineKeyboardMarkup(inline_keyboard=bk_rows)

    # 🔥 ПРОВЕРКА ФОТО
    if passport_path:
        try:
            photo = FSInputFile(passport_path)
            # Отправляем фото
            await message.answer_photo(photo, caption=text, reply_markup=bk, parse_mode="HTML")
            return
        except Exception as e:
            print(f"Ошибка отправки фото: {e}")

    # Фолбэк: Отправляем просто текст
    await message.answer(text, reply_markup=bk, parse_mode="HTML")


@router.callback_query(F.data.startswith("care_passport:"))
async def care_send_passport(call: CallbackQuery):
    bid = int(call.data.split(":")[1])
    b = await get_booking_by_id(bid)
    if not b:
        await call.answer("Бронь не найдена", show_alert=True)
        return

    passport_path = resolve_passport_file_path(getattr(b, "passport_image_path", None))
    if not passport_path:
        await call.answer("Паспорт не найден", show_alert=True)
        return

    try:
        await call.message.answer_document(FSInputFile(passport_path), caption="📎 Паспорт")
    except Exception as e:
        await call.answer(f"Ошибка отправки: {e}", show_alert=True)
        return

    with suppress(Exception):
        await call.answer()

# ==================== 📞 2. СБОР ТЕЛЕФОНОВ ====================

@router.callback_query(F.data == "care_phones")
async def start_phones(call: CallbackQuery, state: FSMContext):
    # Удаляем старое, шлем новое
    with suppress(TelegramBadRequest):
        await call.message.delete()

    tables = get_accessible_tables()
    await call.message.answer("📅 <b>Выберите таблицу (Месяц):</b>", reply_markup=kb_select_table(tables), parse_mode="HTML")
    await state.set_state(CareFlow.choosing_table)
    await call.answer()

@router.callback_query(CareFlow.choosing_table, F.data.startswith("sel_tab:"))
async def care_sel_table(call: CallbackQuery, state: FSMContext):
    sid = call.data.split(":")[1]
    await state.update_data(current_sheet_id=sid)
    sheets = get_sheet_names(sid)

    await call.message.edit_text("✈️ <b>Выберите Лист (Дату):</b>", reply_markup=kb_select_sheet(sheets[:15], len(sheets)>15), parse_mode="HTML")
    await state.set_state(CareFlow.choosing_sheet)
    await call.answer()

@router.callback_query(CareFlow.choosing_sheet, F.data.startswith("sel_date:"))
async def care_sel_date(call: CallbackQuery, state: FSMContext):
    sname = call.data.split(":")[1]
    await state.update_data(current_sheet_name=sname)
    data = await state.get_data()

    # 🔥 ИСПРАВЛЕНИЕ: Используем get_packages_from_sheet вместо get_db_packages_list
    # Это та же функция, что используется при создании брони
    packages_dict = get_packages_from_sheet(data['current_sheet_id'], sname)

    if not packages_dict:
        await call.message.edit_text("❌ На этой дате нет пакетов.", reply_markup=care_kb())
        await state.clear()
        return

    # Извлекаем только названия пакетов (значения из словаря)
    packages = list(packages_dict.values())

    print(f"\n🔍 ОТДЕЛ ЗАБОТ - найдено пакетов:")
    print(f"   Sheet ID: {data['current_sheet_id']}")
    print(f"   Sheet Name: {sname}")
    print(f"   Пакеты: {packages}")

    # 🔥 ИСПРАВЛЕНИЕ: Используем индекс вместо усечения названия
    kb = []
    for idx, pkg in enumerate(packages):
        if not pkg: continue
        display_name = pkg[:40] if len(pkg) > 40 else pkg  # Для отображения
        kb.append([InlineKeyboardButton(
            text=f"📦 {display_name}",
            callback_data=f"care_pkg:{idx}"  # Передаем индекс, а не название
        )])

    await state.update_data(available_packages=packages)

    await call.message.edit_text("📦 <b>Выберите Пакет для списка:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")
    await state.set_state(CareFlow.choosing_pkg)
    await call.answer()

@router.callback_query(CareFlow.choosing_pkg, F.data.startswith("care_pkg:"))
async def show_phone_list(call: CallbackQuery, state: FSMContext):
    # 🔥 ИСПРАВЛЕНИЕ: Получаем индекс, а не усеченное название
    pkg_idx_str = call.data.split(":")[1]
    pkg_idx = int(pkg_idx_str)
    data = await state.get_data()

    available_packages = data.get('available_packages', [])
    if pkg_idx >= len(available_packages):
        await call.answer("Ошибка: пакет не найден", show_alert=True)
        return

    full_pkg_name = available_packages[pkg_idx]

    # 🔥 ДЕБАГ: Показываем что ищем
    print(f"\n📞 ОТДЕЛ ЗАБОТ - Поиск бронирований:")
    print(f"   pkg_idx (из callback): {pkg_idx}")
    print(f"   full_pkg_name (по индексу): {full_pkg_name}")
    print(f"   sheet_id: {data['current_sheet_id']}")
    print(f"   sheet_name: {data['current_sheet_name']}")
    print(f"   available_packages: {available_packages}")

    bookings = await get_all_bookings_in_package(data['current_sheet_id'], data['current_sheet_name'], full_pkg_name)

    print(f"   Найдено бронирований: {len(bookings) if bookings else 0}")
    if bookings:
        for i, b in enumerate(bookings[:3]):  # Показываем первые 3
            print(f"   Бронь {i+1}: {b.guest_last_name} {b.guest_first_name} | {b.client_phone}")

    if not bookings:
        await call.answer("Пусто", show_alert=True)
        return

    report = f"📋 <b>СПИСОК ТУРИСТОВ</b>\n📦 {full_pkg_name}\n📅 {data['current_sheet_name']}\n\n"

    for i, b in enumerate(bookings, 1):
        phone = b.client_phone if b.client_phone else "❌ Нет номера"
        report += f"{i}. <b>{b.guest_last_name} {b.guest_first_name}</b>\n   📞 <code>{phone}</code>\n"

    back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 В меню", callback_data="care_menu")]])

    # Удаляем кнопки выбора пакета и шлем новый отчет
    with suppress(TelegramBadRequest):
        await call.message.delete()

    if len(report) > 4000:
        await call.message.answer(report[:4000], parse_mode="HTML")
        await call.message.answer(report[4000:], parse_mode="HTML", reply_markup=back_kb)
    else:
        await call.message.answer(report, reply_markup=back_kb, parse_mode="HTML")

    await state.clear()
    await call.answer()

@router.callback_query(F.data == "care_menu")
async def care_home(call: CallbackQuery, state: FSMContext):
    await state.clear()
    with suppress(TelegramBadRequest):
        await call.message.delete()
    await call.message.answer("🤝 <b>Ассаламу алейкум! Отдел Заботы</b>", reply_markup=care_kb(), parse_mode="HTML")
    await call.answer()
