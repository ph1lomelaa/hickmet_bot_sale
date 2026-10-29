"""Download the same sales database that feeds the admin analytics."""
import logging
import os
import tempfile
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool

from bull_project.bull_bot.core.sales_export import write_export
from bull_project.bull_bot.database.models import Booking, OpenDateBooking, User
from bull_project.bull_bot.database.setup import async_session

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/admin/export")
async def export_all_sales(format: Literal["csv", "xlsx"] = Query("xlsx")):
    # /api/admin/* is protected by the existing admin access middleware.
    datasets = []
    async with async_session() as session:
        for title, model in (("Продажи", Booking), ("OPEN DATE", OpenDateBooking)):
            columns = list(model.__table__.columns.keys())
            statement = (
                select(
                    *model.__table__.columns,
                    User.full_name.label("manager_full_name"),
                    User.username.label("manager_username"),
                )
                .outerjoin(User, model.manager_id == User.telegram_id)
                .order_by(model.id)
            )
            rows = (await session.execute(statement)).mappings().all()
            datasets.append((title, columns + ["manager_full_name", "manager_username"], rows))

    fd, path = tempfile.mkstemp(suffix="." + format)
    os.close(fd)
    try:
        await run_in_threadpool(write_export, path, format, datasets)
    except Exception as error:
        os.unlink(path)
        if isinstance(error, ValueError):
            raise HTTPException(status_code=422, detail=str(error)) from error
        logger.exception("Sales export failed")
        raise HTTPException(status_code=500, detail="Не удалось создать выгрузку. Повторите попытку.") from error

    media_type = (
        "text/csv; charset=utf-8" if format == "csv"
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return FileResponse(
        path, media_type=media_type, filename=f"bull_sales_all_{stamp}.{format}",
        headers={"Cache-Control": "no-store"},
        background=BackgroundTask(os.unlink, path),
    )
