from fastapi import APIRouter
from fastapi.responses import JSONResponse

from bull_project.bull_bot.core.google_sheets.writer import (
    clear_booking_in_sheets,
    write_cancelled_booking_red,
    write_rescheduled_booking_red,
    save_group_booking,
)
from bull_project.bull_bot.database.requests import (
    get_pending_requests,
    get_booking_by_id,
    get_approval_request,
    update_approval_status,
    delete_admin_request_inbox,
    mark_booking_cancelled,
    mark_booking_rescheduled,
    update_booking_fields,
    update_booking_row,
)


router = APIRouter()


@router.get("/api/admin/requests")
async def admin_requests():
    try:
        pending = await get_pending_requests()
        result = []
        for req in pending:
            booking = await get_booking_by_id(req.booking_id)
            if not booking:
                continue
            group_members = booking.group_members if booking.group_members else []
            result.append({
                "id": req.id,
                "booking_id": booking.id,
                "request_type": req.request_type,
                "status": req.status,
                "created_at": req.created_at.isoformat() if req.created_at else None,
                "initiator_id": req.initiator_id,
                "comment": req.comment,
                "booking": {
                    "package_name": booking.package_name,
                    "sheet_name": booking.sheet_name,
                    "table_id": booking.table_id,
                    "sheet_row_number": booking.sheet_row_number,
                    "guest_last_name": booking.guest_last_name,
                    "guest_first_name": booking.guest_first_name,
                    "client_phone": booking.client_phone,
                    "placement_type": booking.placement_type,
                    "room_type": booking.room_type,
                    "meal_type": booking.meal_type,
                    "price": booking.price,
                    "amount_paid": booking.amount_paid,
                    "region": booking.region,
                    "departure_city": booking.departure_city,
                    "source": booking.source,
                    "comment": booking.comment,
                    "manager_name_text": booking.manager_name_text,
                    "group_members": group_members,
                },
            })
        return {"ok": True, "data": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@router.post("/api/admin/requests/{req_id}/approve")
async def admin_request_approve(req_id: int):
    try:
        req = await get_approval_request(req_id)
        if not req or req.status != "pending":
            return JSONResponse(status_code=404, content={"ok": False, "error": "not found"})
        booking = await get_booking_by_id(req.booking_id)
        if not booking:
            return JSONResponse(status_code=404, content={"ok": False, "error": "booking not found"})

        if req.request_type == "cancel":
            sheets_cleared = False
            guest_name = f"{booking.guest_last_name} {booking.guest_first_name}"

            if booking.sheet_row_number and booking.table_id and booking.sheet_name:
                try:
                    sheets_cleared = await clear_booking_in_sheets(
                        booking.table_id,
                        booking.sheet_name,
                        booking.sheet_row_number,
                        booking.package_name,
                        expected_guest_name=guest_name,  # 🔒 Проверяем имя перед удалением
                    )
                    if not sheets_cleared:
                        print(f"⚠️ Не удалось очистить бронь #{booking.id} в таблице (возможно несовпадение имени)")
                except Exception as e:
                    print(f"❌ Ошибка при очистке брони #{booking.id} в таблице: {e}")
                    sheets_cleared = False

            red_written = False
            if booking.table_id and booking.sheet_name and booking.package_name:
                try:
                    red_written = await write_cancelled_booking_red(
                        booking.table_id,
                        booking.sheet_name,
                        booking.package_name,
                        guest_name,
                    )
                    if not red_written:
                        print(f"⚠️ Не удалось записать отменённую бронь #{booking.id} в красный список")
                except Exception as e:
                    print(f"❌ Ошибка при записи в красный список для брони #{booking.id}: {e}")
                    red_written = False

            await mark_booking_cancelled(booking.id)
            await update_approval_status(req_id, "approved")
            await delete_admin_request_inbox(req_id)
            return {"ok": True, "status": "cancelled", "sheets_cleared": sheets_cleared, "red_written": red_written}

        if req.request_type == "reschedule":
            old_id = None
            if req.comment and req.comment.startswith("old:"):
                try:
                    old_id = int(req.comment.split("old:")[1])
                except Exception:
                    old_id = None
            old_booking = await get_booking_by_id(old_id) if old_id else None

            common_data = {
                'table_id': booking.table_id,
                'sheet_name': booking.sheet_name,
                'package_name': booking.package_name,
                'room_type': booking.room_type,
                'meal_type': booking.meal_type,
                'price': booking.price,
                'amount_paid': booking.amount_paid,
                'exchange_rate': booking.exchange_rate,
                'discount': booking.discount,
                'contract_number': booking.contract_number,
                'region': booking.region,
                'departure_city': booking.departure_city,
                'source': booking.source,
                'comment': booking.comment,
                'manager_name_text': booking.manager_name_text,
                'train': booking.train,
                'visa_status': booking.visa_status,
                'avia': booking.avia,
            }
            person = {
                "Last Name": booking.guest_last_name,
                "First Name": booking.guest_first_name,
                "Gender": booking.gender,
                "Date of Birth": booking.date_of_birth,
                "Document Number": booking.passport_num,
                "Document Expiration": booking.passport_expiry,
                "IIN": booking.guest_iin,
                "client_phone": booking.client_phone,
                "passport_image_path": booking.passport_image_path,
            }
            saved_rows = await save_group_booking([person], common_data, booking.placement_type or 'separate')
            if saved_rows:
                await update_booking_row(booking.id, saved_rows[0])
                await update_booking_fields(booking.id, {"status": "new"})
            else:
                return JSONResponse(status_code=500, content={"ok": False, "error": "sheet write failed"})

            # 🔄 УДАЛЯЕМ СТАРУЮ БРОНЬ ПРИ ПЕРЕНОСЕ
            if old_booking:
                old_guest_name = f"{old_booking.guest_last_name} {old_booking.guest_first_name}"

                # Очищаем старую бронь из таблицы
                if old_booking.sheet_row_number and old_booking.table_id and old_booking.sheet_name:
                    try:
                        cleared = await clear_booking_in_sheets(
                            old_booking.table_id,
                            old_booking.sheet_name,
                            old_booking.sheet_row_number,
                            old_booking.package_name,
                            expected_guest_name=old_guest_name,  # 🔒 Проверяем имя перед удалением
                        )
                        if cleared:
                            print(f"✅ Старая бронь #{old_booking.id} очищена из таблицы")
                        else:
                            print(f"⚠️ Не удалось очистить старую бронь #{old_booking.id} (возможно несовпадение имени или ошибка)")
                    except Exception as e:
                        print(f"❌ ОШИБКА при очистке старой брони #{old_booking.id}: {e}")

                # Записываем в красный список (перенос)
                try:
                    red_written = await write_rescheduled_booking_red(
                        old_booking.table_id,
                        old_booking.sheet_name,
                        old_booking.package_name,
                        old_guest_name
                    )
                    if red_written:
                        print(f"✅ Старая бронь #{old_booking.id} записана в красный список (перенос)")
                    else:
                        print(f"⚠️ Не удалось записать старую бронь #{old_booking.id} в красный список")
                except Exception as e:
                    print(f"❌ ОШИБКА при записи в красный список для старой брони #{old_booking.id}: {e}")

                # Помечаем старую бронь как перенесённую в БД
                await mark_booking_rescheduled(old_booking.id, comment=f"Перенесено в #{booking.id}")

            await update_approval_status(req_id, "approved")
            await delete_admin_request_inbox(req_id)
            return {"ok": True, "status": "rescheduled", "saved_rows": saved_rows}

        return JSONResponse(status_code=400, content={"ok": False, "error": "unknown type"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@router.post("/api/admin/requests/{req_id}/reject")
async def admin_request_reject(req_id: int):
    try:
        req = await get_approval_request(req_id)
        if not req or req.status != "pending":
            return JSONResponse(status_code=404, content={"ok": False, "error": "not found"})
        booking = await get_booking_by_id(req.booking_id)
        if req.request_type == "reschedule":
            old_id = None
            if req.comment and req.comment.startswith("old:"):
                try:
                    old_id = int(req.comment.split("old:")[1])
                except Exception:
                    old_id = None
            if booking:
                await update_booking_fields(booking.id, {"status": "cancelled"})
            if old_id:
                await update_booking_fields(old_id, {"status": "new"})
        else:
            if booking:
                await update_booking_fields(booking.id, {"status": "new"})
        await update_approval_status(req_id, "rejected")
        await delete_admin_request_inbox(req_id)
        return {"ok": True, "status": "rejected"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})
