from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from bull_project.bull_bot.core.websocket_manager import (
    phone_subscribers,
    admin_request_subscribers,
)


from bull_project.bull_bot.core.access import telegram_user_id, has_access
from bull_project.bull_bot.database.requests import get_user_by_id

router = APIRouter()


async def allow_socket(websocket, roles):
    try:
        uid = telegram_user_id(websocket.query_params.get("init_data", ""))
        user = await get_user_by_id(uid)
        if has_access(user) and user.role in roles:
            return True
    except ValueError:
        pass
    await websocket.close(code=1008)
    return False


@router.websocket("/ws/phones")
async def websocket_phone_updates(websocket: WebSocket):
    """WebSocket endpoint - клиенты подключаются сюда для получения новых телефонов мгновенно."""
    if not await allow_socket(websocket, ("admin", "care")):
        return
    await websocket.accept()
    phone_subscribers.append(websocket)
    print(f"📱 WebSocket клиент подключен. Всего подписчиков: {len(phone_subscribers)}")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        phone_subscribers.remove(websocket)
        print(f"📱 WebSocket клиент отключился. Всего подписчиков: {len(phone_subscribers)}")


@router.websocket("/ws/admin-requests")
async def websocket_admin_requests(websocket: WebSocket):
    """WebSocket endpoint - админы подключаются для получения уведомлений о заявках."""
    if not await allow_socket(websocket, ("admin",)):
        return
    await websocket.accept()
    admin_request_subscribers.append(websocket)
    print(f"🔔 WebSocket админ подключен. Всего подписчиков: {len(admin_request_subscribers)}")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        admin_request_subscribers.remove(websocket)
        print(f"🔔 WebSocket админ отключился. Всего подписчиков: {len(admin_request_subscribers)}")
