"""Run: python -m unittest discover -s tests -p test_sales_export.py -v."""
import asyncio
import csv
import io
import json
import os
from datetime import datetime
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from bull_project.bull_bot.api.routes import sales_export
from bull_project.bull_bot.database.models import Base, Booking, OpenDateBooking, User


class SalesExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.engine = create_async_engine(
            "sqlite+aiosqlite:///" + cls.directory.name + "/sales.db", poolclass=NullPool
        )
        cls.sessions = async_sessionmaker(cls.engine)

        async def seed():
            async with cls.engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
            async with cls.sessions() as session:
                session.add(User(telegram_id=100, full_name="Менеджер Әлия", username="aliya"))
                session.add_all([
                    Booking(id=1, manager_id=100, guest_first_name="Әлия", guest_iin="001234567890",
                            client_phone="+77001234567", price="123.45", status="cancelled",
                            created_at=datetime(2020, 1, 1),
                            comment='Строка; с "кавычками"\nи переносом',
                            group_members=[{"first_name": "Гость", "iin": "000111222333"}]),
                    Booking(id=2, manager_id=999, status="rescheduled", comment="=1+1"),
                    Booking(id=3, manager_id=100, status="new", comment="@SUM(A1:A2)"),
                    OpenDateBooking(id=1, manager_id=100, status="OPEN",
                                    pilgrim_data=[{"first_name": "Паломник"}]),
                ])
                await session.commit()
        asyncio.run(seed())
        cls.session_patch = patch.object(sales_export, "async_session", cls.sessions)
        cls.session_patch.start()
        app = FastAPI()
        app.include_router(sales_export.router)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.session_patch.stop()
        asyncio.run(cls.engine.dispose())
        cls.directory.cleanup()

    def test_csv_includes_all_dates_statuses_open_date_and_orphan_manager(self):
        response = self.client.get("/api/admin/export?format=csv&start_date=2026-10-29")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"\xef\xbb\xbf"))
        rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))
        self.assertEqual(len(rows), 4)
        self.assertEqual([row["Статус"] for row in rows], ["cancelled", "rescheduled", "new", "OPEN"])
        self.assertEqual(rows[0]["ИИН"], "001234567890")
        self.assertEqual(rows[0]["ФИО менеджера"], "Менеджер Әлия")
        self.assertEqual(rows[0]["Дата создания"], "2020-01-01T00:00:00")
        self.assertEqual(rows[0]["Комментарий"], 'Строка; с "кавычками"\nи переносом')
        self.assertEqual(json.loads(rows[0]["Участники группы (JSON)"])[0]["iin"], "000111222333")
        self.assertEqual(rows[1]["Комментарий"], "'=1+1")
        self.assertEqual(rows[1]["ФИО менеджера"], "")
        self.assertEqual(rows[-1]["Тип записи"], "OPEN DATE")
        self.assertEqual(json.loads(rows[-1]["Паломники (JSON)"])[0]["first_name"], "Паломник")
        self.assertIn("no-store", response.headers["cache-control"])

    def test_xlsx_preserves_text_and_has_two_complete_sheets(self):
        response = self.client.get("/api/admin/export?format=xlsx")
        self.assertEqual(response.status_code, 200)
        self.assertIn(".xlsx", response.headers["content-disposition"])
        book = load_workbook(io.BytesIO(response.content))
        try:
            self.assertEqual(book.sheetnames, ["Продажи", "OPEN DATE"])
            sheet = book["Продажи"]
            self.assertEqual(sheet.max_row, 4)
            self.assertEqual(book["OPEN DATE"].max_row, 2)
            columns = {cell.value: cell.column for cell in sheet[1]}
            for label, expected in (("ИИН", "001234567890"), ("Телефон клиента", "+77001234567")):
                cell = sheet.cell(2, columns[label])
                self.assertEqual(cell.value, expected)
                self.assertEqual(cell.data_type, "s")
            cell = sheet.cell(3, columns["Комментарий"])
            self.assertEqual(cell.value, "=1+1")
            self.assertEqual(cell.data_type, "s")
            self.assertEqual(sheet.freeze_panes, "A2")
            self.assertIsNotNone(sheet.auto_filter.ref)
        finally:
            book.close()

    def test_unsupported_format_is_rejected(self):
        self.assertEqual(self.client.get("/api/admin/export?format=pdf").status_code, 422)

    def test_empty_database_still_downloads_headers_in_both_formats(self):
        async def empty():
            engine = create_async_engine("sqlite+aiosqlite:///:memory:")
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
            return engine, async_sessionmaker(engine)
        engine, sessions = asyncio.run(empty())
        try:
            with patch.object(sales_export, "async_session", sessions):
                csv_response = self.client.get("/api/admin/export?format=csv")
                xlsx_response = self.client.get("/api/admin/export?format=xlsx")
            self.assertEqual(csv_response.status_code, 200)
            self.assertEqual(len(list(csv.reader(io.StringIO(csv_response.content.decode("utf-8-sig")), delimiter=";"))), 1)
            self.assertEqual(xlsx_response.status_code, 200)
            book = load_workbook(io.BytesIO(xlsx_response.content))
            try:
                self.assertEqual([s.max_row for s in book], [1, 1])
            finally:
                book.close()
        finally:
            asyncio.run(engine.dispose())

    def test_temporary_download_files_are_removed(self):
        with patch.object(sales_export.tempfile, "tempdir", self.directory.name):
            self.assertEqual(self.client.get("/api/admin/export?format=csv").status_code, 200)
            self.assertEqual(self.client.get("/api/admin/export?format=xlsx").status_code, 200)
        self.assertEqual([p.name for p in Path(self.directory.name).iterdir()], ["sales.db"])


if __name__ == "__main__":
    unittest.main()
