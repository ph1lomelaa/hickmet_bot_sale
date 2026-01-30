import os

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from bull_project.bull_bot.api.utils import get_active_tables_for_care, resolve_passport_path
from bull_project.bull_bot.core.google_sheets.client import get_sheet_names, get_packages_from_sheet
from bull_project.bull_bot.database.requests import (
    search_tourist_by_name,
    get_latest_passport_for_person,
    get_db_packages_list,
    get_all_bookings_in_package,
)


router = APIRouter()


@router.get("/api/care/tables")
async def get_care_tables():
    """Возвращает список таблиц (Google Sheets) для отдела заботы."""
    try:
        tables = get_active_tables_for_care()
        if not tables:
            return {"ok": False, "error": "Нет доступных таблиц"}

        return {"ok": True, "tables": tables}
    except Exception as e:
        print(f"❌ Ошибка получения таблиц отдела заботы: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@router.get("/api/care/sheets")
async def get_care_sheets(table_id: str = Query(...)):
    """Возвращает список листов в выбранной таблице."""
    try:
        sheets = get_sheet_names(table_id) or []
        return {"ok": True, "sheets": sheets}
    except Exception as e:
        print(f"❌ Ошибка получения листов: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@router.get("/api/care/search")
async def care_search_tourist(query: str = Query(..., min_length=1)):
    """
    Поиск паломника по имени/фамилии (без учета регистра, пробелов).
    Возвращает список найденных паломников с фото паспорта и всей информацией.
    """
    try:
        # Нормализуем запрос: убираем лишние пробелы
        query_normalized = " ".join(query.strip().split())

        print(f"🔍 Care Search: ищем '{query_normalized}'")

        # Поиск в БД
        results = await search_tourist_by_name(query_normalized)

        if not results:
            return {
                "ok": True,
                "results": []
            }

        # Формируем ответ
        tourists_data = []
        for booking in results:
            has_passport = bool(booking.passport_image_path)

            # Если паспорта нет, пробуем взять самый свежий по этому же ФИО
            fallback_passport = None
            if not has_passport and booking.guest_last_name and booking.guest_first_name:
                try:
                    fallback_passport = await get_latest_passport_for_person(
                        booking.guest_last_name,
                        booking.guest_first_name
                    )
                    if fallback_passport and not os.path.exists(fallback_passport):
                        fallback_passport = None
                except Exception:
                    fallback_passport = None

            tourists_data.append({
                "id": booking.id,
                "last_name": booking.guest_last_name or "-",
                "first_name": booking.guest_first_name or "-",
                "gender": booking.gender or "-",
                "date_of_birth": booking.date_of_birth or "-",
                "passport_num": booking.passport_num or "-",
                "passport_expiry": booking.passport_expiry or "-",
                "iin": booking.guest_iin or "-",
                "phone": booking.client_phone or "-",
                "package_name": booking.package_name or "-",
                "sheet_name": booking.sheet_name or "-",
                "placement_type": booking.placement_type or "-",
                "room_type": booking.room_type or "-",
                "meal_type": booking.meal_type or "-",
                "price": booking.price or "-",
                "amount_paid": booking.amount_paid or "-",
                "manager_name": booking.manager_name_text or "-",
                "comment": booking.comment or "",
                "visa_status": booking.visa_status or "-",
                "avia": booking.avia or "-",
                "train": booking.train or "-",
                "region": booking.region or "-",
                "departure_city": booking.departure_city or "-",
                "source": booking.source or "-",
                "passport_image_path": booking.passport_image_path or fallback_passport or None,
                "created_at": booking.created_at.isoformat() if booking.created_at else None,
                "status": booking.status
            })
            print(
                f"  Паломник {booking.guest_last_name} {booking.guest_first_name}: "
                f"паспорт={has_passport}, путь={booking.passport_image_path or fallback_passport}"
            )

        print(f"✅ Найдено {len(tourists_data)} результатов")

        return {
            "ok": True,
            "results": tourists_data
        }

    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@router.get("/api/care/packages-by-date")
async def get_packages_by_date_for_care(
    table_id: str = Query(...),
    sheet_name: str = Query(...)
):
    """
    Возвращает список пакетов на конкретной дате (для выбора date sheet).
    """
    try:
        print(f"📋 Care Packages: table_id={table_id}, sheet_name={sheet_name}")

        # Сначала пробуем прочитать актуальные пакеты напрямую из Google Sheet
        packages_map = get_packages_from_sheet(table_id, sheet_name)
        packages = list(packages_map.values()) if packages_map else []

        # Если из таблицы ничего не нашли (например, проблемы с форматами),
        # пробуем достать из БД как фолбэк.
        if not packages:
            packages = await get_db_packages_list(table_id, sheet_name)

        return {
            "ok": True,
            "packages": list(packages)
        }

    except Exception as e:
        print(f"❌ Ошибка получения пакетов: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@router.get("/api/care/bookings-in-package")
async def get_bookings_in_package_for_care(
    table_id: str = Query(...),
    sheet_name: str = Query(...),
    package_name: str = Query(...)
):
    """
    Возвращает все брони в конкретном пакете со всей информацией.
    """
    try:
        print(f"📋 Care Bookings: package='{package_name}', sheet='{sheet_name}'")

        bookings = await get_all_bookings_in_package(table_id, sheet_name, package_name)

        bookings_data = []
        for b in bookings:
            passport_path = await resolve_passport_path(b)
            bookings_data.append({
                "id": b.id,
                "last_name": b.guest_last_name or "-",
                "first_name": b.guest_first_name or "-",
                "package_name": b.package_name or "-",
                "sheet_name": b.sheet_name or "-",
                "table_id": b.table_id or "-",
                "gender": b.gender or "-",
                "date_of_birth": b.date_of_birth or "-",
                "passport_num": b.passport_num or "-",
                "passport_expiry": b.passport_expiry or "-",
                "iin": b.guest_iin or "-",
                "phone": b.client_phone or "-",
                "room_type": b.room_type or "-",
                "meal_type": b.meal_type or "-",
                "price": b.price or "-",
                "amount_paid": b.amount_paid or "-",
                "manager_name": b.manager_name_text or "-",
                "comment": b.comment or "",
                "visa_status": b.visa_status or "-",
                "avia": b.avia or "-",
                "train": b.train or "-",
                "region": b.region or "-",
                "departure_city": b.departure_city or "-",
                "source": b.source or "-",
                "passport_image_path": passport_path or None,
                "sheet_row_number": b.sheet_row_number,
                "created_at": b.created_at.isoformat() if b.created_at else None,
                "status": b.status
            })

        print(f"✅ Найдено {len(bookings_data)} броней в пакете")

        return {
            "ok": True,
            "bookings": bookings_data
        }

    except Exception as e:
        print(f"❌ Ошибка получения броней: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@router.get("/api/care/phones-by-package")
async def get_phones_by_package(
    table_id: str = Query(...),
    sheet_name: str = Query(...),
    package_name: str = Query(...)
):
    """
    Возвращает список телефонов с именами для конкретного пакета.
    """
    try:
        print(f"📞 Care Phones: package='{package_name}'")

        bookings = await get_all_bookings_in_package(table_id, sheet_name, package_name)

        phones_data = []
        for b in bookings:
            if b.client_phone and b.client_phone != "-":
                phones_data.append({
                    "name": f"{b.guest_last_name or ''} {b.guest_first_name or ''}".strip(),
                    "phone": b.client_phone
                })

        print(f"✅ Найдено {len(phones_data)} телефонов")

        return {
            "ok": True,
            "phones": phones_data
        }

    except Exception as e:
        print(f"❌ Ошибка получения телефонов: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )
