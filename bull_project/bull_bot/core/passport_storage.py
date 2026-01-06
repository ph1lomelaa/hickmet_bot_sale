import os
from typing import Optional

from bull_project.bull_bot.config.constants import ABS_UPLOADS_DIR, PROJECT_ROOT


def normalize_passport_path_for_storage(value: Optional[str]) -> Optional[str]:
    """
    Normalizes passport path before saving into DB.

    We prefer storing just the filename (relative) for files located in uploads,
    but keep arbitrary external/absolute paths as-is for backward compatibility.
    """
    if value is None:
        return None

    raw = str(value).strip()
    if not raw or raw in {"-", "None", "null"}:
        return None

    # If it's already a plain filename, keep it.
    if "/" not in raw and "\\" not in raw:
        return raw

    normalized = raw.replace("\\", "/")
    if normalized.startswith(ABS_UPLOADS_DIR.replace("\\", "/")) or "/tmp/uploads/" in normalized:
        return os.path.basename(raw)

    return raw


def resolve_passport_file_path(value: Optional[str]) -> Optional[str]:
    """
    Resolves passport_image_path from DB to a real filesystem path.

    Supports:
    - absolute paths (old format)
    - plain filenames returned by /api/passports/upload (new format)
    - relative paths like tmp/uploads/...
    """
    if value is None:
        return None

    raw = str(value).strip()
    if not raw or raw in {"-", "None", "null"}:
        return None

    # If DB already has a valid existing path, use it.
    if os.path.isabs(raw) and os.path.exists(raw):
        return raw

    base = os.path.basename(raw)
    candidate = os.path.join(ABS_UPLOADS_DIR, base)
    if os.path.exists(candidate):
        return candidate

    # Relative path from repo root (PROJECT_ROOT == bull_bot/)
    candidate2 = os.path.join(PROJECT_ROOT, raw.lstrip("/\\"))
    if os.path.exists(candidate2):
        return candidate2

    return None

