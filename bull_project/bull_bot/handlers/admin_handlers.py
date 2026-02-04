from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder # 🔥
from contextlib import suppress
from aiogram.exceptions import TelegramBadRequest

from bull_project.bull_bot.core.google_sheets.four_u_logic import find_availability_for_4u, create_4u_sheet
from bull_project.bull_bot.database.models import Base
from bull_project.bull_bot.database.requests import (
    get_active_4u_requests, get_4u_request_by_id, update_4u_status,
    get_approval_request, update_approval_status, get_booking_by_id,
    mark_booking_cancelled, update_booking_fields, get_user_role, get_manager_packages, get_bookings_in_package,
    get_admin_settings, set_admin_settings, update_booking_row,
    get_pending_requests_for_admin,
    delete_admin_request_inbox,
)
from bull_project.bull_bot.config.keyboards import admin_kb
from bull_project.bull_bot.config.constants import bot
from bull_project.bull_bot.database.setup import engine
from bull_project.bull_bot.core.google_sheets.writer import (
    clear_booking_in_sheets, write_cancelled_booking_red,
    save_group_booking, write_rescheduled_booking_red,
    find_pilgrim_in_package
)
from bull_project.bull_bot.database.requests import mark_booking_rescheduled

router = Router()

# TODO: Разместите файлы на GitHub Pages или другом хостинге
ADMIN_PANEL_URL = "https://ph1lomelaa.github.io/book/admin-panel.html"
ADMIN_BOOKINGS_URL = "https://ph1lomelaa.github.io/book/admin-bookings.html"
ADMIN_CREATE_URL = "https://ph1lomelaa.github.io/book/admin-create-booking.html"
ADMIN_REQUESTS_URL = "https://ph1lomelaa.github.io/book/admin-requests.html"

# === ADMIN COMMANDS: PENDING CANCEL/RESCHEDULE REQUESTS ===

def _fmt_req_short(req, booking) -> str:
    req_type = "Отмена" if req.request_type == "cancel" else ("Перенос" if req.request_type == "reschedule" else req.request_type)
    name = "-"
    if booking:
        name = f"{(booking.guest_last_name or '').strip()} {(booking.guest_first_name or '').strip()}".strip() or "-"
    return f"{req_type} #{req.id} · {name}"


async def _send_requests_list(message: Message, request_type: str):
    print(f"📋 _send_requests_list вызвана: user_id={message.from_user.id}, request_type={request_type}")

    role = await get_user_role(message.from_user.id)
    print(f"   👤 Роль пользователя: {role}")

    if role != "admin":
        print(f"   ❌ Доступ запрещён: роль {role} != admin")
        await message.answer("❌ Команда доступна только администраторам.")
        return

    pending = await get_pending_requests_for_admin(message.from_user.id, request_type)
    print(f"   📦 Pending requests для админа ({request_type}): {len(pending)}")

    if not pending:
        print(f"   ℹ️ Нет активных заявок типа '{request_type}'")
        await message.answer("✅ Активных заявок нет.", reply_markup=admin_kb())
        return

    builder = InlineKeyboardBuilder()
    for req in pending[:50]:
        booking = await get_booking_by_id(req.booking_id)
        builder.button(text=_fmt_req_short(req, booking), callback_data=f"admin_req_view:{req.id}:{request_type}")
    builder.button(text="Открыть запросы (WebApp)", web_app=WebAppInfo(url=ADMIN_REQUESTS_URL))
    builder.adjust(1)

    title = "Заявки на отмену" if request_type == "cancel" else "Заявки на перенос"
    print(f"   ✅ Отправка списка из {len(pending[:50])} заявок")
    await message.answer(f"📋 <b>{title}</b>\nВыберите заявку:", reply_markup=builder.as_markup(), parse_mode="HTML")


@router.message(Command("cancel"))
async def admin_cmd_cancel(message: Message):
    print(f"📥 /cancel команда получена от пользователя {message.from_user.id}")
    await _send_requests_list(message, "cancel")


@router.message(Command("reschedule"))
async def admin_cmd_reschedule(message: Message):
    print(f"📥 /reschedule команда получена от пользователя {message.from_user.id}")
    await _send_requests_list(message, "reschedule")


@router.callback_query(F.data.startswith("admin_req_view:"))
async def admin_req_view(call: CallbackQuery):
    role = await get_user_role(call.from_user.id)
    if role != "admin":
        await call.answer("❌ Только администраторы", show_alert=True)
        return

    parts = call.data.split(":")
    req_id = int(parts[1])
    req_type = parts[2] if len(parts) > 2 else ""

    req = await get_approval_request(req_id)
    if not req:
        await call.answer("Заявка не найдена", show_alert=True)
        return

    booking = await get_booking_by_id(req.booking_id)

    full_name = "-"
    pkg = "-"
    sheet = "-"
    phone = "-"
    manager = "-"
    if booking:
        full_name = f"{booking.guest_last_name or '-'} {booking.guest_first_name or '-'}".strip()
        pkg = booking.package_name or "-"
        sheet = booking.sheet_name or "-"
        phone = booking.client_phone or "-"
        manager = booking.manager_name_text or "-"

    comment = (req.comment or "-").strip() or "-"
    created_at = req.created_at.strftime("%d.%m.%Y %H:%M") if getattr(req, "created_at", None) else "-"

    title = "🔵 ЗАПРОС НА ОТМЕНУ" if req.request_type == "cancel" else "🔵 ЗАПРОС НА ПЕРЕНОС"
    text = (
        f"{title}\n\n"
        f"ФИО: {full_name}\n\n"
        f"Пакет: {pkg}\n"
        f"Лист: {sheet}\n"
        f"Телефон: {phone}\n"
        f"Менеджер: {manager}\n\n"
        f"━━━ ЗАЯВКА ━━━\n"
        f"Комментарий: {comment}\n"
        f"Дата заявки: {created_at}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть запросы (WebApp)", web_app=WebAppInfo(url=ADMIN_REQUESTS_URL))],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_req_back:{req_type}")],
    ])

    with suppress(TelegramBadRequest):
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("admin_req_back:"))
async def admin_req_back(call: CallbackQuery):
    role = await get_user_role(call.from_user.id)
    if role != "admin":
        await call.answer("❌ Только администраторы", show_alert=True)
        return

    req_type = call.data.split(":")[1] if ":" in call.data else "cancel"
    pending = await get_pending_requests_for_admin(call.from_user.id, req_type)

    if not pending:
        with suppress(TelegramBadRequest):
            await call.message.edit_text("✅ Активных заявок нет.", reply_markup=admin_kb(), parse_mode="HTML")
        await call.answer()
        return

    builder = InlineKeyboardBuilder()
    for req in pending[:50]:
        booking = await get_booking_by_id(req.booking_id)
        builder.button(text=_fmt_req_short(req, booking), callback_data=f"admin_req_view:{req.id}:{req_type}")
    builder.button(text="Открыть запросы (WebApp)", web_app=WebAppInfo(url=ADMIN_REQUESTS_URL))
    builder.adjust(1)

    title = "Заявки на отмену" if req_type == "cancel" else "Заявки на перенос"
    with suppress(TelegramBadRequest):
        await call.message.edit_text(f"📋 <b>{title}</b>\nВыберите заявку:", reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()

# === 1. СПИСОК ЗАЯВОК ===
@router.callback_query(F.data == "admin_stats")
async def show_4u_list(call: CallbackQuery):
    requests = await get_active_4u_requests()

    if not requests:
        with suppress(TelegramBadRequest):
            await call.message.edit_text("📭 <b>Активных заявок 4U нет.</b>", reply_markup=admin_kb(), parse_mode="HTML")
        return

    builder = InlineKeyboardBuilder()
    for req in requests:
        icon = "🔴" if req.status == 'pending' else "🟢"
        builder.button(text=f"{icon} #{req.id} | {req.manager_name} | {req.dates}", callback_data=f"view_4u:{req.id}")

    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu"))

    with suppress(TelegramBadRequest):
        await call.message.edit_text("📋 <b>ЗАЯВКИ НА 4U:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()

# === 2. ПРОСМОТР ЗАЯВКИ ===
@router.callback_query(F.data.startswith("view_4u:"))
async def view_request(call: CallbackQuery):
    req_id = int(call.data.split(":")[1])
    req = await get_4u_request_by_id(req_id)

    if not req:
        await call.answer("Заявка не найдена")
        return

    text = (
        f"<b>ЗАЯВКА #{req.id}</b>\n"
        f"<b>Менеджер:</b> {req.manager_name}\n"
        f"<b>Даты:</b> {req.dates}\n"
        f"<b>Людей:</b> {req.pilgrim_count}\n"
        f"<b>Номер:</b> {req.room_type}\n"
        f"<b>Статус:</b> {req.status}\n"
    )

    kb = InlineKeyboardBuilder()
    if req.status == 'pending':
        # Кнопки в 2 колонки
        kb.button(text="Проверить места", callback_data=f"check_4u:{req.id}")
        kb.button(text="Создать лист", callback_data=f"approve_start:{req.id}")
        kb.button(text="Отклонить", callback_data=f"reject_4u:{req.id}")
        kb.adjust(2) # Красиво упаковываем

    kb.row(InlineKeyboardButton(text="🔙 К списку", callback_data="admin_stats"))

    await call.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")

# === 3. ПРОВЕРКА МЕСТ ===
@router.callback_query(F.data.startswith("check_4u:"))
async def check_availability(call: CallbackQuery):
    req_id = int(call.data.split(":")[1])
    req = await get_4u_request_by_id(req_id)

    await call.message.edit_text("⏳ <b>Сканирую таблицу...</b>", parse_mode="HTML")

    results = await find_availability_for_4u(req.table_id, req.dates, req.pilgrim_count, req.room_type)

    kb = InlineKeyboardBuilder()
    if not results:
        text = "🤷‍♂️ <b>Свободных блоков не найдено.</b>\nСоздавайте новый лист."
        kb.button(text="➕ Создать новый лист", callback_data=f"approve_start:{req_id}")
    else:
        text = "🔎 <b>Найдены места:</b>\n\n"
        for r in results:
            text += f"🔹 {r['package']}\n📄 {r['sheet']}\n🧹 Удалить: {r['rows_to_clear']}\n---\n"

        kb.button(text="Создать лист", callback_data=f"approve_start:{req_id}")

    kb.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"view_4u:{req_id}"))

    await call.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")

# === 4. СОЗДАНИЕ ===
@router.callback_query(F.data.startswith("approve_start:"))
async def create_sheet_confirm(call: CallbackQuery):
    req_id = int(call.data.split(":")[1])
    req = await get_4u_request_by_id(req_id)

    text = f"🚀 <b>Создание листа 4U</b>\n📅 {req.dates}\n🛏 {req.pilgrim_count} мест ({req.room_type})\n\nПодтверждаете?"

    kb = InlineKeyboardBuilder()
    kb.button(text="🔥 ПОДТВЕРДИТЬ", callback_data=f"do_create_4u:{req_id}")
    kb.button(text="Отмена", callback_data=f"view_4u:{req_id}")
    kb.adjust(2)

    await call.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("do_create_4u:"))
async def execute_creation(call: CallbackQuery):
    req_id = int(call.data.split(":")[1])
    req = await get_4u_request_by_id(req_id)

    await call.message.edit_text("⏳ <b>Создаю лист и объединяю ячейки...</b>", parse_mode="HTML")

    success, result_msg = await create_4u_sheet(
        req.table_id, req.dates, req.pilgrim_count, req.room_type, req.manager_name
    )

    if success:
        await update_4u_status(req_id, "approved", sheet_name=result_msg)
        try: await bot.send_message(req.manager_id, f"✅ <b>Заявка 4U одобрена!</b>\nЛист: <code>{result_msg}</code>")
        except: pass

        await call.message.edit_text(
            f"✅ <b>Готово!</b> Лист <code>{result_msg}</code> создан.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 К списку", callback_data="admin_stats")]])
        )
    else:
        await call.message.edit_text(f"❌ Ошибка: {result_msg}",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data=f"view_4u:{req_id}")]]))

# === 5. ОТКЛОНЕНИЕ ===
@router.callback_query(F.data.startswith("reject_4u:"))
async def reject_request(call: CallbackQuery):
    req_id = int(call.data.split(":")[1])
    req = await get_4u_request_by_id(req_id)

    if req:
        await update_4u_status(req_id, "rejected")
        try: await bot.send_message(req.manager_id, f"❌ Заявка 4U на {req.dates} отклонена.")
        except: pass

    await call.message.edit_text(
        "❌ Заявка отклонена.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 К списку", callback_data="admin_stats")]])
    )

# === ОДОБРЕНИЕ ОТМЕНЫ/ПЕРЕНОСА ===
async def _perform_cancel(booking):
    sheets_cleared = False
    guest_name = f"{booking.guest_last_name} {booking.guest_first_name}"

    if booking.sheet_row_number and booking.table_id and booking.sheet_name:
        try:
            sheets_cleared = await clear_booking_in_sheets(
                booking.table_id,
                booking.sheet_name,
                booking.sheet_row_number,
                booking.package_name,
                expected_guest_name=guest_name,  # 🔒 Проверяем имя перед удалением
            )
            if not sheets_cleared:
                print(f"⚠️ Не удалось очистить бронь #{booking.id} (возможно несовпадение имени)")
                # 🔥 ВАЖНО: Если не удалось очистить - НЕ отмечаем как отменённую!
                return False
        except Exception as e:
            print(f"❌ Ошибка при очистке брони #{booking.id}: {e}")
            # 🔥 ВАЖНО: При ошибке тоже НЕ отмечаем как отменённую!
            return False

    red_written = False
    if booking.table_id and booking.sheet_name and booking.package_name:
        try:
            red_written = await write_cancelled_booking_red(
                booking.table_id,
                booking.sheet_name,
                booking.package_name,
                guest_name
            )
            if not red_written:
                print(f"⚠️ Не удалось записать отменённую бронь #{booking.id} в красный список")
        except Exception as e:
            print(f"❌ Ошибка при записи в красный список для брони #{booking.id}: {e}")
            red_written = False

    # ✅ Только если успешно очистили из Sheets - отмечаем в БД
    await mark_booking_cancelled(booking.id)
    return True

@router.callback_query(F.data.startswith("admin_cancel_ok:"))
async def admin_cancel_ok(call: CallbackQuery):
    # Проверка прав доступа
    role = await get_user_role(call.from_user.id)
    if role != "admin":
        await call.answer("❌ Только администраторы могут подтверждать отмену", show_alert=True)
        return

    req_id = int(call.data.split(":")[1])
    req = await get_approval_request(req_id)
    if not req or req.status != "pending":
        await call.answer("Заявка не найдена или уже обработана", show_alert=True)
        return
    booking = await get_booking_by_id(req.booking_id)
    if not booking:
        await call.answer("Бронь не найдена", show_alert=True)
        return

    await call.message.edit_text("⏳ Обрабатываю отмену...", parse_mode="HTML")
    
    cancel_success = await _perform_cancel(booking)
    
    # ❌ Если отмена не удалась - ищем паломника по всему пакету
    if not cancel_success:
        guest_name = f"{booking.guest_last_name} {booking.guest_first_name}"
        await call.message.edit_text(
            f"⏳ Имя на строке {booking.sheet_row_number} не совпадает...\n"
            f"🔍 Ищу <b>{guest_name}</b> по всему пакету...",
            parse_mode="HTML"
        )

        # Ищем паломника по всему пакету
        matches = []
        if booking.table_id and booking.sheet_name and booking.package_name:
            matches = await find_pilgrim_in_package(
                booking.table_id,
                booking.sheet_name,
                booking.package_name,
                guest_name
            )

        if matches:
            # Нашли паломника - показываем где
            buttons = []
            for found_row, found_name in matches[:5]:  # Максимум 5 результатов
                buttons.append([InlineKeyboardButton(
                    text=f"✅ Очистить строку {found_row}: {found_name}",
                    callback_data=f"admin_cancel_row:{req_id}:{booking.id}:{found_row}"
                )])

            buttons.append([InlineKeyboardButton(
                text="❌ Отклонить заявку",
                callback_data=f"admin_cancel_reject:{req_id}"
            )])
            buttons.append([InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="admin_menu"
            )])

            found_keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            await call.message.edit_text(
                f"🔍 <b>Паломник найден в другой строке!</b>\n\n"
                f"<b>Искали:</b> {guest_name}\n"
                f"<b>В БД строка:</b> {booking.sheet_row_number}\n\n"
                f"<b>Найден в пакете:</b>\n" +
                "\n".join([f"• Строка {row}: {name}" for row, name in matches[:5]]) +
                f"\n\n<b>Выберите строку для очистки:</b>",
                reply_markup=found_keyboard,
                parse_mode="HTML"
            )
        else:
            # Не нашли - показываем ошибку
            error_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="❌ Отклонить заявку",
                    callback_data=f"admin_cancel_reject:{req_id}"
                )],
                [InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="admin_menu"
                )],
            ])

            await call.message.edit_text(
                f"⚠️ <b>Паломник не найден в пакете!</b>\n\n"
                f"<b>Искали:</b> {guest_name}\n"
                f"<b>Пакет:</b> {booking.package_name}\n"
                f"<b>Лист:</b> {booking.sheet_name}\n"
                f"<b>Строка в БД:</b> {booking.sheet_row_number}\n\n"
                f"Паломник не найден ни на указанной строке, ни в других местах пакета.\n"
                f"Возможно данные уже удалены или имя записано иначе.",
                reply_markup=error_keyboard,
                parse_mode="HTML"
            )
        return
    
    # ✅ Только если успешно - отмечаем в БД
    await update_approval_status(req_id, "approved")
    await delete_admin_request_inbox(req_id)

    text = (
        f"🗑 <b>Бронь #{booking.id} отменена</b>\n"
        f"Пакет: {booking.package_name}\n"
        f"Паломник: {booking.guest_last_name} {booking.guest_first_name}\n\n"
        f"✅ Данные очищены из Google Sheets"
    )
    await call.message.edit_text(text, reply_markup=admin_kb(), parse_mode="HTML")
    # Уведомляем инициатора
    try:
        await bot.send_message(req.initiator_id, f"✅ Отмена брони #{booking.id} одобрена админом.")
    except: pass

@router.callback_query(F.data.startswith("admin_cancel_reject:"))
async def admin_cancel_reject(call: CallbackQuery):
    # Проверка прав доступа
    role = await get_user_role(call.from_user.id)
    if role != "admin":
        await call.answer("❌ Только администраторы могут отклонять отмену", show_alert=True)
        return

    req_id = int(call.data.split(":")[1])
    req = await get_approval_request(req_id)
    if not req or req.status != "pending":
        await call.answer("Заявка не найдена или уже обработана", show_alert=True)
        return
    booking = await get_booking_by_id(req.booking_id)
    if booking:
        await update_booking_fields(booking.id, {"status": "new"})
    await update_approval_status(req_id, "rejected")
    await delete_admin_request_inbox(req_id)

    await call.message.edit_text("❌ Заявка на отмену отклонена.", reply_markup=admin_kb(), parse_mode="HTML")
    try:
        await bot.send_message(req.initiator_id, f"❌ Отмена брони #{req.booking_id} отклонена админом.")
    except: pass


@router.callback_query(F.data.startswith("admin_cancel_row:"))
async def admin_cancel_at_row(call: CallbackQuery):
    """Очистка брони по найденной строке (когда исходная строка не совпала)"""
    role = await get_user_role(call.from_user.id)
    if role != "admin":
        await call.answer("❌ Только администраторы", show_alert=True)
        return

    parts = call.data.split(":")
    req_id = int(parts[1])
    booking_id = int(parts[2])
    found_row = int(parts[3])

    req = await get_approval_request(req_id)
    if not req or req.status != "pending":
        await call.answer("Заявка не найдена или уже обработана", show_alert=True)
        return

    booking = await get_booking_by_id(booking_id)
    if not booking:
        await call.answer("Бронь не найдена", show_alert=True)
        return

    await call.message.edit_text(
        f"⏳ Очищаю строку {found_row}...",
        parse_mode="HTML"
    )

    guest_name = f"{booking.guest_last_name} {booking.guest_first_name}"

    # Очищаем по найденной строке БЕЗ проверки имени (мы уже проверили при поиске)
    sheets_cleared = False
    if booking.table_id and booking.sheet_name:
        try:
            sheets_cleared = await clear_booking_in_sheets(
                booking.table_id,
                booking.sheet_name,
                found_row,  # Используем НАЙДЕННУЮ строку
                booking.package_name,
                expected_guest_name=None,  # Не проверяем - уже нашли
            )
        except Exception as e:
            print(f"❌ Ошибка при очистке строки {found_row}: {e}")

    if not sheets_cleared:
        await call.message.edit_text(
            f"❌ Не удалось очистить строку {found_row}.\n"
            f"Возможно данные уже удалены.",
            reply_markup=admin_kb(),
            parse_mode="HTML"
        )
        return

    # Записываем в красный список
    try:
        await write_cancelled_booking_red(
            booking.table_id,
            booking.sheet_name,
            booking.package_name,
            guest_name
        )
    except Exception as e:
        print(f"⚠️ Не удалось записать в красный список: {e}")

    # Обновляем номер строки в БД и отмечаем как отменённую
    await update_booking_fields(booking.id, {"sheet_row_number": found_row})
    await mark_booking_cancelled(booking.id)
    await update_approval_status(req_id, "approved")
    await delete_admin_request_inbox(req_id)

    text = (
        f"🗑 <b>Бронь #{booking.id} отменена</b>\n"
        f"Пакет: {booking.package_name}\n"
        f"Паломник: {guest_name}\n"
        f"Строка: {found_row} (найдена автоматически)\n\n"
        f"✅ Данные очищены из Google Sheets"
    )
    await call.message.edit_text(text, reply_markup=admin_kb(), parse_mode="HTML")

    try:
        await bot.send_message(req.initiator_id, f"✅ Отмена брони #{booking.id} одобрена админом.")
    except: pass


@router.callback_query(F.data.startswith("admin_resched_row:"))
async def admin_resched_clear_row(call: CallbackQuery):
    """Очистка старой брони по найденной строке при переносе"""
    role = await get_user_role(call.from_user.id)
    if role != "admin":
        await call.answer("❌ Только администраторы", show_alert=True)
        return

    parts = call.data.split(":")
    req_id = int(parts[1])
    booking_id = int(parts[2])
    found_row = int(parts[3])
    idx = int(parts[4])

    req = await get_approval_request(req_id)
    if not req:
        await call.answer("Заявка не найдена", show_alert=True)
        return

    booking = await get_booking_by_id(booking_id)
    if not booking:
        await call.answer("Бронь не найдена", show_alert=True)
        return

    await call.message.edit_text(
        f"⏳ Очищаю строку {found_row}...",
        parse_mode="HTML"
    )

    guest_name = f"{booking.guest_last_name} {booking.guest_first_name}"

    # Очищаем по найденной строке
    sheets_cleared = False
    if booking.table_id and booking.sheet_name:
        try:
            sheets_cleared = await clear_booking_in_sheets(
                booking.table_id,
                booking.sheet_name,
                found_row,
                booking.package_name,
                expected_guest_name=None,
            )
        except Exception as e:
            print(f"❌ Ошибка при очистке строки {found_row}: {e}")

    if sheets_cleared:
        # Записываем в красный список (перенос)
        try:
            await write_rescheduled_booking_red(
                booking.table_id,
                booking.sheet_name,
                booking.package_name,
                guest_name
            )
        except Exception as e:
            print(f"⚠️ Не удалось записать в красный список: {e}")

        # Обновляем номер строки и отмечаем как перенесённую
        await update_booking_fields(booking.id, {"sheet_row_number": found_row})

        # Получаем new_ids из комментария заявки
        new_ids = []
        if req.comment:
            try:
                import json as _json
                parsed = _json.loads(req.comment)
                if isinstance(parsed, dict):
                    new_ids = [int(x) for x in (parsed.get("new_booking_ids") or []) if int(x) > 0]
            except:
                pass
        if not new_ids:
            new_ids = [req.booking_id]

        target_new = new_ids[idx] if idx < len(new_ids) else new_ids[0]
        await mark_booking_rescheduled(booking.id, comment=f"Перенесено в #{target_new}")

        await call.message.edit_text(
            f"✅ <b>Строка {found_row} очищена</b>\n"
            f"Паломник: {guest_name}\n\n"
            f"Бронь #{booking.id} отмечена как перенесённая в #{target_new}",
            reply_markup=admin_kb(),
            parse_mode="HTML"
        )
    else:
        await call.message.edit_text(
            f"❌ Не удалось очистить строку {found_row}.\n"
            f"Возможно данные уже удалены.",
            reply_markup=admin_kb(),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("admin_resched_skip:"))
async def admin_resched_skip_cleanup(call: CallbackQuery):
    """Пропустить очистку старых броней и завершить перенос"""
    role = await get_user_role(call.from_user.id)
    if role != "admin":
        await call.answer("❌ Только администраторы", show_alert=True)
        return

    req_id = int(call.data.split(":")[1])

    req = await get_approval_request(req_id)
    if not req:
        await call.answer("Заявка не найдена или уже обработана", show_alert=True)
        return

    # Одобряем заявку без очистки старых данных
    await update_approval_status(req_id, "approved")
    await delete_admin_request_inbox(req_id)

    await call.message.edit_text(
        f"✅ <b>Перенос завершён</b>\n\n"
        f"⚠️ Очистка старых данных пропущена.\n"
        f"Проверьте и удалите данные в Google Sheets вручную.",
        reply_markup=admin_kb(),
        parse_mode="HTML"
    )

    try:
        await bot.send_message(req.initiator_id, f"✅ Перенос одобрен админом.")
    except: pass


@router.callback_query(F.data.startswith("admin_resched_ok:"))
async def admin_resched_ok(call: CallbackQuery):
    # Проверка прав доступа
    role = await get_user_role(call.from_user.id)
    if role != "admin":
        await call.answer("❌ Только администраторы могут подтверждать перенос", show_alert=True)
        return

    req_id = int(call.data.split(":")[1])
    req = await get_approval_request(req_id)
    if not req or req.status != "pending":
        await call.answer("Заявка не найдена или уже обработана", show_alert=True)
        return
    new_booking = await get_booking_by_id(req.booking_id)
    if not new_booking:
        await call.answer("Новая бронь не найдена", show_alert=True)
        return
    old_ids = []
    new_ids = []
    manager_comment = None
    if req.comment:
        try:
            import json as _json
            parsed = _json.loads(req.comment)
            if isinstance(parsed, dict) and ("old_booking_ids" in parsed or "new_booking_ids" in parsed):
                old_ids = [int(x) for x in (parsed.get("old_booking_ids") or []) if int(x) > 0]
                new_ids = [int(x) for x in (parsed.get("new_booking_ids") or []) if int(x) > 0]
                manager_comment = (parsed.get("comment") or "").strip() or None
        except Exception:
            pass
    if not new_ids:
        new_ids = [new_booking.id]
    if not old_ids and req.comment and req.comment.startswith("old:"):
        try:
            old_ids = [int(req.comment.split("old:")[1])]
        except Exception:
            old_ids = []
    old_bookings = []
    for oid in old_ids:
        b = await get_booking_by_id(oid)
        if b:
            old_bookings.append(b)

    await call.message.edit_text("⏳ Обрабатываю перенос...", parse_mode="HTML")

    # Запись новой брони в Sheets
    common_data = {
        'table_id': new_booking.table_id,
        'sheet_name': new_booking.sheet_name,
        'package_name': new_booking.package_name,
        'room_type': new_booking.room_type,
        'meal_type': new_booking.meal_type,
        'price': new_booking.price,
        'amount_paid': new_booking.amount_paid,
        'exchange_rate': new_booking.exchange_rate,
        'discount': new_booking.discount,
        'contract_number': new_booking.contract_number,
        'region': new_booking.region,
        'departure_city': new_booking.departure_city,
        'source': new_booking.source,
        'comment': new_booking.comment,
        'manager_name_text': new_booking.manager_name_text,
        'train': new_booking.train,
    }
    persons = []
    for bid in new_ids:
        nb = await get_booking_by_id(bid)
        if not nb:
            continue
        persons.append({
            "Last Name": nb.guest_last_name,
            "First Name": nb.guest_first_name,
            "Gender": nb.gender,
            "Date of Birth": nb.date_of_birth,
            "Document Number": nb.passport_num,
            "Document Expiration": nb.passport_expiry,
            "IIN": nb.guest_iin,
            "client_phone": nb.client_phone,
            "passport_image_path": nb.passport_image_path
        })
    saved_rows = await save_group_booking(persons, common_data, new_booking.placement_type or 'separate')
    if saved_rows:
        for i, bid in enumerate(new_ids):
            if i < len(saved_rows):
                await update_booking_row(bid, saved_rows[i])
            await update_booking_fields(bid, {"status": "new"})
    else:
        # Rollback: откатываем статус старой брони и отклоняем запрос
        for ob in old_bookings:
            await update_booking_fields(ob.id, {"status": "new"})
        await update_approval_status(req_id, "rejected")
        await delete_admin_request_inbox(req_id)
        await call.message.edit_text("❌ Не удалось записать новую бронь в таблицу", reply_markup=admin_kb(), parse_mode="HTML")
        return

    # Обработка старой брони (очистка из таблицы)
    cleanup_failed = False
    cleanup_failed_bookings = []  # 🔥 Храним брони которые не удалось очистить

    for idx, ob in enumerate(old_bookings):
        if ob.sheet_row_number and ob.table_id and ob.sheet_name:
            old_guest_name = f"{ob.guest_last_name} {ob.guest_first_name}"
            try:
                cleared = await clear_booking_in_sheets(
                    ob.table_id,
                    ob.sheet_name,
                    ob.sheet_row_number,
                    ob.package_name,
                    expected_guest_name=old_guest_name,  # 🔒 Проверяем имя перед удалением
                )
                if cleared:
                    print(f"✅ Старая бронь #{ob.id} ({old_guest_name}) очищена из таблицы")
                    # ✅ Только если успешно очистили - отмечаем как перенесённую
                    target_new = new_ids[idx] if idx < len(new_ids) else new_ids[0]
                    await mark_booking_rescheduled(ob.id, comment=f"Перенесено в #{target_new}")
                else:
                    # 🔍 Ищем паломника по всему пакету
                    print(f"⚠️ Имя на строке {ob.sheet_row_number} не совпадает, ищем по пакету...")
                    matches = await find_pilgrim_in_package(
                        ob.table_id,
                        ob.sheet_name,
                        ob.package_name,
                        old_guest_name
                    )
                    if matches:
                        # Нашли - показываем где и предлагаем выбрать
                        cleanup_failed = True
                        cleanup_failed_bookings.append((ob.id, idx, matches))
                    else:
                        # Не нашли вообще
                        cleanup_failed = True
                        cleanup_failed_bookings.append((ob.id, idx, None))
            except Exception as e:
                print(f"❌ ОШИБКА при очистке старой брони #{ob.id}: {e}")
                cleanup_failed = True
                cleanup_failed_bookings.append((ob.id, idx, None))
        else:
            # Если нет данных для очистки из Sheets - отмечаем как перенесённую
            target_new = new_ids[idx] if idx < len(new_ids) else new_ids[0]
            await mark_booking_rescheduled(ob.id, comment=f"Перенесено в #{target_new}")

    # 🔥 Если были ошибки очистки - показываем варианты
    if cleanup_failed:
        # Проверяем есть ли найденные паломники
        found_any = any(item[2] for item in cleanup_failed_bookings if len(item) > 2)

        if found_any:
            # Есть найденные - показываем кнопки для выбора
            buttons = []
            info_lines = []

            for item in cleanup_failed_bookings:
                bid = item[0]
                idx = item[1]
                matches = item[2] if len(item) > 2 else None
                b = await get_booking_by_id(bid)

                if b and matches:
                    guest_name = f"{b.guest_last_name} {b.guest_first_name}"
                    info_lines.append(f"<b>{guest_name}</b> (строка {b.sheet_row_number} в БД):")
                    for found_row, found_name in matches[:3]:
                        buttons.append([InlineKeyboardButton(
                            text=f"✅ Очистить строку {found_row}: {found_name}",
                            callback_data=f"admin_resched_row:{req_id}:{bid}:{found_row}:{idx}"
                        )])
                        info_lines.append(f"  • Найден в строке {found_row}")
                elif b:
                    guest_name = f"{b.guest_last_name} {b.guest_first_name}"
                    info_lines.append(f"<b>{guest_name}</b> - не найден в пакете")

            buttons.append([InlineKeyboardButton(
                text="⏭ Пропустить очистку",
                callback_data=f"admin_resched_skip:{req_id}"
            )])
            buttons.append([InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="admin_menu"
            )])

            found_keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            await call.message.edit_text(
                f"🔍 <b>Перенос: паломники найдены в других строках!</b>\n\n"
                f"✅ Новые брони созданы: {', '.join([str(x) for x in new_ids])}\n\n"
                f"⚠️ Старые брони не на указанных строках:\n" +
                "\n".join(info_lines) +
                f"\n\n<b>Выберите строки для очистки или пропустите:</b>",
                reply_markup=found_keyboard,
                parse_mode="HTML"
            )
        else:
            # Не нашли никого - показываем ошибку
            failed_info = []
            for item in cleanup_failed_bookings:
                bid = item[0]
                b = await get_booking_by_id(bid)
                if b:
                    failed_info.append(f"#{bid} ({b.guest_last_name} {b.guest_first_name}) - строка {b.sheet_row_number}")

            error_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="⏭ Пропустить очистку (завершить перенос)",
                    callback_data=f"admin_resched_skip:{req_id}"
                )],
                [InlineKeyboardButton(
                    text="🔙 Назад к меню",
                    callback_data="admin_menu"
                )],
            ])

            await call.message.edit_text(
                f"⚠️ <b>Перенос частично выполнен</b>\n\n"
                f"✅ Новые брони созданы: {', '.join([str(x) for x in new_ids])}\n"
                f"❌ НО: Не удалось найти старые брони в таблице\n\n"
                f"<b>Проблемные брони:</b>\n" + "\n".join(failed_info) + "\n\n"
                f"Паломники не найдены ни на указанных строках, ни в других местах пакета.\n"
                f"Возможно данные уже удалены.",
                reply_markup=error_keyboard,
                parse_mode="HTML"
            )
        return

    await update_approval_status(req_id, "approved")
    await delete_admin_request_inbox(req_id)

    text = (
        f"♻️ <b>Перенос одобрен</b>\n"
        f"Пакет: {new_booking.package_name}\n"
        f"Новые: {', '.join([str(x) for x in new_ids])}\n"
        f"Старые: {', '.join([str(x) for x in old_ids]) if old_ids else '-'}\n"
        f"Строки: {', '.join([str(x) for x in saved_rows])}"
    )
    await call.message.edit_text(text, reply_markup=admin_kb(), parse_mode="HTML")
    try:
        group_members = (new_booking.group_members or []) if new_booking else []
        if old_ids and len(old_ids) == len(new_ids) == 1:
            pilgrim_name = (group_members[0] if group_members else f"{new_booking.guest_last_name} {new_booking.guest_first_name}").strip()
            await bot.send_message(
                req.initiator_id,
                f"✅ Перенос паломника(-ов) \"{pilgrim_name}\" одобрен админом.\nНовые: {new_ids[0]}"
            )
        else:
            names = ", ".join([str(x).strip() for x in group_members if str(x).strip()]) or "-"
            await bot.send_message(
                req.initiator_id,
                f"✅ Перенос группы одобрен админом.\nПаломники: {names}\nНовые: {', '.join([str(x) for x in new_ids])}"
            )
    except: pass


@router.callback_query(F.data.startswith("admin_resched_reject:"))
async def admin_resched_reject(call: CallbackQuery):
    # Проверка прав доступа
    role = await get_user_role(call.from_user.id)
    if role != "admin":
        await call.answer("❌ Только администраторы могут отклонять перенос", show_alert=True)
        return

    req_id = int(call.data.split(":")[1])
    req = await get_approval_request(req_id)
    if not req or req.status != "pending":
        await call.answer("Заявка не найдена или уже обработана", show_alert=True)
        return
    new_booking = await get_booking_by_id(req.booking_id)
    old_ids = []
    new_ids = []
    if req.comment:
        try:
            import json as _json
            parsed = _json.loads(req.comment)
            if isinstance(parsed, dict) and ("old_booking_ids" in parsed or "new_booking_ids" in parsed):
                old_ids = [int(x) for x in (parsed.get("old_booking_ids") or []) if int(x) > 0]
                new_ids = [int(x) for x in (parsed.get("new_booking_ids") or []) if int(x) > 0]
        except Exception:
            pass
    if not new_ids and new_booking:
        new_ids = [new_booking.id]
    if not old_ids and req.comment and req.comment.startswith("old:"):
        try:
            old_ids = [int(req.comment.split("old:")[1])]
        except Exception:
            old_ids = []

    for bid in new_ids:
        await update_booking_fields(bid, {"status": "cancelled"})
    for oid in old_ids:
        await update_booking_fields(oid, {"status": "new"})

    await update_approval_status(req_id, "rejected")
    await delete_admin_request_inbox(req_id)
    await call.message.edit_text("❌ Перенос отклонен.", reply_markup=admin_kb(), parse_mode="HTML")
    try:
        if old_ids and len(old_ids) == 1:
            await bot.send_message(req.initiator_id, f"❌ Перенос брони #{old_ids[0]} отклонен админом.")
        else:
            await bot.send_message(req.initiator_id, "❌ Перенос группы отклонен админом.")
    except: pass

@router.message(Command("wipe_database_secret_123"))
async def hard_reset_db(message: Message):
    # Защита: только для вас (вставьте свой ID)
    MY_ID = 489877724
    if message.from_user.id != MY_ID:
        return

    await message.answer("⚠️ <b>НАЧИНАЮ ПОЛНЫЙ СБРОС БАЗЫ...</b>")

    try:
        async with engine.begin() as conn:
            # 1. Удаляем все таблицы (DROP)
            await conn.run_sync(Base.metadata.drop_all)
            # 2. Создаем заново (CREATE)
            await conn.run_sync(Base.metadata.create_all)

        await message.answer("💥 <b>База данных полностью стерта и пересоздана!</b>\nВсе данные удалены. Структура обновлена.")
    except Exception as e:
        await message.answer(f"❌ Ошибка сброса: {e}")


@router.message(Command("toggle_notify_cancel"))
async def toggle_notify_cancel(message: Message):
    """Вкл/выкл уведомления об отменах для админа"""
    role = await get_user_role(message.from_user.id)
    if role != "admin":
        return
    settings = await get_admin_settings(message.from_user.id)
    current = settings.notify_cancel if settings else 0
    new_val = not bool(current)
    await set_admin_settings(message.from_user.id, notify_cancel=new_val)
    state = "включены" if new_val else "выключены"
    await message.answer(f"🔔 Уведомления об отменах {state}.")


@router.message(Command("toggle_notify_resched"))
async def toggle_notify_resched(message: Message):
    """Вкл/выкл уведомления о переносах для админа"""
    role = await get_user_role(message.from_user.id)
    if role != "admin":
        return
    settings = await get_admin_settings(message.from_user.id)
    current = settings.notify_reschedule if settings else 0
    new_val = not bool(current)
    await set_admin_settings(message.from_user.id, notify_reschedule=new_val)
    state = "включены" if new_val else "выключены"
    await message.answer(f"🔔 Уведомления о переносах {state}.")


@router.callback_query(F.data == "admin_menu")
async def show_admin_main_menu(call: CallbackQuery):
    """Главное админское меню"""
    # Используем единое меню из config/keyboards.py, чтобы кнопки не "пропадали" после возврата
    from bull_project.bull_bot.config.keyboards import admin_kb
    kb = admin_kb()

    await call.message.edit_text(
        "<b>🕋 Ассаламу алейкум! Админ Меню</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_notify_menu")
async def admin_notify_menu(call: CallbackQuery):
    settings = await get_admin_settings(call.from_user.id)
    notify_new = bool(settings.notify_new) if settings else False
    notify_cancel = bool(settings.notify_cancel) if settings else False
    notify_resched = bool(settings.notify_reschedule) if settings else False

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"Новые брони: {'✅' if notify_new else '❌'}",
            callback_data=f"toggle_notify:new:{int(notify_new)}"
        )],
        [InlineKeyboardButton(
            text=f"Отмены: {'✅' if notify_cancel else '❌'}",
            callback_data=f"toggle_notify:cancel:{int(notify_cancel)}"
        )],
        [InlineKeyboardButton(
            text=f"Переносы: {'✅' if notify_resched else '❌'}",
            callback_data=f"toggle_notify:resched:{int(notify_resched)}"
        )],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
    ])
    await call.message.edit_text("🔔 Настройки уведомлений", reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("toggle_notify:"))
async def toggle_notify(call: CallbackQuery):
    _, kind, current = call.data.split(":")
    current_val = int(current)
    new_val = not bool(current_val)
    if kind == "new":
        await set_admin_settings(call.from_user.id, notify_new=new_val)
    elif kind == "cancel":
        await set_admin_settings(call.from_user.id, notify_cancel=new_val)
    elif kind == "resched":
        await set_admin_settings(call.from_user.id, notify_reschedule=new_val)
    await call.answer("Сохранено")
    await admin_notify_menu(call)
