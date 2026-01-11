from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import unquote_plus


def normalize_sheet_and_package(raw_sheet_name: str, raw_package_name: str):
    """Очищает названия от лишних символов перед записью."""
    s_name = unquote_plus(raw_sheet_name).strip()
    p_name = unquote_plus(raw_package_name).strip()
    if "[" in p_name and "]" in p_name:
        p_name = p_name.split("[")[0].strip()
    return s_name, p_name


def check_passport_expiry(passport_expiry: str) -> Optional[str]:
    """
    Проверяет срок действия паспорта.
    Если паспорт истекает в течение 6 месяцев - возвращает предупреждение.
    Возвращает None если все в порядке.

    Поддерживаемые форматы дат:
    - DD.MM.YYYY
    - YYYY-MM-DD
    - DD/MM/YYYY
    """
    if not passport_expiry or str(passport_expiry).strip() in ("-", ""):
        return None

    try:
        expiry_date = None
        for fmt in ["%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"]:
            try:
                expiry_date = datetime.strptime(str(passport_expiry).strip(), fmt)
                break
            except ValueError:
                continue

        if not expiry_date:
            return None

        now = datetime.now()
        six_months_later = now + timedelta(days=180)

        if expiry_date <= now:
            days_expired = (now - expiry_date).days
            return f"⚠️ ПАСПОРТ ПРОСРОЧЕН на {days_expired} дн."
        if expiry_date <= six_months_later:
            days_left = (expiry_date - now).days
            months_left = days_left // 30
            return f"⚠️ Истекает через {months_left} мес. ({days_left} дн.)"

        return None

    except Exception:
        return None

