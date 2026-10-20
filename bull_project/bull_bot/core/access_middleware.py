from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery
from bull_project.bull_bot.core.access import has_access, REAUTH_MESSAGE, reauth_keyboard
from bull_project.bull_bot.database.requests import get_user_by_id


class AccessMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        from bull_project.bull_bot.handlers.booking_handlers import BookingFlow
        state = data["state"]
        text = getattr(event, "text", None) or ""
        command = text.split()[0].split("@")[0] if text else ""
        if command in ("/start", "/logout") or (
            isinstance(event, CallbackQuery) and event.data == "access:enter_password"
        ):
            return await handler(event, data)
        user = await get_user_by_id(event.from_user.id)
        if has_access(user):
            return await handler(event, data)
        current = await state.get_state()
        if not isinstance(event, CallbackQuery) and current in (
            BookingFlow.waiting_access_code.state,
            BookingFlow.waiting_registration_name.state,
        ):
            return await handler(event, data)
        await state.clear()
        await state.set_state(BookingFlow.waiting_access_code)
        if isinstance(event, CallbackQuery):
            await event.answer()
            await event.bot.send_message(event.from_user.id, REAUTH_MESSAGE, reply_markup=reauth_keyboard())
        else:
            await event.answer(REAUTH_MESSAGE, reply_markup=reauth_keyboard())
