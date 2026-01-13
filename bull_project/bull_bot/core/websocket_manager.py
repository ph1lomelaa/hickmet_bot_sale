
import os
import aiohttp
from typing import List, Optional
from fastapi import WebSocket
from datetime import datetime

phone_subscribers: List[WebSocket] = []
admin_request_subscribers: List[WebSocket] = []


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
    """Отправляет уведомление о новом телефоне всем подключенным WebSocket клиентам"""
    if not phone or phone == "-":
        return

    message = {
        "event": "new_phone",
        "phone": phone,
        "booking_id": booking_id,
        "guest_name": guest_name,
        "timestamp": datetime.now().isoformat(),

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
            print(f"📱 Отправлен телефон {phone} WebSocket клиенту (пакет: {package_name})")
        except Exception:
            disconnected.append(ws)

    # Очистка отключенных клиентов
    for ws in disconnected:
        phone_subscribers.remove(ws)


async def notify_admin_request_subscribers(request_data: dict):
    """Отправляет уведомление о новой заявке всем подключенным админам"""
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
    """
    Отправка уведомления напрямую через Telegram Bot API без aiogram.
    Работает даже когда SKIP_BOT=true.
    """
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
    try:
        # Импортируем функции для работы с БД
        from bull_project.bull_bot.database.requests import get_admin_ids, get_admin_settings

        admin_ids = await get_admin_ids()

        # Формируем текст уведомления
        type_emoji = "🛑" if request_type == "cancel" else "♻️"
        type_text = "Запрос на отмену" if request_type == "cancel" else "Запрос на перенос"

        guest_name = f"{booking_data.get('guest_last_name', '')} {booking_data.get('guest_first_name', '')}".strip() or "-"
        package_name = booking_data.get('package_name', '-')
        phone = booking_data.get('client_phone', '-')
        manager_name = booking_data.get('manager_name_text', '-')

        text = f"{type_emoji} <b>{type_text}</b>\n\n"
        text += f"📋 Бронь: <b>#{booking_id}</b>\n"
        text += f"📦 Пакет: {package_name}\n"
        text += f"👤 Гость: {guest_name}\n"
        text += f"📱 Телефон: {phone}\n"
        text += f"👔 Менеджер: {manager_name}\n"
        text += f"🆔 Инициатор: {initiator_id}\n"

        if comment:
            text += f"💬 Комментарий: {comment}\n"

        # Кнопки для подтверждения/отклонения
        inline_keyboard = [
            [
                {
                    "text": "✅ Подтвердить",
                    "callback_data": f"admin_{'cancel' if request_type == 'cancel' else 'reschedule'}_ok:{request_id}"
                },
                {
                    "text": "❌ Отклонить",
                    "callback_data": f"admin_{'cancel' if request_type == 'cancel' else 'reschedule'}_reject:{request_id}"
                }
            ]
        ]

        reply_markup = {"inline_keyboard": inline_keyboard}

        # Отправляем уведомления админам
        for admin_id in admin_ids:
            try:
                settings = await get_admin_settings(admin_id)

                # Проверяем настройки уведомлений
                if request_type == "cancel" and not settings.notify_cancel:
                    print(f"ℹ️ Админ {admin_id} отключил уведомления об отменах")
                    continue
                elif request_type == "reschedule" and not settings.notify_reschedule:
                    print(f"ℹ️ Админ {admin_id} отключил уведомления о переносах")
                    continue

                # Отправляем через HTTP API
                await send_telegram_notification(
                    chat_id=admin_id,
                    text=text,
                    reply_markup=reply_markup
                )

            except Exception as e:
                print(f"⚠️ Ошибка отправки уведомления админу {admin_id}: {e}")
                continue

        print(f"🔔 Уведомления о заявке #{request_id} отправлены админам")

    except Exception as e:
        print(f"❌ Ошибка в notify_admins_about_request: {e}")
        import traceback
        traceback.print_exc()
