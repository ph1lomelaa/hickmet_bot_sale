import json
from datetime import datetime
from typing import List, Dict, Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from bull_project.bull_bot.api.schemas import (
    BookingSubmitIn,
    RescheduleRequestIn,
    CancelRequestIn,
    BookingUpdateIn,
)
from bull_project.bull_bot.api.utils import normalize_sheet_and_package, check_passport_expiry, resolve_passport_path
from bull_project.bull_bot.database.requests import (
    add_booking_to_db,
    update_booking_row,
    add_user,
    get_last_n_bookings_by_manager,
    get_booking_by_id,
    update_booking_fields,
    find_active_bookings_for_person,
    delete_bookings_by_ids,
    create_approval_request,
)
from bull_project.bull_bot.core.google_sheets.writer import save_group_booking
from bull_project.bull_bot.core.websocket_manager import (
    notify_admins_about_request,
    notify_admins_about_new_booking,
    notify_phone_subscribers,
)

# Опциональный импорт webhook (требует httpx)
try:
    from bull_project.bull_bot.core.webhook_notifier import notify_new_booking
    WEBHOOK_ENABLED = True
except ImportError:
    WEBHOOK_ENABLED = False
    notify_new_booking = None  # type: ignore


router = APIRouter()


@router.post("/api/bookings/submit")
async def api_bookings_submit(payload: BookingSubmitIn):
    print("\n" + "="*60)
    print("📥 ПОЛУЧЕН ЗАПРОС /api/bookings/submit")
    print("="*60)
    print(f"Количество паломников: {len(payload.pilgrims)}")

    for i, p in enumerate(payload.pilgrims):
        print(f"\n👤 Паломник {i+1}:")
        print(f"  Фамилия: {p.last_name}")
        print(f"  Имя: {p.first_name}")
        print(f"  Пол: {p.gender}")
        print(f"  Дата рождения: {p.date_of_birth}")
        print(f"  Номер паспорта: {p.passport_num}")
        print(f"  Срок действия: {p.passport_expiry}")
        print(f"  ИИН: {p.iin}")
        print(f"  Телефон: {p.phone}")
        print(f"  🔍 DEBUG: is_infant={p.is_infant}, is_child={p.is_child}")

    print("\n📦 Общие данные:")
    print(f"  Пакет: {payload.package_name}")
    print(f"  Лист: {payload.sheet_name}")
    print(f"  Таблица: {payload.table_id}")
    print(f"  Тип комнаты: {payload.room_type}")
    print("="*60 + "\n")

    # 0. Защита от пустого списка
    if not payload.pilgrims:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "Список паломников пуст"}
        )

    # 1. Проверяем/создаем менеджера в БД
    manager_id = payload.manager_id or 0
    try:
        await add_user(
            manager_id,
            payload.manager_name_text or "Manager",
            username="-",
            role="manager",
        )
    except Exception:
        pass  # если уже есть — игнорируем

    # 2. Нормализация имен
    sheet_name, package_name = normalize_sheet_and_package(
        payload.sheet_name,
        payload.package_name,
    )

    # 3. Подготовка общих данных (Common Data)
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

    # 4. Проверка пола у всех паломников
    print(f"\n🔍 ПРОВЕРКА ПОЛА всех паломников:")
    for idx, pilgrim in enumerate(payload.pilgrims):
        gen = (pilgrim.gender or "").strip().upper()
        print(f"   Паломник {idx+1}: {pilgrim.last_name} {pilgrim.first_name}")
        print(f"      gender RAW: '{pilgrim.gender}'")
        print(f"      gender NORMALIZED: '{gen}'")
        if gen not in ("M", "F"):
            error_msg = (
                "❌ Пол не указан или некорректен для паломника "
                f"{idx+1}: {pilgrim.last_name} {pilgrim.first_name} (получено: '{pilgrim.gender}')"
            )
            print(error_msg)
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "error": f"Укажите пол (M/F) для паломника: {pilgrim.last_name} {pilgrim.first_name}",
                    "pilgrim_index": idx,
                    "pilgrim_name": f"{pilgrim.last_name} {pilgrim.first_name}"
                }
            )
    print(f"✅ Все паломники имеют корректный пол")

    # 4.1 Проверка на дубликаты (активные брони по ФИО или паспорту).
    # Не запрещаем, а предупреждаем: менеджер может подтвердить (confirm_duplicates).
    if not payload.confirm_duplicates:
        duplicates = []
        for pilgrim in payload.pilgrims:
            ln = (pilgrim.last_name or "").strip()
            fn = (pilgrim.first_name or "").strip()
            existing = await find_active_bookings_for_person(ln, fn, pilgrim.passport_num)
            for b in existing:
                duplicates.append({
                    "name": f"{ln} {fn}".strip(),
                    "booking_id": b.id,
                    "package_name": b.package_name or "-",
                    "sheet_name": b.sheet_name or "-",
                    "manager_name_text": b.manager_name_text or "-",
                    "created_at": b.created_at.strftime("%d.%m.%Y") if b.created_at else "-",
                    "same_tour": (
                        b.table_id == payload.table_id
                        and (b.sheet_name or "").strip() == sheet_name
                        and (b.package_name or "").strip() == package_name
                    ),
                })
        if duplicates:
            return JSONResponse(
                status_code=409,
                content={
                    "ok": False,
                    "code": "duplicate_warning",
                    "error": "Найдены существующие брони для паломников",
                    "duplicates": duplicates,
                }
            )

    # 5. Формирование данных для Google Sheets
    group_data_for_sheets: List[Dict[str, Any]] = []
    db_records: List[Dict[str, Any]] = []  # 🔥 Храним данные для БД
    group_members: List[str] = []

    for pilgrim in payload.pilgrims:
        full_name = f"{(pilgrim.last_name or '').strip()} {(pilgrim.first_name or '').strip()}".strip()
        group_members.append(full_name or "-")

        # 🔥 Проверка типа документа
        document_type = pilgrim.document_type or "passport"
        is_id_card = (document_type == "id_card")

        # 🔥 Проверка срока действия паспорта
        passport_warning = None
        if is_id_card:
            # Если загружено удостоверение личности
            passport_warning = "⚠️ Загружено удостоверение личности, требуется заграничный паспорт"
            print(f"🆔 {full_name}: {passport_warning}")
        else:
            # Проверяем срок действия только для паспортов
            passport_warning = check_passport_expiry(pilgrim.passport_expiry)
            if passport_warning:
                print(f"⚠️ {full_name}: {passport_warning}")

        # Данные для Sheets
        if is_id_card:
            # Для ID card записываем только: имя, фамилию, дату рождения, ИИН, пол
            # НЕ записываем номер документа ID card
            p_sheet_data = {
                "Last Name": pilgrim.last_name or "-",
                "First Name": pilgrim.first_name or "-",
                "Gender": pilgrim.gender or "M",
                "Date of Birth": pilgrim.date_of_birth or "-",
                "Document Number": "-",  # НЕ записываем номер ID card
                "Document Expiration": "-",  # НЕ записываем срок действия ID card
                "IIN": pilgrim.iin or "-",
                "client_phone": pilgrim.phone or "-",
                "phone": pilgrim.phone or "-",
                "manager_name_text": common["manager_name_text"],
                "is_infant": pilgrim.is_infant,
                "is_child": pilgrim.is_child
            }
        else:
            p_sheet_data = {
                "Last Name": pilgrim.last_name or "-",
                "First Name": pilgrim.first_name or "-",
                "Gender": pilgrim.gender or "M",
                "Date of Birth": pilgrim.date_of_birth or "-",
                "Document Number": pilgrim.passport_num or "-",
                "Document Expiration": pilgrim.passport_expiry or "-",
                "IIN": pilgrim.iin or "-",
                "client_phone": pilgrim.phone or "-",
                "phone": pilgrim.phone or "-",
                "manager_name_text": common["manager_name_text"],
                "is_infant": pilgrim.is_infant,
                "is_child": pilgrim.is_child
            }
        group_data_for_sheets.append(p_sheet_data)

        # Данные для БД
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
            "status": "new"
        }
        db_records.append(db_record)

    # 6. Запись в Google Sheets
    saved_rows, room_notices = await save_group_booking(
        group_data_for_sheets,
        common,
        common["placement_type"],
        payload.specific_row,
        False
    )

    if not saved_rows:
        return JSONResponse(
            status_code=409,
            content={"ok": False, "error": "Нет мест"}
        )

    # 7. Запись в БД
    db_ids = []
    try:
        for i, record in enumerate(db_records):
            if i < len(saved_rows):
                record['sheet_row_number'] = saved_rows[i]
            booking_id = await add_booking_to_db(record, manager_id)
            db_ids.append(booking_id)

        # 8. Отправляем уведомления админам о новых бронях
        try:
            # Подготавливаем данные брони для уведомления
            for i, record in enumerate(db_records):
                booking_data = {
                    'id': db_ids[i] if i < len(db_ids) else 0,
                    'package_name': record.get("package_name", "-"),
                    'sheet_name': record.get("sheet_name", "-"),
                    'sheet_row_number': saved_rows[i] if i < len(saved_rows) else "-",
                    'guest_last_name': record.get("guest_last_name", ""),
                    'guest_first_name': record.get("guest_first_name", ""),
                    'gender': record.get("gender", "M"),
                    'client_phone': record.get("client_phone", "-"),
                    'room_type': record.get("room_type", "-"),
                    'meal_type': record.get("meal_type", "-"),
                    'price': record.get("price", "-"),
                    'amount_paid': record.get("amount_paid", "-"),
                    'region': record.get("region", "-"),
                    'departure_city': record.get("departure_city", "-"),
                    'visa_status': record.get("visa_status", "-"),
                    'avia': record.get("avia", "-"),
                    'manager_name_text': record.get("manager_name_text", "-"),
                    'comment': record.get("comment", ""),
                    'passport_warning': record.get("passport_warning", ""),
                    'created_at': datetime.now()
                }

                await notify_admins_about_new_booking(booking_data)

        except Exception as notify_error:
            # Не прерываем выполнение если уведомление не отправилось
            print(f"⚠️ Ошибка отправки уведомления админам (не критично): {notify_error}")

        # 9. 📱 Отправляем WebSocket уведомления о новых телефонах
        for i, record in enumerate(db_records):
            phone = record.get("client_phone", "-")
            if phone and phone != "-":
                await notify_phone_subscribers(
                    phone=phone,
                    booking_id=db_ids[i] if i < len(db_ids) else 0,
                    guest_name=f"{record.get('guest_first_name', '')} {record.get('guest_last_name', '')}",
                    package_name=record.get("package_name", "-"),
                    group_size=len(db_records),
                    group_members=record.get("group_members", []),
                    room_type=record.get("room_type", "-"),
                    manager_name=record.get("manager_name_text", "-"),
                    departure_city=record.get("departure_city", "-"),
                    comment=record.get("comment", "-"),
                    price=record.get("price", "0"),
                    visa_status=record.get("visa_status", "-"),
                    avia=record.get("avia", "-"),
                    gender=record.get("gender", "M")
                )

        # 10. 🔔 Отправляем webhook уведомление о новой брони
        if WEBHOOK_ENABLED and notify_new_booking:
            try:
                await notify_new_booking(
                    bookings_data=db_records,
                    package_name=package_name,
                    sheet_name=sheet_name,
                    table_id=payload.table_id,
                    db_ids=db_ids,
                    saved_rows=saved_rows
                )
            except Exception as webhook_error:
                # Не прерываем выполнение если webhook не отправился
                print(f"⚠️ Ошибка отправки webhook (не критично): {webhook_error}")

        return {"ok": True, "db_ids": db_ids, "saved_rows": saved_rows, "room_notices": room_notices}

    except Exception:
        await delete_bookings_by_ids(db_ids)
        raise


@router.get("/api/history/{manager_id}")
async def get_manager_history(manager_id: int):
    """
    Получение истории бронирований менеджера
    """
    try:
        print(f"\n📋 Запрос истории для менеджера {manager_id}")

        # Получаем последние 100 бронирований менеджера
        bookings = await get_last_n_bookings_by_manager(manager_id, limit=100, include_cancelled=True)

        if not bookings:
            return {
                "ok": True,
                "bookings": [],
                "message": "История пуста"
            }

        bookings_data = []
        for b in bookings:
            passport_path = await resolve_passport_path(b)
            # group_members теперь автоматически десериализуется SQLAlchemy (тип JSON)
            group_members = b.group_members if b.group_members else []
            bookings_data.append({
                "id": b.id,
                "manager_id": b.manager_id,
                "table_id": b.table_id,
                "sheet_name": b.sheet_name,
                "sheet_row_number": b.sheet_row_number,
                "package_name": b.package_name,
                "region": b.region,
                "departure_city": b.departure_city,
                "source": b.source,
                "amount_paid": b.amount_paid,
                "exchange_rate": b.exchange_rate,
                "discount": b.discount,
                "contract_number": b.contract_number,
                "visa_status": b.visa_status,
                "avia": b.avia,
                "avia_request": b.avia_request,
                "room_type": b.room_type,
                "meal_type": b.meal_type,
                "train": b.train,
                "price": b.price,
                "comment": b.comment,
                "manager_name_text": b.manager_name_text,
                "placement_type": b.placement_type,
                "guest_last_name": b.guest_last_name,
                "guest_first_name": b.guest_first_name,
                "gender": b.gender,
                "date_of_birth": b.date_of_birth,
                "passport_num": b.passport_num,
                "passport_expiry": b.passport_expiry,
                "guest_iin": b.guest_iin,
                "client_phone": b.client_phone,
                "passport_image_path": passport_path,
                "group_members": group_members,
                "status": b.status,
                "created_at": b.created_at.isoformat() if b.created_at else None
            })

        print(f"✅ Найдено {len(bookings_data)} бронирований")

        return {
            "ok": True,
            "bookings": bookings_data
        }

    except Exception as e:
        print(f"❌ Ошибка получения истории: {e}")
        import traceback
        traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"ok": False, "error": str(e)}
    )


@router.post("/api/bookings/reschedule/request")
async def api_bookings_reschedule_request(payload: RescheduleRequestIn):
    """
    Создание заявки на перенос (без записи в Google Sheets).
    Создаёт новую бронь в БД со статусом pending_reschedule + ApprovalRequest(old:<id>).
    """
    try:
        if not payload.pilgrims:
            return JSONResponse(status_code=400, content={"ok": False, "error": "Список паломников пуст"})

        old_ids = []
        if payload.old_booking_ids:
            old_ids = [int(x) for x in payload.old_booking_ids if int(x) > 0]
        if not old_ids:
            old_ids = [int(payload.old_booking_id or 0)]
        old_ids = [x for x in old_ids if x > 0]
        if not old_ids:
            return JSONResponse(status_code=400, content={"ok": False, "error": "old_booking_id is required"})

        if len(payload.pilgrims) != len(old_ids):
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "Количество паломников не совпадает с количеством переносимых броней"},
            )

        for oid in old_ids:
            b = await get_booking_by_id(oid)
            if not b:
                return JSONResponse(status_code=404, content={"ok": False, "error": f"Старая бронь не найдена: #{oid}"})

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

        group_members = [
            f"{(p.last_name or '').strip()} {(p.first_name or '').strip()}".strip() or "-"
            for p in payload.pilgrims
        ]

        new_booking_ids = []
        for pilgrim in payload.pilgrims:
            gender = (pilgrim.gender or "").strip().upper()
            if gender not in ("M", "F"):
                return JSONResponse(
                    status_code=400,
                    content={"ok": False, "error": "Укажите пол (M/F) для переноса"},
                )

            # Предупреждение по сроку / типу документа
            passport_warning = None
            document_type = pilgrim.document_type or "passport"
            is_id_card = (document_type == "id_card")
            if is_id_card:
                passport_warning = "⚠️ Загружено удостоверение личности, требуется заграничный паспорт"
            else:
                passport_warning = check_passport_expiry(pilgrim.passport_expiry)
                if not passport_warning and (pilgrim.passport_expiry is None or str(pilgrim.passport_expiry).strip() == "-" or str(pilgrim.passport_expiry).strip() == ""):
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
                "group_members": group_members,
            }

            new_booking_ids.append(await add_booking_to_db(new_booking_data, manager_id))

        # Один ApprovalRequest на всю группу (ссылается на первую новую бронь)
        request_payload = {
            "old_booking_ids": old_ids,
            "new_booking_ids": new_booking_ids,
            "comment": (payload.comment or "").strip() or None,
        }
        req_id = await create_approval_request(
            new_booking_ids[0],
            "reschedule",
            manager_id,
            comment=json.dumps(request_payload, ensure_ascii=False),
        )
        for old_id in old_ids:
            await update_booking_fields(old_id, {"status": "pending_reschedule"})

        # Отправляем уведомления админам о новой заявке на перенос
        new_booking = await get_booking_by_id(new_booking_ids[0])
        if new_booking:
            booking_dict = {
                "id": new_booking.id,
                "package_name": new_booking.package_name,
                "sheet_name": new_booking.sheet_name,
                "sheet_row_number": new_booking.sheet_row_number,
                "guest_last_name": new_booking.guest_last_name,
                "guest_first_name": new_booking.guest_first_name,
                "client_phone": new_booking.client_phone,
                "manager_name_text": new_booking.manager_name_text,
                "room_type": new_booking.room_type,
                "meal_type": new_booking.meal_type,
                "price": new_booking.price,
                "amount_paid": new_booking.amount_paid,
                "region": new_booking.region,
                "departure_city": new_booking.departure_city,
                "visa_status": new_booking.visa_status,
                "avia": new_booking.avia,
                "passport_warning": new_booking.passport_warning,
                "old_booking_ids": old_ids,
                "group_members": group_members,
            }
            await notify_admins_about_request(
                request_id=req_id,
                booking_id=new_booking.id,
                request_type="reschedule",
                booking_data=booking_dict,
                initiator_id=manager_id,
                comment=(payload.comment or "").strip() or f"Старые брони: {', '.join([str(x) for x in old_ids])}"
            )

        return {"ok": True, "booking_ids": new_booking_ids, "request_id": req_id}
    except Exception as e:
        print(f"❌ Ошибка /api/bookings/reschedule/request: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@router.post("/api/bookings/cancel/request")
async def api_bookings_cancel_request(payload: CancelRequestIn):
    """
    Создание заявки на отмену (без прямой отмены).
    """
    try:
        booking_id = int(payload.booking_id or 0)
        comment = (payload.comment or "").strip()
        initiator_id = int(payload.initiator_id or 0)

        if booking_id <= 0:
            return JSONResponse(status_code=400, content={"ok": False, "error": "booking_id is required"})
        if not comment:
            return JSONResponse(status_code=400, content={"ok": False, "error": "comment is required"})

        booking = await get_booking_by_id(booking_id)
        if not booking:
            return JSONResponse(status_code=404, content={"ok": False, "error": "booking not found"})

        req_id = await create_approval_request(booking.id, "cancel", initiator_id, comment=comment)
        await update_booking_fields(booking.id, {"status": "pending_cancel"})

        booking_dict = {
            "id": booking.id,
            "package_name": booking.package_name,
            "sheet_name": booking.sheet_name,
            "sheet_row_number": booking.sheet_row_number,
            "guest_last_name": booking.guest_last_name,
            "guest_first_name": booking.guest_first_name,
            "client_phone": booking.client_phone,
            "manager_name_text": booking.manager_name_text,
            "room_type": booking.room_type,
            "meal_type": booking.meal_type,
            "price": booking.price,
            "amount_paid": booking.amount_paid,
            "region": booking.region,
            "departure_city": booking.departure_city,
            "visa_status": booking.visa_status,
            "avia": booking.avia,
            "passport_warning": booking.passport_warning,
        }

        await notify_admins_about_request(
            request_id=req_id,
            booking_id=booking.id,
            request_type="cancel",
            booking_data=booking_dict,
            initiator_id=initiator_id,
            comment=comment,
        )

        return {"ok": True, "booking_id": booking.id, "request_id": req_id}
    except Exception as e:
        print(f"❌ Ошибка /api/bookings/cancel/request: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@router.post("/api/bookings/{booking_id}/cancel")
async def cancel_booking_endpoint(booking_id: int):
    """
    УСТАРЕЛО: прямая отмена выключена. Отмена теперь только через заявку + одобрение админа.
    """
    try:
        return JSONResponse(
            status_code=403,
            content={
                "ok": False,
                "error": "Прямая отмена отключена. Создайте заявку на отмену и дождитесь одобрения администратора.",
            },
        )

    except Exception as e:
        print(f"❌ Ошибка отмены брони: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@router.get("/api/bookings/{booking_id}")
async def get_booking_details(booking_id: int):
    """
    Получение детальной информации о бронировании
    """
    try:
        booking = await get_booking_by_id(booking_id)
        if not booking:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": "Бронь не найдена"}
            )

        return {
            "ok": True,
            "booking": {
                "id": booking.id,
                "guest_last_name": booking.guest_last_name,
                "guest_first_name": booking.guest_first_name,
                "gender": booking.gender,
                "date_of_birth": booking.date_of_birth,
                "passport_num": booking.passport_num,
                "passport_expiry": booking.passport_expiry,
                "guest_iin": booking.guest_iin,
                "client_phone": booking.client_phone,
                "package_name": booking.package_name,
                "sheet_name": booking.sheet_name,
                "table_id": booking.table_id,
                "sheet_row_number": booking.sheet_row_number,
                "departure_city": booking.departure_city,
                "room_type": booking.room_type,
                "meal_type": booking.meal_type,
                "price": booking.price,
                "amount_paid": booking.amount_paid,
                "exchange_rate": booking.exchange_rate,
                "discount": booking.discount,
                "contract_number": booking.contract_number,
                "visa_status": booking.visa_status,
                "avia": booking.avia,
                "train": booking.train,
                "region": booking.region,
                "source": booking.source,
                "manager_name_text": booking.manager_name_text,
                "comment": booking.comment,
                "passport_image_path": booking.passport_image_path,
                "status": booking.status,
                "created_at": booking.created_at.isoformat() if booking.created_at else None
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@router.patch("/api/bookings/{booking_id}")
async def update_booking_endpoint(booking_id: int, payload: BookingUpdateIn):
    """
    Обновление существующей брони (редактирование)
    """
    try:
        print(f"\n✏️ Запрос на обновление брони #{booking_id}")

        # Получаем текущую бронь
        booking = await get_booking_by_id(booking_id)
        if not booking:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": "Бронь не найдена"}
            )

        # Формируем обновленные данные
        update_fields = {}

        p = None  # будем использовать позже при валидации
        # Обновляем данные паломника если переданы
        if payload.pilgrims and len(payload.pilgrims) > 0:
            p = payload.pilgrims[0]  # Берем первого паломника
            # Проверяем что значение не None и не пустое перед обновлением
            if p.last_name and p.last_name != "-":
                update_fields['guest_last_name'] = p.last_name
            if p.first_name and p.first_name != "-":
                update_fields['guest_first_name'] = p.first_name
            if p.gender and p.gender != "-":
                update_fields['gender'] = p.gender
            if p.date_of_birth and p.date_of_birth != "-":
                update_fields['date_of_birth'] = p.date_of_birth
            if p.passport_num and p.passport_num != "-":
                update_fields['passport_num'] = p.passport_num
            if p.passport_expiry and p.passport_expiry != "-":
                update_fields['passport_expiry'] = p.passport_expiry
                # 🔥 Проверяем срок действия паспорта при обновлении (только для паспортов, не для ID card)
                document_type = p.document_type or "passport"
                is_id_card = (document_type == "id_card")
                if not is_id_card:
                    passport_warning = check_passport_expiry(p.passport_expiry)
                    update_fields['passport_warning'] = passport_warning
                    if passport_warning:
                        print(f"⚠️ Обновление брони #{booking_id}: {passport_warning}")
            if p.iin and p.iin != "-":
                update_fields['guest_iin'] = p.iin
            if p.phone and p.phone != "-":
                update_fields['client_phone'] = p.phone

            # Обновляем фото паспорта если передано
            # Важно: пишем через update_fields, чтобы:
            # 1) запись точно попала в один commit update_booking_fields()
            # 2) в логах/ответе было видно, что обновлялось
            if p.passport_image_path:
                update_fields["passport_image_path"] = p.passport_image_path

                # 🔥 Проверяем тип документа
                document_type = p.document_type or "passport"
                is_id_card = (document_type == "id_card")

                if is_id_card:
                    # Если загружено удостоверение личности
                    update_fields['passport_warning'] = "⚠️ Загружено удостоверение личности, требуется заграничный паспорт"
                    print(f"🆔 При загрузке паспорта обнаружено удостоверение личности для брони #{booking_id}")
                else:
                    # 🔥 Проверяем существующий срок действия паспорта в БД
                    if booking.passport_expiry and booking.passport_expiry != "-":
                        passport_warning = check_passport_expiry(booking.passport_expiry)
                        update_fields['passport_warning'] = passport_warning
                        if passport_warning:
                            print(f"⚠️ При загрузке паспорта обнаружено: {passport_warning}")

        # Обновляем общие поля (пакет/дата/таблица не меняем PATCH'ем)
        if payload.departure_city: update_fields['departure_city'] = payload.departure_city
        if payload.room_type: update_fields['room_type'] = payload.room_type
        if payload.meal_type: update_fields['meal_type'] = payload.meal_type
        if payload.visa_status: update_fields['visa_status'] = payload.visa_status
        if payload.avia: update_fields['avia'] = payload.avia
        if payload.price: update_fields['price'] = payload.price
        if payload.amount_paid: update_fields['amount_paid'] = payload.amount_paid
        if payload.contract_number: update_fields['contract_number'] = payload.contract_number
        if payload.exchange_rate: update_fields['exchange_rate'] = payload.exchange_rate
        if payload.discount: update_fields['discount'] = payload.discount
        if payload.source: update_fields['source'] = payload.source
        if payload.region: update_fields['region'] = payload.region
        if payload.train: update_fields['train'] = payload.train
        if payload.manager_name_text: update_fields['manager_name_text'] = payload.manager_name_text
        if payload.comment: update_fields['comment'] = payload.comment

        # Обновляем в БД
        await update_booking_fields(booking_id, update_fields)

        print(f"✅ Бронь #{booking_id} успешно обновлена в БД")
        print(f"   Обновлено полей: {len(update_fields)}")

        # 🔥 По требованию: при обновлении/загрузке паспорта Google Sheets не трогаем вообще
        return JSONResponse(status_code=200, content={
            "ok": True,
            "booking_id": booking_id,
            "updated_fields": len(update_fields),
            "sheets_updated": False,
            "db_updated": True,
            "message": "Бронь обновлена (без изменений в Google Sheets)"
        })

    except Exception as e:
        print(f"❌ Ошибка обновления брони: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )
