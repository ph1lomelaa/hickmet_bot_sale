from typing import Any, Dict, List

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from bull_project.bull_bot.api.schemas import BookingSubmitIn, BookingUpdateIn, RescheduleRequestIn
from bull_project.bull_bot.api.utils import normalize_sheet_and_package, check_passport_expiry
from bull_project.bull_bot.database.requests import (
    add_user,
    booking_exists,
    add_booking_to_db,
    delete_bookings_by_ids,
    update_booking_fields,
    update_booking_row,
    get_booking_by_id,
    mark_booking_cancelled,
    create_approval_request,
)
from bull_project.bull_bot.core.google_sheets.writer import save_group_booking
from bull_project.bull_bot.core.websocket_manager import notify_admins_about_request


router = APIRouter()


@router.post("/api/bookings/submit")
async def api_bookings_submit(payload: BookingSubmitIn):
    """
    Создание бронирования.
    """
    try:
        if not payload.pilgrims:
            return JSONResponse(status_code=400, content={"ok": False, "error": "Список паломников пуст"})

        manager_id = payload.manager_id or 0
        try:
            await add_user(
                manager_id,
                payload.manager_name_text or "Manager",
                username="-",
                role="manager",
            )
        except Exception:
            pass

        sheet_name, package_name = normalize_sheet_and_package(payload.sheet_name, payload.package_name)

        visa_status_value = (payload.visa_status or "UMRAH VISA").strip()
        if visa_status_value.upper() == "NO VISA":
            visa_status_value = "-"

        common = {
            "table_id": payload.table_id,
            "sheet_name": sheet_name,
            "package_name": package_name,
            "region": payload.region or "-",
            "departure_city": payload.departure_city or "-",
            "source": payload.source or "-",
            "amount_paid": str(payload.amount_paid or "0"),
            "exchange_rate": str(payload.exchange_rate or "495"),
            "discount": payload.discount or "-",
            "contract_number": payload.contract_number or "-",
            "visa_status": visa_status_value,
            "avia": payload.avia or "-",
            "avia_request": payload.avia or "-",
            "room_type": payload.room_type or "-",
            "meal_type": payload.meal_type or "-",
            "train": payload.train or "-",
            "price": str(payload.price or "0"),
            "comment": payload.comment or "-",
            "manager_name_text": payload.manager_name_text or "-",
            "placement_type": payload.placement_type or "separate",
        }

        # Валидация пола
        for idx, pilgrim in enumerate(payload.pilgrims):
            gen = (pilgrim.gender or "").strip().upper()
            if gen not in ("M", "F"):
                return JSONResponse(
                    status_code=400,
                    content={
                        "ok": False,
                        "error": f"Укажите пол (M/F) для паломника: {(pilgrim.last_name or '-')} {(pilgrim.first_name or '-')}",
                        "pilgrim_index": idx,
                    },
                )

        # Дубликаты
        for pilgrim in payload.pilgrims:
            ln = (pilgrim.last_name or "").strip()
            fn = (pilgrim.first_name or "").strip()
            if await booking_exists(payload.table_id, sheet_name, ln, fn):
                return JSONResponse(
                    status_code=409,
                    content={"ok": False, "error": f"Бронь для {ln} {fn} уже существует"},
                )

        group_data_for_sheets: List[Dict[str, Any]] = []
        db_records: List[Dict[str, Any]] = []
        group_members: List[str] = []

        for pilgrim in payload.pilgrims:
            full_name = f"{(pilgrim.last_name or '').strip()} {(pilgrim.first_name or '').strip()}".strip()
            group_members.append(full_name or "-")

            document_type = pilgrim.document_type or "passport"
            is_id_card = (document_type == "id_card")

            passport_warning = None
            if is_id_card:
                passport_warning = "⚠️ Загружено удостоверение личности, требуется заграничный паспорт"
            else:
                passport_warning = check_passport_expiry(pilgrim.passport_expiry)
                if not passport_warning and (pilgrim.passport_expiry is None or str(pilgrim.passport_expiry).strip() in ("", "-")):
                    passport_warning = "⚠️ Срок действия не распознан"

            if is_id_card:
                p_sheet_data = {
                    "Last Name": pilgrim.last_name or "-",
                    "First Name": pilgrim.first_name or "-",
                    "Date of Birth": pilgrim.date_of_birth or "-",
                    "IIN": pilgrim.iin or "-",
                    "Gender": (pilgrim.gender or "M").strip().upper(),
                    "Document Number": "-",
                    "Document Expiration": "-",
                    "client_phone": pilgrim.phone or "-",
                    "passport_image_path": pilgrim.passport_image_path,
                }
            else:
                p_sheet_data = {
                    "Last Name": pilgrim.last_name or "-",
                    "First Name": pilgrim.first_name or "-",
                    "Gender": (pilgrim.gender or "M").strip().upper(),
                    "Date of Birth": pilgrim.date_of_birth or "-",
                    "Document Number": pilgrim.passport_num or "-",
                    "Document Expiration": pilgrim.passport_expiry or "-",
                    "IIN": pilgrim.iin or "-",
                    "client_phone": pilgrim.phone or "-",
                    "passport_image_path": pilgrim.passport_image_path,
                }
            group_data_for_sheets.append(p_sheet_data)

            db_record = {
                "table_id": payload.table_id,
                "sheet_name": sheet_name,
                "sheet_row_number": None,
                "package_name": package_name,
                "region": common["region"],
                "departure_city": common["departure_city"],
                "source": common["source"],
                "amount_paid": common["amount_paid"],
                "exchange_rate": common["exchange_rate"],
                "discount": common["discount"],
                "contract_number": common["contract_number"],
                "visa_status": common["visa_status"],
                "avia": common["avia"],
                "avia_request": common["avia"],
                "room_type": common["room_type"],
                "meal_type": common["meal_type"],
                "train": common["train"],
                "guest_last_name": (pilgrim.last_name or "-").strip().upper(),
                "guest_first_name": (pilgrim.first_name or "-").strip().upper(),
                "gender": (pilgrim.gender or "M").strip().upper(),
                "date_of_birth": pilgrim.date_of_birth or "-",
                "passport_num": (pilgrim.passport_num or "-").strip().upper(),
                "passport_expiry": pilgrim.passport_expiry or "-",
                "guest_iin": pilgrim.iin or "-",
                "price": common["price"],
                "comment": common["comment"],
                "client_phone": pilgrim.phone or "-",
                "manager_name_text": common["manager_name_text"],
                "placement_type": common["placement_type"],
                "passport_image_path": pilgrim.passport_image_path,
                "passport_warning": passport_warning,
                "group_members": group_members,
                "status": "new",
            }
            db_records.append(db_record)

        # Запись в Sheets
        saved_rows = await save_group_booking(
            group_data_for_sheets,
            common,
            common["placement_type"],
            payload.specific_row,
            False,
        )
        if not saved_rows:
            return JSONResponse(status_code=409, content={"ok": False, "error": "Нет мест"})

        saved_ids: List[int] = []
        try:
            for i, rec in enumerate(db_records):
                if i < len(saved_rows):
                    rec["sheet_row_number"] = saved_rows[i]
                booking_id = await add_booking_to_db(rec, manager_id)
                saved_ids.append(booking_id)
            return {"ok": True, "saved_rows": saved_rows, "db_ids": saved_ids}
        except Exception:
            await delete_bookings_by_ids(saved_ids)
            raise

    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@router.post("/api/bookings/reschedule/request")
async def api_bookings_reschedule_request(payload: RescheduleRequestIn):
    """
    Создание заявки на перенос (без записи в Google Sheets).
    Создаёт новую бронь в БД со статусом pending_reschedule + ApprovalRequest(old:<id>).
    """
    print(f"\n{'='*60}")
    print(f"📨 API: Получен запрос на перенос")
    print(f"{'='*60}")
    print(f"   Old booking ID: {payload.old_booking_id}")
    print(f"   New package: {payload.package_name}")
    print(f"{'='*60}\n")

    try:
        if not payload.pilgrims:
            return JSONResponse(status_code=400, content={"ok": False, "error": "Список паломников пуст"})
        if len(payload.pilgrims) != 1:
            return JSONResponse(status_code=400, content={"ok": False, "error": "Перенос возможен только для 1 паломника"})

        old_booking = await get_booking_by_id(payload.old_booking_id)
        if not old_booking:
            return JSONResponse(status_code=404, content={"ok": False, "error": "Старая бронь не найдена"})

        manager_id = payload.manager_id or 0
        try:
            await add_user(
                manager_id,
                payload.manager_name_text or "Manager",
                username="-",
                role="manager",
            )
        except Exception:
            pass

        sheet_name, package_name = normalize_sheet_and_package(payload.sheet_name, payload.package_name)

        pilgrim = payload.pilgrims[0]
        gender = (pilgrim.gender or "").strip().upper()
        if gender not in ("M", "F"):
            return JSONResponse(status_code=400, content={"ok": False, "error": "Укажите пол (M/F) для переноса"})

        passport_warning = None
        document_type = pilgrim.document_type or "passport"
        is_id_card = (document_type == "id_card")
        if is_id_card:
            passport_warning = "⚠️ Загружено удостоверение личности, требуется заграничный паспорт"
        else:
            passport_warning = check_passport_expiry(pilgrim.passport_expiry)
            if not passport_warning and (pilgrim.passport_expiry is None or str(pilgrim.passport_expiry).strip() in ("", "-")):
                passport_warning = "⚠️ Срок действия не распознан"

        new_booking_data = {
            "table_id": payload.table_id,
            "sheet_name": sheet_name,
            "package_name": package_name,
            "region": payload.region or "-",
            "departure_city": payload.departure_city or "-",
            "source": payload.source or "-",
            "amount_paid": str(payload.amount_paid or "0"),
            "exchange_rate": str(payload.exchange_rate or "495"),
            "discount": payload.discount or "-",
            "contract_number": payload.contract_number or "-",
            "visa_status": (payload.visa_status or "-").strip(),
            "avia": payload.avia or "-",
            "avia_request": payload.avia or "-",
            "room_type": payload.room_type or "-",
            "meal_type": payload.meal_type or "-",
            "train": payload.train or "-",
            "price": str(payload.price or "0"),
            "comment": payload.comment or "-",
            "client_phone": pilgrim.phone or "-",
            "manager_name_text": payload.manager_name_text or "-",
            "placement_type": payload.placement_type or "separate",
            "guest_last_name": (pilgrim.last_name or "-").strip().upper(),
            "guest_first_name": (pilgrim.first_name or "-").strip().upper(),
            "gender": gender,
            "date_of_birth": pilgrim.date_of_birth or "-",
            "passport_num": (pilgrim.passport_num or "-").strip().upper(),
            "passport_expiry": pilgrim.passport_expiry or "-",
            "guest_iin": pilgrim.iin or "-",
            "passport_image_path": pilgrim.passport_image_path,
            "passport_warning": passport_warning,
            "status": "pending_reschedule",
            "sheet_row_number": None,
            "group_members": [f"{(pilgrim.last_name or '').strip()} {(pilgrim.first_name or '').strip()}".strip() or "-"],
        }

        new_booking_id = await add_booking_to_db(new_booking_data, manager_id)
        req_id = await create_approval_request(new_booking_id, "reschedule", manager_id, comment=f"old:{payload.old_booking_id}")
        await update_booking_fields(payload.old_booking_id, {"status": "pending_reschedule"})

        # Отправляем уведомления админам о новой заявке на перенос
        new_booking = await get_booking_by_id(new_booking_id)
        if new_booking:
            booking_data = {
                'id': new_booking.id,
                'package_name': new_booking.package_name,
                'sheet_name': new_booking.sheet_name,
                'sheet_row_number': new_booking.sheet_row_number,
                'guest_last_name': new_booking.guest_last_name,
                'guest_first_name': new_booking.guest_first_name,
                'gender': new_booking.gender,
                'client_phone': new_booking.client_phone,
                'room_type': new_booking.room_type,
                'meal_type': new_booking.meal_type,
                'price': new_booking.price,
                'amount_paid': new_booking.amount_paid,
                'region': new_booking.region,
                'departure_city': new_booking.departure_city,
                'visa_status': new_booking.visa_status,
                'avia': new_booking.avia,
                'manager_name_text': new_booking.manager_name_text,
                'comment': new_booking.comment,
                'passport_warning': new_booking.passport_warning,
                'created_at': new_booking.created_at,
                'old_booking_id': payload.old_booking_id
            }
            await notify_admins_about_request(
                request_id=req_id,
                booking_id=new_booking_id,
                request_type="reschedule",
                booking_data=booking_data,
                initiator_id=manager_id,
                comment=f"Перенос с #{payload.old_booking_id}"
            )

        return {"ok": True, "booking_id": new_booking_id, "request_id": req_id}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@router.patch("/api/bookings/{booking_id}")
async def update_booking_endpoint(booking_id: int, payload: BookingUpdateIn):
    """
    Обновление бронирования (без изменений в Google Sheets).
    """
    try:
        booking = await get_booking_by_id(booking_id)
        if not booking:
            return JSONResponse(status_code=404, content={"ok": False, "error": "Бронь не найдена"})

        update_fields: Dict[str, Any] = {}
        for key, value in payload.model_dump(exclude_unset=True).items():
            if key == "pilgrims":
                continue
            update_fields[key] = value

        if update_fields:
            await update_booking_fields(booking_id, update_fields)

        return {"ok": True, "sheets_updated": False, "db_updated": True, "message": "Бронь обновлена (без изменений в Google Sheets)"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@router.post("/api/bookings/cancel/request")
async def api_bookings_cancel_request(payload: Dict[str, Any]):
    """
    Создание заявки на отмену брони (через WebApp).
    Создаёт ApprovalRequest и ставит статус pending_cancel.
    """
    print(f"\n{'='*60}")
    print(f"📨 API: Получен запрос на отмену")
    print(f"{'='*60}")
    print(f"   Payload: {payload}")
    print(f"{'='*60}\n")

    try:
        booking_id = payload.get("booking_id")
        comment = payload.get("comment", "").strip()
        manager_id = payload.get("manager_id", 0)

        if not booking_id:
            return JSONResponse(status_code=400, content={"ok": False, "error": "Не указан booking_id"})
        if not comment:
            return JSONResponse(status_code=400, content={"ok": False, "error": "Нужен комментарий для заявки на отмену"})

        booking = await get_booking_by_id(booking_id)
        if not booking:
            return JSONResponse(status_code=404, content={"ok": False, "error": "Бронь не найдена"})

        # Создаём заявку на отмену
        req_id = await create_approval_request(booking.id, "cancel", manager_id, comment=comment)
        await update_booking_fields(booking.id, {"status": "pending_cancel"})

        # Уведомляем админов через HTTP API
        booking_data = {
            'id': booking.id,
            'package_name': booking.package_name,
            'sheet_name': booking.sheet_name,
            'sheet_row_number': booking.sheet_row_number,
            'guest_last_name': booking.guest_last_name,
            'guest_first_name': booking.guest_first_name,
            'gender': booking.gender,
            'client_phone': booking.client_phone,
            'room_type': booking.room_type,
            'meal_type': booking.meal_type,
            'price': booking.price,
            'amount_paid': booking.amount_paid,
            'region': booking.region,
            'departure_city': booking.departure_city,
            'visa_status': booking.visa_status,
            'avia': booking.avia,
            'manager_name_text': booking.manager_name_text,
            'comment': booking.comment,
            'passport_warning': booking.passport_warning,
            'created_at': booking.created_at
        }

        await notify_admins_about_request(
            request_id=req_id,
            booking_id=booking.id,
            request_type="cancel",
            booking_data=booking_data,
            initiator_id=manager_id,
            comment=comment
        )

        return {"ok": True, "request_id": req_id, "message": "Заявка на отмену отправлена администратору"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@router.post("/api/bookings/{booking_id}/cancel")
async def cancel_booking_endpoint(booking_id: int):
    """
    УСТАРЕЛО: прямая отмена выключена. Используйте /api/bookings/cancel/request
    """
    return JSONResponse(
        status_code=403,
        content={
            "ok": False,
            "error": "Прямая отмена отключена. Используйте /api/bookings/cancel/request",
        },
    )


@router.get("/api/bookings/{booking_id}")
async def get_booking_endpoint(booking_id: int):
    try:
        booking = await get_booking_by_id(booking_id)
        if not booking:
            return JSONResponse(status_code=404, content={"ok": False, "error": "Бронь не найдена"})
        return {"ok": True, "booking": booking.__dict__}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

