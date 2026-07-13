import os
from typing import Optional

from bull_project.bull_bot.config.constants import ABS_UPLOADS_DIR, PROJECT_ROOT


def normalize_passport_path_for_storage(value: Optional[str]) -> Optional[str]:

    if value is None:
        return None

    raw = str(value).strip()
    if not raw or raw in {"-", "None", "null"}:
        return None
    
    if "/" not in raw and "\\" not in raw:
        return raw

    normalized = raw.replace("\\", "/")
    if normalized.startswith(ABS_UPLOADS_DIR.replace("\\", "/")) or "/tmp/uploads/" in normalized:
        return os.path.basename(raw)

    return raw


def _is_within(path: str, base: str) -> bool:
    """True, если реальный путь лежит внутри base (защита от обхода каталога)."""
    base_real = os.path.realpath(base)
    target_real = os.path.realpath(path)
    return target_real == base_real or target_real.startswith(base_real + os.sep)


def resolve_passport_file_path(value: Optional[str]) -> Optional[str]:

    if value is None:
        return None

    raw = str(value).strip()
    if not raw or raw in {"-", "None", "null"}:
        return None

    # Абсолютный путь принимаем ТОЛЬКО если он внутри разрешённых каталогов
    # (uploads/проект), иначе можно было бы прочитать любой файл ФС.
    if os.path.isabs(raw):
        if os.path.exists(raw) and (
            _is_within(raw, ABS_UPLOADS_DIR) or _is_within(raw, PROJECT_ROOT)
        ):
            return raw
        return None

    base = os.path.basename(raw)
    candidate = os.path.join(ABS_UPLOADS_DIR, base)
    if os.path.exists(candidate):
        return candidate

    candidate2 = os.path.join(PROJECT_ROOT, raw.lstrip("/\\"))
    # Проверяем, что после join путь не вышел за пределы PROJECT_ROOT (../.. и т.п.)
    if os.path.exists(candidate2) and _is_within(candidate2, PROJECT_ROOT):
        return candidate2

    return None

