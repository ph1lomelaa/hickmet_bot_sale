"""Run: python -m unittest discover -s tests -v (uses only a temporary SQLite DB)."""
import asyncio
import hashlib
import hmac
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import AsyncMock, patch
from urllib.parse import urlencode

_test_dir = tempfile.TemporaryDirectory()
os.environ.update(API_TOKEN='123456789:test-token-for-access-checks', MANAGER_PASSWORD='new-secret',
                  DATABASE_URL='sqlite+aiosqlite:///' + _test_dir.name + '/test.db',
                  MOCK_MODE='true', SKIP_BOT='true')
# OCR is outside this suite: no model downloads or real passport processing.
sys.modules.setdefault('easyocr', types.ModuleType('easyocr'))
from bull_project.bull_bot.core.access import (
    has_access, manager_access_version, telegram_user_id, issue_upload_token,
)
from bull_project.bull_bot.database.models import User, Booking, OpenDateBooking
from bull_project.bull_bot.database.setup import init_db, async_session, engine
from bull_project.bull_bot.database.requests import add_user, get_user_by_id, get_booking_by_id
from bull_project.bull_bot.api.access import api_access_guard, router as access_router
from bull_project.bull_bot.api.routes.bookings import router as booking_router
from bull_project.bull_bot.api.routes.open_date import router as open_date_router
from bull_project.bull_bot.handlers.booking_handlers import check_code, register_name, enter_access_password, BookingFlow, _login_attempts
from bull_project.bull_bot.core.access_middleware import AccessMiddleware
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import Message, Chat, User as TelegramUser, CallbackQuery
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient


def signed(uid=101, stamp=None):
    values = {'auth_date': str(int(time.time()) if stamp is None else stamp),
              'user': json.dumps({'id': uid, 'first_name': 'Manager'})}
    check = '\n'.join(f'{k}={v}' for k, v in sorted(values.items()))
    key = hmac.new(b'WebAppData', os.environ['API_TOKEN'].encode(), hashlib.sha256).digest()
    values['hash'] = hmac.new(key, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(values)


app = FastAPI()
app.middleware('http')(api_access_guard)
app.include_router(access_router)
app.include_router(booking_router)
app.include_router(open_date_router)

@app.get('/api/probe')
async def probe(request: Request):
    return {'id': request.state.user.telegram_id}

@app.post('/api/passports/upload')
async def upload_probe(request: Request):
    return {'id': request.state.user.telegram_id}

@app.get('/api/admin/probe')
async def admin_probe():
    return {'ok': True}

@app.get('/api/care/passport-photo/{booking_id}')
async def media_probe(booking_id: int):
    return {'ok': True}


class AccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.new_event_loop()
        # Simulate an existing users table without the new access column.
        con = sqlite3.connect(_test_dir.name + '/test.db')
        con.execute('CREATE TABLE users (telegram_id BIGINT PRIMARY KEY, full_name VARCHAR, username VARCHAR, role VARCHAR, created_at DATETIME)')
        con.execute("INSERT INTO users VALUES (101, 'Original name', 'original', 'manager', CURRENT_TIMESTAMP)")
        con.commit(); con.close()
        cls.loop.run_until_complete(init_db())
        cls.loop.run_until_complete(init_db())
        cls.client = TestClient(app)
        cls.bot = Bot(os.environ['API_TOKEN'])

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.loop.run_until_complete(engine.dispose())
        cls.loop.run_until_complete(cls.bot.session.close())
        cls.loop.close()

    def run_async(self, task):
        return self.loop.run_until_complete(task)

    def setUp(self):
        os.environ['MANAGER_PASSWORD'] = 'new-secret'
        os.environ['MANAGER_ACCESS_VERSION'] = '1'
        _login_attempts.clear()
        self.run_async(add_user(101, 'Original name', 'original', 'manager'))
        self.run_async(add_user(102, 'Other', 'other', 'manager', manager_access_version()))
        self.run_async(add_user(201, 'Admin', 'admin', 'admin'))
        self.run_async(add_user(301, 'Care', 'care', 'care'))

    def authorize(self):
        self.run_async(add_user(101, 'Original name', 'original', 'manager', manager_access_version()))

    def headers(self, uid=101):
        return {'X-Telegram-Init-Data': signed(uid)}

    def message(self, text):
        return Message(message_id=1, date=int(time.time()), chat=Chat(id=101, type='private'),
                       from_user=TelegramUser(id=101, is_bot=False, first_name='New name', username='renamed'),
                       text=text).as_(self.bot)

    def state(self):
        return FSMContext(MemoryStorage(), StorageKey(bot_id=self.bot.id, chat_id=101, user_id=101))

    def test_legacy_manager_requires_login(self):
        self.assertFalse(has_access(self.run_async(get_user_by_id(101))))
        r = self.client.get('/api/probe', headers=self.headers())
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()['code'], 'access_expired')

    def test_relogin_preserves_profile_and_booking(self):
        async def seed():
            async with async_session() as session:
                b = Booking(manager_id=101, guest_first_name='Existing', guest_last_name='Booking')
                session.add(b); await session.commit(); return b.id
        bid = self.run_async(seed())
        before = self.run_async(get_user_by_id(101))
        state = self.state()
        with patch.object(Message, 'answer', new_callable=AsyncMock), patch.object(Message, 'delete', new_callable=AsyncMock):
            self.run_async(check_code(self.message('new-secret'), state))
        after = self.run_async(get_user_by_id(101))
        booking = self.run_async(get_booking_by_id(bid))
        self.assertEqual(after.full_name, before.full_name)
        self.assertEqual(after.created_at, before.created_at)
        self.assertEqual(booking.manager_id, 101)
        self.assertTrue(has_access(after))
        r = self.client.get('/api/history/101', headers=self.headers())
        self.assertEqual(r.status_code, 200)
        self.assertIn(str(bid), r.text)
        self.assertIsNone(self.run_async(state.get_state()))

    def test_password_or_version_rotation_revokes_access(self):
        self.authorize()
        self.assertEqual(self.client.get('/api/probe', headers=self.headers()).status_code, 200)
        os.environ['MANAGER_PASSWORD'] = 'rotated-secret'
        self.assertEqual(self.client.get('/api/probe', headers=self.headers()).status_code, 403)
        os.environ['MANAGER_PASSWORD'] = 'new-secret'
        os.environ['MANAGER_ACCESS_VERSION'] = '2'
        self.assertEqual(self.client.get('/api/probe', headers=self.headers()).status_code, 403)

    def test_old_password_cannot_reauthorize(self):
        with patch.object(Message, 'answer', new_callable=AsyncMock), patch.object(Message, 'delete', new_callable=AsyncMock):
            self.run_async(check_code(self.message('SALE'), self.state()))
        self.assertFalse(has_access(self.run_async(get_user_by_id(101))))

    def test_registration_started_before_rotation_cannot_finish(self):
        state = self.state()
        self.run_async(state.update_data(reg_role='manager', reg_access_version=manager_access_version()))
        os.environ['MANAGER_ACCESS_VERSION'] = '2'
        with patch.object(Message, 'answer', new_callable=AsyncMock):
            self.run_async(register_name(self.message('Forged new name'), state))
        self.assertFalse(has_access(self.run_async(get_user_by_id(101))))
        self.assertEqual(self.run_async(state.get_state()), BookingFlow.waiting_access_code.state)

    def test_old_callback_and_in_progress_flow_are_blocked(self):
        state = self.state()
        self.run_async(state.set_state(BookingFlow.waiting_count))
        handler = AsyncMock()
        with patch.object(Message, 'answer', new_callable=AsyncMock):
            self.run_async(AccessMiddleware()(handler, self.message('3'), {'state': state}))
        handler.assert_not_awaited()
        callback = CallbackQuery(id='old', from_user=self.message('').from_user, chat_instance='old', data='create_booking').as_(self.bot)
        with patch.object(CallbackQuery, 'answer', new_callable=AsyncMock), patch.object(Bot, 'send_message', new_callable=AsyncMock):
            self.run_async(AccessMiddleware()(handler, callback, {'state': state}))
        handler.assert_not_awaited()

    def test_admin_and_care_keep_access(self):
        for uid in (201, 301):
            self.assertEqual(self.client.get('/api/probe', headers=self.headers(uid)).status_code, 200)
        self.assertEqual(self.client.get('/api/admin/probe', headers=self.headers(301)).status_code, 403)
        self.assertEqual(self.client.get('/api/admin/probe', headers=self.headers(201)).status_code, 200)

    def test_forged_missing_expired_telegram_identity_denied(self):
        self.authorize()
        for raw in ('', signed().replace('101', '102'), signed(stamp=1), signed(stamp=int(time.time()) + 300)):
            self.assertEqual(self.client.get('/api/probe', headers={'X-Telegram-Init-Data': raw}).status_code, 401)
        self.assertEqual(telegram_user_id(signed()), 101)

    def test_direct_submit_does_not_create_or_reactivate_user(self):
        payload = {'pilgrims': [], 'package_name': 'P', 'sheet_name': 'S', 'table_id': 'T', 'manager_id': 101}
        for endpoint in ('/api/bookings/submit', '/api/open-date/submit'):
            self.assertEqual(self.client.post(endpoint, json=payload, headers=self.headers()).status_code, 403)
        self.assertFalse(has_access(self.run_async(get_user_by_id(101))))
        self.authorize()
        self.assertEqual(self.client.post('/api/bookings/submit', json=payload, headers=self.headers()).status_code, 400)
        self.assertTrue(has_access(self.run_async(get_user_by_id(101))))

    def test_cannot_impersonate_or_read_other_history(self):
        self.authorize()
        self.assertEqual(self.client.get('/api/history/102', headers=self.headers()).status_code, 403)
        r = self.client.post('/api/bookings/submit', json={'manager_id': 102}, headers=self.headers())
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.client.get('/api/open-date/list', headers=self.headers()).status_code, 403)

    def test_other_booking_and_open_date_cannot_be_changed(self):
        self.authorize()
        async def seed():
            async with async_session() as session:
                b = Booking(manager_id=102)
                o = OpenDateBooking(manager_id=102)
                session.add_all([b, o]); await session.commit(); return b.id, o.id
        bid, oid = self.run_async(seed())
        for method, path, body in (
            ('GET', f'/api/bookings/{bid}', None),
            ('PATCH', f'/api/bookings/{bid}', {}),
            ('POST', '/api/bookings/cancel/request', {'booking_id': bid}),
            ('POST', '/api/bookings/reschedule/request', {'old_booking_ids': [bid]}),
            ('POST', f'/api/open-date/convert/{oid}', {}),
        ):
            self.assertEqual(self.client.request(method, path, json=body, headers=self.headers()).status_code, 403)

    def test_media_token_scoped_and_revoked_with_access(self):
        self.authorize()
        async def seed():
            async with async_session() as session:
                b = Booking(manager_id=101); session.add(b); await session.commit(); return b.id
        bid = self.run_async(seed()); path = f'/api/care/passport-photo/{bid}'
        response = self.client.get('/api/access/media-token', params={'path': path}, headers=self.headers())
        self.assertEqual(response.status_code, 200)
        token = response.json()['token']
        self.assertEqual(self.client.get(path, params={'access_token': token}).status_code, 200)
        self.assertEqual(self.client.get(f'/api/care/passport-photo/{bid+1}', params={'access_token': token}).status_code, 401)
        os.environ['MANAGER_ACCESS_VERSION'] = '2'
        self.assertEqual(self.client.get(path, params={'access_token': token}).status_code, 403)

    def test_internal_upload_token_is_scoped_and_revocable(self):
        self.authorize(); token = issue_upload_token(101)
        headers = {'X-Bot-Upload-Token': token}
        self.assertEqual(self.client.post('/api/passports/upload', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/api/probe', headers=headers).status_code, 401)
        os.environ['MANAGER_ACCESS_VERSION'] = '2'
        self.assertEqual(self.client.post('/api/passports/upload', headers=headers).status_code, 403)

    def test_new_user_registration_gets_current_access(self):
        state = self.state()
        message = self.message('new-secret').model_copy(update={
            'from_user': TelegramUser(id=401, is_bot=False, first_name='New'),
        }).as_(self.bot)
        with patch.object(Message, 'answer', new_callable=AsyncMock), patch.object(Message, 'delete', new_callable=AsyncMock):
            self.run_async(check_code(message, state))
            self.assertEqual(self.run_async(state.get_state()), BookingFlow.waiting_registration_name.state)
            self.run_async(register_name(message.model_copy(update={'text': 'New manager'}).as_(self.bot), state))
        user = self.run_async(get_user_by_id(401))
        self.assertEqual(user.full_name, 'New manager')
        self.assertTrue(has_access(user))

    def test_actual_api_startup_cors_and_preflight(self):
        from bull_project.bull_bot.core.api_server import app as real_app
        with TestClient(real_app) as client:
            self.assertEqual(client.get('/health').status_code, 200)
            response = client.get('/api/packages?date=2026-10-20', headers={'Origin': 'https://ph1lomelaa.github.io'})
            self.assertEqual(response.status_code, 401)
            self.assertIn(response.headers.get('access-control-allow-origin'), ('*', 'https://ph1lomelaa.github.io'))
            response = client.options('/api/bookings/submit', headers={
                'Origin': 'https://ph1lomelaa.github.io', 'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'x-telegram-init-data,content-type',
            })
            self.assertEqual(response.status_code, 200)
            with self.assertRaises(Exception):
                with client.websocket_connect('/ws/phones'):
                    pass

    def test_password_button_prompts_and_preserves_profile(self):
        state = self.state()
        self.run_async(state.update_data(old_booking=123))
        callback = CallbackQuery(id='reauth', from_user=self.message('').from_user,
                                chat_instance='test', data='access:enter_password').as_(self.bot)
        handler = AsyncMock()
        self.run_async(AccessMiddleware()(handler, callback, {'state': state}))
        handler.assert_awaited_once()
        with patch.object(CallbackQuery, 'answer', new_callable=AsyncMock), patch.object(Bot, 'send_message', new_callable=AsyncMock) as sent:
            self.run_async(enter_access_password(callback, state))
        self.assertEqual(self.run_async(state.get_state()), BookingFlow.waiting_access_code.state)
        self.assertIn('Отправьте новый пароль', sent.call_args.args[1])
        self.assertFalse(has_access(self.run_async(get_user_by_id(101))))
        self.assertEqual(self.run_async(get_user_by_id(101)).full_name, 'Original name')

    def test_rotation_notification_sent_once_only_to_stale_managers(self):
        from bull_project.bull_bot.core.access_notifications import notify_managers_about_access
        from sqlalchemy import update
        async def reset_notices():
            async with async_session() as session:
                await session.execute(update(User).values(manager_access_notice_version=None))
                await session.commit()
        self.run_async(reset_notices())
        bot = types.SimpleNamespace(send_message=AsyncMock())
        with patch('bull_project.bull_bot.core.access_notifications.asyncio.sleep', new_callable=AsyncMock):
            self.run_async(notify_managers_about_access(bot))
            self.run_async(notify_managers_about_access(bot))
        bot.send_message.assert_awaited_once()
        self.assertEqual(bot.send_message.call_args.args[0], 101)
        self.assertIn('Ассалям алейкум', bot.send_message.call_args.args[1])
        button = bot.send_message.call_args.kwargs['reply_markup'].inline_keyboard[0][0]
        self.assertEqual(button.text, '🔑 Ввести пароль')
        self.assertEqual(button.callback_data, 'access:enter_password')
        self.assertFalse(has_access(self.run_async(get_user_by_id(101))))
        os.environ['MANAGER_ACCESS_VERSION'] = '2'
        with patch('bull_project.bull_bot.core.access_notifications.asyncio.sleep', new_callable=AsyncMock):
            self.run_async(notify_managers_about_access(bot))
        self.assertGreater(bot.send_message.await_count, 1)

    def test_login_attempt_limit(self):
        answer = AsyncMock()
        with patch.object(Message, 'answer', answer), patch.object(Message, 'delete', new_callable=AsyncMock):
            for _ in range(5): self.run_async(check_code(self.message('wrong'), self.state()))
            self.run_async(check_code(self.message('new-secret'), self.state()))
        self.assertIn('5 минут', answer.call_args.args[0])
        self.assertFalse(has_access(self.run_async(get_user_by_id(101))))


if __name__ == '__main__':
    unittest.main()
