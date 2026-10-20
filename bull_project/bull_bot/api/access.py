"""Authenticate API calls before any database or Sheets mutation."""
import base64
import hashlib
import hmac
import json
import os
import re
import time
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from bull_project.bull_bot.core.access import telegram_user_id, has_access, ACCESS_MESSAGE, upload_user_id
from bull_project.bull_bot.database import requests as db

router = APIRouter()
MEDIA_PATH = re.compile(r"^/api/care/passport-(?:photo|original|pdf)/[0-9]+$")


def denied(status, text, code):
    return JSONResponse(status_code=status, content={"ok": False, "success": False,
                        "error": text, "detail": text, "code": code})


def media_signature(value):
    return hmac.new(os.environ["API_TOKEN"].strip().encode(), b"media:" + value.encode(), hashlib.sha256).hexdigest()


@router.get("/api/access/media-token")
async def media_token(request: Request, path: str):
    if not MEDIA_PATH.fullmatch(path):
        return denied(400, "Недопустимый адрес файла", "invalid_media_path")
    # Check ownership here too, so a manager cannot mint links for somebody else.
    if request.state.user.role == "manager":
        booking = await db.get_booking_by_id(int(path.rsplit("/", 1)[1]))
        if not booking or booking.manager_id != request.state.user.telegram_id:
            return denied(403, "Нет доступа к этой брони", "forbidden")
    payload = json.dumps([request.state.user.telegram_id, int(time.time()) + 120, path])
    value = base64.urlsafe_b64encode(payload.encode()).decode()
    return {"token": value + "." + media_signature(value)}


def media_user_id(token, path):
    value, signature = token.split(".", 1)
    if not hmac.compare_digest(signature, media_signature(value)):
        raise ValueError("Invalid token")
    uid, expiry, expected_path = json.loads(base64.urlsafe_b64decode(value))
    if expected_path != path or expiry < time.time():
        raise ValueError("Expired token")
    return uid


async def api_access_guard(request, call_next):
    path = request.url.path
    if not path.startswith("/api/") or request.method == "OPTIONS":
        return await call_next(request)
    try:
        token = request.query_params.get("access_token")
        upload_token = request.headers.get("X-Bot-Upload-Token")
        if upload_token and request.method == "POST" and path == "/api/passports/upload":
            uid = upload_user_id(upload_token)
        elif token and request.method == "GET" and MEDIA_PATH.fullmatch(path):
            uid = media_user_id(token, path)
        else:
            uid = telegram_user_id(request.headers.get("X-Telegram-Init-Data", ""))
    except (ValueError, TypeError, KeyError):
        return denied(401, "Откройте форму заново через Telegram-бота.", "telegram_auth_required")
    user = await db.get_user_by_id(uid)
    if not has_access(user):
        return denied(403, ACCESS_MESSAGE, "access_expired")
    request.state.user = user
    if path.startswith("/api/admin/") and user.role != "admin":
        return denied(403, "Доступ разрешён только администратору", "forbidden")
    if path.startswith("/api/care/") and not MEDIA_PATH.fullmatch(path) and user.role not in ("admin", "care"):
        return denied(403, "Нет доступа к сопровождению", "forbidden")

    body = {}
    if request.method in ("POST", "PATCH", "DELETE") and "application/json" in request.headers.get("content-type", ""):
        try:
            body = await request.json()
            if not isinstance(body, dict):
                return denied(400, "Ожидается JSON объект", "invalid_request")
        except ValueError:
            return denied(400, "Некорректный JSON", "invalid_request")
    # Identity is always the signed Telegram account, even for administrators.
    for key in ("manager_id", "initiator_id"):
        if body.get(key) is not None:
            try:
                if int(body[key]) != uid:
                    return denied(403, "Нельзя действовать от имени другого пользователя", "forbidden")
            except (ValueError, TypeError):
                return denied(400, "Некорректный идентификатор", "invalid_request")
    if user.role == "manager":
        history = re.fullmatch(r"/api/history/([0-9]+)", path)
        if history and int(history[1]) != uid:
            return denied(403, "Нет доступа к чужой истории", "forbidden")
        if path == "/api/open-date/list":
            if request.query_params.get("manager_id") != str(uid):
                return denied(403, "Укажите свой профиль", "forbidden")
        if path == "/api/open-date/search":
            return denied(403, "Поиск доступен сопровождению", "forbidden")
        ids = []
        match = re.fullmatch(r"/api/bookings/([0-9]+)(?:/cancel)?", path)
        media = MEDIA_PATH.fullmatch(path)
        if match:
            ids.append(int(match[1]))
        if media:
            ids.append(int(path.rsplit("/", 1)[1]))
        for key in ("booking_id", "old_booking_id"):
            if body.get(key) is not None:
                ids.append(body[key])
        old_ids = body.get("old_booking_ids") or []
        if not isinstance(old_ids, list):
            return denied(400, "Некорректный список броней", "invalid_request")
        ids.extend(old_ids)
        for booking_id in ids:
            try:
                booking = await db.get_booking_by_id(int(booking_id))
            except (ValueError, TypeError):
                return denied(400, "Некорректный номер брони", "invalid_request")
            if not booking or booking.manager_id != uid:
                return denied(403, "Нет доступа к этой брони", "forbidden")
        match = re.fullmatch(r"/api/open-date/(?:convert/)?([0-9]+)", path)
        if match:
            booking = await db.get_open_date_booking_by_id(int(match[1]))
            if not booking or booking.manager_id != uid:
                return denied(403, "Нет доступа к этой брони", "forbidden")
    return await call_next(request)
