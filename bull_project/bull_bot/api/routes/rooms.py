from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from bull_project.bull_bot.core.google_sheets.client import get_sheet_data
from bull_project.bull_bot.core.google_sheets.allocator import (
    get_open_rooms_for_manual_selection,
    find_best_slot,
)
from bull_project.bull_bot.api.utils import normalize_sheet_and_package


router = APIRouter()

# Человекочитаемые описания трансформаций (соответствуют режимам find_best_slot)
_TRANSFORM_LABELS = {
    "trans_1quad_2dbl": "1 пустой Quadro → 2 Double",
    "trans_2trpl_3dbl": "2 пустых Triple → 3 Double",
    "trans_2quad_mix": "2 пустых Quadro → 2 Triple + 1 Double",
    "trans_3dbl_2trpl": "3 пустых Double → 2 Triple",
    "trans_2dbl_1quad": "2 пустых Double → 1 Quadro",
    "trans_1dbl_2sgl": "1 пустой Double → 2 Single",
    "trans_1trpl_mix": "1 пустой Triple → 1 Double + 1 Single",
}


def _detect_transform(all_rows, package_name, room_type, gender):
    """Возвращает описание трансформации, только если авторазмещение реально
    её применит (режим trans_*). В остальных случаях — None."""
    try:
        _, _, mode = find_best_slot(all_rows, package_name, gender or "M", room_type)
    except Exception:
        return None
    if mode and mode.startswith("trans_"):
        return _TRANSFORM_LABELS.get(mode, "Автоматическое размещение создаст свободное место")
    return None


@router.get("/api/rooms")
async def api_rooms(
    table_id: str,
    sheet_name: str,
    package_name: str,
    count: int = 1,
    room_type: str = "Quad",
    gender: str = "M",
):
    """Получение списка свободных комнат."""
    s_name, p_name = normalize_sheet_and_package(sheet_name, package_name)
    try:
        all_rows = await run_in_threadpool(get_sheet_data, table_id, s_name)
        rooms = await run_in_threadpool(
            get_open_rooms_for_manual_selection,
            all_rows,
            p_name,
            count,
            room_type,
            gender,
        )
        # Подсказку о трансформации показываем только если подселения нет,
        # но авторазмещение реально создаст место за счёт трансформации.
        transform = None
        if not rooms:
            transform = await run_in_threadpool(
                _detect_transform, all_rows, p_name, room_type, gender
            )
        return {"ok": True, "found": len(rooms) > 0, "rooms": rooms, "transform": transform}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

