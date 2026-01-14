
import os
import re
import aiohttp
from typing import List, Optional
from fastapi import WebSocket
from datetime import datetime

phone_subscribers: List[WebSocket] = []
admin_request_subscribers: List[WebSocket] = []


def extract_departure_date(package_name: str) -> str:
    """
    Извлекает первую дату из названия пакета.
    Примеры:
        "31.01-07.02 NIYET econom" -> "31.01"
        "15.03-22.03 Умра" -> "15.03"
    """
    if not package_name or package_name == "-":
        return "-"

    # Ищем паттерн DD.MM в начале строки
    match = re.match(r'(\d{1,2}\.\d{1,2})', package_name.strip())
    if match:
        return match.group(1)

    return "-"


async def notify_phone_subscribers(
    phone: str,
    booking_id: int,
    guest_name: str,
    package_name: str = "-",
    group_size: int = 1,
    group_members: list = None,
    room_type: str = "-",
    manager_name: str = "-",
    departure_city: str = "-",
    comment: str = "-",
    price: str = "0",
    visa_status: str = "-",
    avia: str = "-",
    gender: str = "M"
):
    if not phone or phone == "-":
        return

    # Извлекаем дату вылета из названия пакета
    departure_date = extract_departure_date(package_name)

    message = {
        "event": "new_phone",
        "phone": phone,
        "booking_id": booking_id,
        "guest_name": guest_name,
        "timestamp": datetime.now().isoformat(),

        "departure_date": departure_date,
        "package_name": package_name,
        "departure_city": departure_city,

        "room_type": room_type,
        "gender": gender,

        "group_size": group_size,
        "group_members": group_members or [guest_name],

        "manager_name": manager_name,

        "comment": comment,
        "price": price,
        "visa_status": visa_status,
        "avia": avia,
    }

    disconnected = []
    for ws in phone_subscribers:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        phone_subscribers.remove(ws)

    if phone_subscribers:
        print(f"\n{'='*60}")
        print(f"📱 NEW PHONE RECEIVED!")
        print(f"{'='*60}")
        print(f"   Phone:      {phone}")
        print(f"   Guest:      {guest_name}")
        print(f"   Booking ID: {booking_id}")
        print(f"   Timestamp:  {message['timestamp']}")
        print(f"\n   Date:       {departure_date}")
        print(f"   Package:    {package_name}")
        print(f"   Departure:  {departure_city}")
        print(f"   Room:       {room_type}")
        print(f"   Manager:    {manager_name}")
        if group_size > 1:
            print(f"   Group:      {group_size} persons")
        if comment and comment != '-':
            print(f"   Comment:    {comment}")
        print(f"{'='*60}\n")


async def notify_admin_request_subscribers(request_data: dict):
    if not request_data:
        return

    message = {
        "event": "new_admin_request",
        "request_id": request_data.get("request_id"),
        "booking_id": request_data.get("booking_id"),
        "request_type": request_data.get("request_type"),  # "cancel" or "reschedule"
        "guest_name": request_data.get("guest_name"),
        "package_name": request_data.get("package_name"),
        "manager_name": request_data.get("manager_name"),
        "comment": request_data.get("comment"),
        "timestamp": datetime.now().isoformat()
    }

    disconnected = []
    for ws in admin_request_subscribers:
        try:
            await ws.send_json(message)
            print(f"🔔 Отправлено уведомление о заявке #{request_data.get('request_id')} админу")
        except Exception:
            disconnected.append(ws)

    # Очистка отключенных клиентов
    for ws in disconnected:
        admin_request_subscribers.remove(ws)


async def send_telegram_notification(
    chat_id: int,
    text: str,
    reply_markup: Optional[dict] = None,
    parse_mode: str = "HTML"
) -> dict:
    bot_token = os.getenv("API_TOKEN")
    if not bot_token or bot_token.startswith("your_"):
        print(f"⚠️ API_TOKEN не настроен, уведомление не отправлено")
        return {"ok": False, "error": "No token"}

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                result = await response.json()
                if result.get("ok"):
                    print(f"✅ Telegram уведомление отправлено админу {chat_id}")
                else:
                    print(f"⚠️ Ошибка отправки Telegram: {result.get('description')}")
                return result
    except Exception as e:
        print(f"❌ Ошибка HTTP запроса к Telegram API: {e}")
        return {"ok": False, "error": str(e)}


def format_admin_notification(
    notification_type: str,
    booking_data: dict,
    request_data: Optional[dict] = None
) -> str:
    guest_last_name = booking_data.get('guest_last_name', '')
    guest_first_name = booking_data.get('guest_first_name', '')
    guest_name = f"{guest_last_name} {guest_first_name}".strip() or "-"

    # Заголовок в зависимости от типа
    if notification_type == "new_booking":
        header = "🟢 НОВАЯ БРОНЬ"
    elif notification_type == "cancel":
        header = "🛑 ЗАПРОС НА ОТМЕНУ"
    elif notification_type == "reschedule":
        header = "🔵 ЗАПРОС НА ПЕРЕНОС"
    else:
        header = "📋 УВЕДОМЛЕНИЕ"

    # Начало сообщения
    text = f"{header}\n\n"
    text += f"ФИО: {guest_name}\n\n"

    # Информация о пакете
    if notification_type == "reschedule" and request_data:
        old_package = request_data.get('old_package_name', '-')
        text += f"▫️ Старый пакет: {old_package}\n"
        text += f"▫️ Новый пакет: {booking_data.get('package_name', '-')}\n"
        sheet_row = booking_data.get('sheet_row_number', '-')
        if sheet_row is None:
            sheet_row = "-"
        text += f"▫️ Новый лист: {booking_data.get('sheet_name', '-')} | Строка: {sheet_row}\n"
    else:
        sheet_row = booking_data.get('sheet_row_number', '-')
        if sheet_row is None:
            sheet_row = "-"
        text += f"▫️ Пакет: {booking_data.get('package_name', '-')}\n"
        text += f"▫️ Лист: {booking_data.get('sheet_name', '-')} | Строка: {sheet_row}\n"

    text += f"▫️ Телефон: {booking_data.get('client_phone', '-')}\n"

    # Размещение и финансы
    room_type = booking_data.get('room_type', '-')
    meal_type = booking_data.get('meal_type', '-')
    text += f"▫️ Размещение: {room_type} | {meal_type}\n"

    price = booking_data.get('price', '-')
    amount_paid = booking_data.get('amount_paid', '-')
    text += f"▫️ Сумма: {price}\n"
    text += f"▫️ Сумма оплаты: {amount_paid}\n"

    # Логистика
    region = booking_data.get('region', '-')
    departure_city = booking_data.get('departure_city', '-')
    text += f"▫️ Регион: {region} | Вылет: {departure_city}\n"

    visa_status = booking_data.get('visa_status', '-')
    avia = booking_data.get('avia', '-')
    text += f"▫️ Виза: {visa_status} | Авиа: {avia}\n"

    # Менеджер
    manager_name = booking_data.get('manager_name_text', '-')
    text += f"▫️ Менеджер: {manager_name}\n"

    # Блок ЗАЯВКА (только для cancel/reschedule)
    if request_data and notification_type in ["cancel", "reschedule"]:
        text += "\n━━━ ЗАЯВКА ━━━\n"
        text += f" Менеджер: {manager_name}\n"

        request_comment = request_data.get('comment', '')
        if request_comment:
            text += f"▫️ Комментарий: {request_comment}\n"

        if notification_type == "reschedule":
            old_booking_ids = request_data.get('old_booking_ids') or []
            if not old_booking_ids:
                old_booking_id = request_data.get('old_booking_id', '')
                if old_booking_id:
                    old_booking_ids = [old_booking_id]
            if old_booking_ids:
                if len(old_booking_ids) == 1:
                    text += f"▫️ Старая бронь: #{old_booking_ids[0]}\n"
                else:
                    joined = ", ".join([f"#{x}" for x in old_booking_ids])
                    text += f"▫️ Старые брони: {joined}\n"

        request_date = request_data.get('request_date', '')
        if request_date:
            text += f"▫️ Дата заявки: {request_date}\n"

    return text


async def notify_admins_about_request(
    request_id: int,
    booking_id: int,
    request_type: str,
    booking_data: dict,
    initiator_id: int,
    comment: str = None
):
    """
    Отправляет уведомления админам о новой заявке на отмену/перенос.
    Проверяет настройки каждого админа и отправляет только тем, у кого включены уведомления.

    Args:
        request_id: ID заявки
        booking_id: ID брони
        request_type: "cancel" или "reschedule"
        booking_data: Данные брони (dict с полями package_name, guest_last_name, guest_first_name и т.д.)
        initiator_id: ID менеджера/пользователя который создал заявку
        comment: Комментарий к заявке
    """
    print(f"\n{'='*60}")
    print(f"🔔 notify_admins_about_request вызвана!")
    print(f"{'='*60}")
    print(f"   Request ID:   {request_id}")
    print(f"   Booking ID:   {booking_id}")
    print(f"   Request type: {request_type}")
    print(f"   Initiator ID: {initiator_id}")
    print(f"   Comment:      {comment}")
    print(f"   Booking data: {booking_data}")
    print(f"{'='*60}\n")

    try:
        # Импортируем функции для работы с БД
        from bull_project.bull_bot.database.requests import get_admin_ids, get_admin_settings

        admin_ids = await get_admin_ids()
        print(f"📋 Найдено админов: {len(admin_ids)} - {admin_ids}")

        # Подготавливаем данные заявки
        request_data = {
            'comment': comment,
            'request_date': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'old_booking_id': booking_data.get('old_booking_id', ''),  # backward compat
            'old_booking_ids': booking_data.get('old_booking_ids', [])  # Для reschedule (group)
        }

        # Форматируем текст уведомления используя единую функцию
        text = format_admin_notification(
            notification_type=request_type,
            booking_data=booking_data,
            request_data=request_data
        )

        # Кнопки для подтверждения/отклонения (callback_data должны совпадать с handlers/admin_handlers.py)
        button_text_confirm = "✅ Подтвердить отмену" if request_type == "cancel" else "✅ Подтвердить перенос"
        button_text_reject = "❌ Отклонить"

        if request_type == "cancel":
            cb_ok = f"admin_cancel_ok:{request_id}"
            cb_reject = f"admin_cancel_reject:{request_id}"
        elif request_type == "reschedule":
            # Исторически в боте используются admin_resched_ok/admin_resched_reject
            cb_ok = f"admin_resched_ok:{request_id}"
            cb_reject = f"admin_resched_reject:{request_id}"
        else:
            cb_ok = f"admin_{request_type}_ok:{request_id}"
            cb_reject = f"admin_{request_type}_reject:{request_id}"

        inline_keyboard = [[
            {"text": button_text_confirm, "callback_data": cb_ok},
            {"text": button_text_reject, "callback_data": cb_reject},
        ]]

        reply_markup = {"inline_keyboard": inline_keyboard}

        # Отправляем уведомления админам
        for admin_id in admin_ids:
            try:
                print(f"\n   Обработка админа {admin_id}...")

                # 🔧 ВРЕМЕННО: отправляем только одному админу для тестирования
                if admin_id != 8413412150:
                    print(f"   ⏭️  Пропущен (не тестовый админ)")
                    continue

                print(f"   ✅ Тестовый админ - продолжаем")

                settings = await get_admin_settings(admin_id)
                print(f"   📊 Настройки: new={settings.notify_new}, cancel={settings.notify_cancel}, reschedule={settings.notify_reschedule}")

                # Проверяем настройки уведомлений
                if request_type == "cancel" and not settings.notify_cancel:
                    print(f"   ℹ️ Админ {admin_id} отключил уведомления об отменах")
                    continue
                elif request_type == "reschedule" and not settings.notify_reschedule:
                    print(f"   ℹ️ Админ {admin_id} отключил уведомления о переносах")
                    continue

                print(f"   📤 Отправка Telegram уведомления...")

                # Отправляем через HTTP API
                result = await send_telegram_notification(
                    chat_id=admin_id,
                    text=text,
                    reply_markup=reply_markup
                )

                print(f"   📬 Результат отправки: {result}")

            except Exception as e:
                print(f"   ⚠️ Ошибка отправки уведомления админу {admin_id}: {e}")
                import traceback
                traceback.print_exc()
                continue

        print(f"🔔 Уведомления о заявке #{request_id} отправлены админам")

    except Exception as e:
        print(f"❌ Ошибка в notify_admins_about_request: {e}")
        import traceback
        traceback.print_exc()


async def notify_admins_about_new_booking(booking_data: dict):
    """
    Отправляет уведомления админам о новой брони.
    Проверяет настройки каждого админа и отправляет только тем, у кого включены уведомления.

    Args:
        booking_data: Данные брони (dict с полями package_name, guest_last_name, guest_first_name и т.д.)
    """
    try:
        # Импортируем функции для работы с БД
        from bull_project.bull_bot.database.requests import get_admin_ids, get_admin_settings

        admin_ids = await get_admin_ids()

        # Форматируем текст уведомления используя единую функцию
        text = format_admin_notification(
            notification_type="new_booking",
            booking_data=booking_data,
            request_data=None
        )

        # Уведомления о новых бронях без кнопок (информационные)
        # Отправляем уведомления админам
        for admin_id in admin_ids:
            try:
                # 🔧 ВРЕМЕННО: отправляем только одному админу для тестирования
                if admin_id != 8413412150:
                    continue

                settings = await get_admin_settings(admin_id)

                # Проверяем настройки уведомлений (используем notify_new)
                if not settings.notify_new:
                    print(f"ℹ️ Админ {admin_id} отключил уведомления о новых бронях")
                    continue

                # Отправляем через HTTP API (без кнопок)
                await send_telegram_notification(
                    chat_id=admin_id,
                    text=text,
                    reply_markup=None
                )

            except Exception as e:
                print(f"⚠️ Ошибка отправки уведомления админу {admin_id}: {e}")
                continue

        booking_id = booking_data.get('id', '?')
        print(f"🔔 Уведомления о новой брони #{booking_id} отправлены админам")

    except Exception as e:
        print(f"❌ Ошибка в notify_admins_about_new_booking: {e}")
        import traceback
        traceback.print_exc()
