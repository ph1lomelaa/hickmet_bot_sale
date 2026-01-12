"""
WebSocket менеджер для отправки уведомлений.
Хранит списки подписчиков и функции для отправки уведомлений.
"""
from typing import List
from fastapi import WebSocket
from datetime import datetime


# Глобальные списки подписчиков
phone_subscribers: List[WebSocket] = []
admin_request_subscribers: List[WebSocket] = []


async def notify_phone_subscribers(phone: str, booking_id: int, guest_name: str):
    """Отправляет уведомление о новом телефоне всем подключенным WebSocket клиентам"""
    if not phone or phone == "-":
        return

    message = {
        "event": "new_phone",
        "phone": phone,
        "booking_id": booking_id,
        "guest_name": guest_name,
        "timestamp": datetime.now().isoformat()
    }

    disconnected = []
    for ws in phone_subscribers:
        try:
            await ws.send_json(message)
            print(f"📱 Отправлен телефон {phone} WebSocket клиенту")
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
