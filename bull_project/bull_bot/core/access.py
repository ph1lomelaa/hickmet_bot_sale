"""Shared access policy. Password rotation never deletes users or bookings."""
import hashlib
import hmac
import json
import os
import time
from urllib.parse import parse_qsl

ACCESS_MESSAGE = "Ассалям алейкум! Пароль доступа обновлён. Пожалуйста, вернитесь в бот, нажмите /start и введите новый пароль. Ваш профиль, брони и история сохранены."
REAUTH_MESSAGE = (
    "🕋 Ассалям алейкум!\n\n"
    "Мы обновили пароль доступа. Пожалуйста, войдите заново, чтобы продолжить работу.\n\n"
    "Ваш профиль, все брони и история сохранены.\n\n"
    "Нажмите «🔑 Ввести пароль» и отправьте новый пароль следующим сообщением."
)


def reauth_keyboard():
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔑 Ввести пароль", callback_data="access:enter_password")
    ]])


def manager_access_version():
    password = os.getenv("MANAGER_PASSWORD", "")
    if not password:
        return None
    # Store a keyed fingerprint, never the password or an unkeyed password hash.
    key = os.environ["API_TOKEN"].strip().encode()
    value = os.getenv("MANAGER_ACCESS_VERSION", "1") + "\0" + password
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()


def has_access(user):
    if user is None:
        return False
    if user.role in ("admin", "care"):
        return True
    version = manager_access_version()
    return (user.role == "manager" and version is not None
            and hmac.compare_digest(user.manager_access_version or "", version))


def telegram_user_id(raw, now=None):
    """Validate Telegram Mini App initData, including signature and expiry."""
    try:
        pairs = parse_qsl(raw, keep_blank_values=True, strict_parsing=True)
        values = dict(pairs)
        if len(values) != len(pairs):
            raise ValueError("Duplicate fields")
        supplied = values.pop("hash")
        check = "\n".join(f"{k}={v}" for k, v in sorted(values.items()))
        secret = hmac.new(b"WebAppData", os.environ["API_TOKEN"].strip().encode(), hashlib.sha256).digest()
        expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, supplied):
            raise ValueError("Invalid signature")
        age = (time.time() if now is None else now) - int(values["auth_date"])
        if age < -30 or age > int(os.getenv("TELEGRAM_AUTH_MAX_AGE", "43200")):
            raise ValueError("Expired initData")
        user_id = json.loads(values["user"])["id"]
        if type(user_id) is not int or user_id <= 0:
            raise ValueError("Invalid user")
        return user_id
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise ValueError("Откройте форму заново через Telegram-бота.") from exc


def issue_upload_token(user_id):
    """Short-lived worker credential, restricted to the passport upload endpoint."""
    import base64
    value = base64.urlsafe_b64encode(json.dumps([user_id, int(time.time()) + 120]).encode()).decode()
    signature = hmac.new(os.environ["API_TOKEN"].strip().encode(), b"upload:" + value.encode(), hashlib.sha256).hexdigest()
    return value + "." + signature


def upload_user_id(token):
    import base64
    value, signature = token.split(".", 1)
    expected = hmac.new(os.environ["API_TOKEN"].strip().encode(), b"upload:" + value.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise ValueError("Invalid upload token")
    user_id, expiry = json.loads(base64.urlsafe_b64decode(value))
    if not time.time() <= expiry <= time.time() + 120:
        raise ValueError("Expired upload token")
    return user_id


def validate_access_config():
    if not os.getenv("API_TOKEN", "").strip():
        raise RuntimeError("API_TOKEN must be configured for both API and worker")
    password = os.getenv("MANAGER_PASSWORD", "")
    if not password or password != password.strip():
        raise RuntimeError("Set a non-empty MANAGER_PASSWORD without surrounding whitespace before deploying")
    if password in (os.getenv("ADMIN_PASSWORD", "HickmetTravel"), os.getenv("CARE_PASSWORD", "CARE")):
        raise RuntimeError("Manager, admin and care passwords must be different")
