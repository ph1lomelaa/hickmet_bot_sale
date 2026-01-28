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


def resolve_passport_file_path(value: Optional[str]) -> Optional[str]:

    if value is None:
        return None

    raw = str(value).strip()
    if not raw or raw in {"-", "None", "null"}:
        return None

    if os.path.isabs(raw) and os.path.exists(raw):
        return raw

    base = os.path.basename(raw)
    candidate = os.path.join(ABS_UPLOADS_DIR, base)
    if os.path.exists(candidate):
        return candidate

    candidate2 = os.path.join(PROJECT_ROOT, raw.lstrip("/\\"))
    if os.path.exists(candidate2):
        return candidate2

    return None

