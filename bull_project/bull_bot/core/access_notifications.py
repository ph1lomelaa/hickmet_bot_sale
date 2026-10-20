"""Notify existing managers once per access version, without changing their profiles."""
import asyncio
import logging
from sqlalchemy import select, update, or_
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from bull_project.bull_bot.database.models import User
from bull_project.bull_bot.database.setup import async_session
from bull_project.bull_bot.core.access import manager_access_version, has_access, REAUTH_MESSAGE, reauth_keyboard
from bull_project.bull_bot.database.requests import get_user_by_id

logger = logging.getLogger(__name__)


async def pending_manager_ids(version):
    async with async_session() as session:
        result = await session.scalars(select(User.telegram_id).where(
            User.role == "manager",
            or_(User.manager_access_version.is_(None), User.manager_access_version != version),
            or_(User.manager_access_notice_version.is_(None), User.manager_access_notice_version != version),
        ))
        return list(result)


async def mark_notified(user_id, version):
    async with async_session() as session:
        await session.execute(update(User).where(User.telegram_id == user_id).values(
            manager_access_notice_version=version))
        await session.commit()


async def notify_managers_about_access(bot):
    version = manager_access_version()
    if not version:
        return
    for user_id in await pending_manager_ids(version):
        user = await get_user_by_id(user_id)
        if not user or user.role != "manager" or has_access(user):
            continue
        try:
            try:
                await bot.send_message(user_id, REAUTH_MESSAGE, reply_markup=reauth_keyboard())
            except TelegramRetryAfter as exc:
                await asyncio.sleep(exc.retry_after)
                await bot.send_message(user_id, REAUTH_MESSAGE, reply_markup=reauth_keyboard())
            await mark_notified(user_id, version)
        except TelegramForbiddenError:
            # A blocked bot cannot deliver messages. Other managers must still be notified.
            await mark_notified(user_id, version)
        except Exception:
            logger.exception("Could not send access update to manager %s", user_id)
        await asyncio.sleep(0.05)
