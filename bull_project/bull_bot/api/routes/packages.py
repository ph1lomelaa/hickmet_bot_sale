from fastapi import APIRouter
from fastapi.responses import JSONResponse

from bull_project.bull_bot.core.smart_search import get_packages_by_date


router = APIRouter()


@router.get("/api/packages")
async def api_packages(date: str, force: bool = False):
    """Поиск пакетов по дате (Smart Search)."""
    try:
        print(f"🔍 Запрос пакетов для даты: '{date}' (force={force})")

        results = await get_packages_by_date(date_part=date, force=force)

        print(f"✅ Результат поиска: found={results.get('found')}, data_count={len(results.get('data', []))}")
        print(f"   Пакеты: {[item.get('n') for item in results.get('data', [])]}")

        return {
            "ok": True,
            "found": results.get("found", False),
            "data": results.get("data", [])
        }
    except Exception as e:
        print(f"❌ Ошибка в /api/packages: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "found": False,
                "data": []
            }
        )
