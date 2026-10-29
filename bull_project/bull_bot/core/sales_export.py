"""Complete sales fields shared by CSV and Excel downloads."""
import csv
import json
from datetime import date, datetime


LABELS = {
    "record_type": "Тип записи", "id": "ID", "manager_id": "ID менеджера",
    "manager_full_name": "ФИО менеджера", "manager_username": "Telegram менеджера",
    "manager_name_text": "Менеджер в брони", "table_id": "ID Google-таблицы",
    "sheet_name": "Лист", "sheet_row_number": "Строка в таблице",
    "package_name": "Пакет", "region": "Регион", "departure_city": "Город вылета",
    "source": "Источник клиента", "amount_paid": "Оплачено", "exchange_rate": "Курс",
    "discount": "Скидка", "avia_request": "Авиа-запрос", "visa_status": "Статус визы",
    "avia": "Авиа", "room_type": "Тип номера", "meal_type": "Питание", "train": "Поезд",
    "guest_last_name": "Фамилия", "guest_first_name": "Имя", "gender": "Пол",
    "date_of_birth": "Дата рождения", "passport_num": "Номер паспорта",
    "passport_expiry": "Срок паспорта", "guest_iin": "ИИН",
    "contract_number": "Номер договора", "group_members": "Участники группы (JSON)",
    "price": "Стоимость", "comment": "Комментарий", "client_phone": "Телефон клиента",
    "placement_type": "Размещение", "passport_image_path": "Путь к паспорту",
    "passport_warning": "Предупреждение по паспорту", "status": "Статус",
    "created_at": "Дата создания", "updated_at": "Дата изменения",
    "pilgrim_data": "Паломники (JSON)", "google_sheet_row": "Строка OPEN DATE",
}


def export_value(value):
    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def csv_value(value):
    value = export_value(value)
    # A quoted CSV field alone does not prevent Excel from executing formulas.
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def write_csv(output, datasets):
    """One table with a record type; no status, period or row limit."""
    fields = ["record_type"]
    for _, columns, _ in datasets:
        fields.extend(key for key in columns if key not in fields)
    writer = csv.writer(output, delimiter=";", lineterminator="\r\n")
    output.write("\ufeff")  # Excel detects Cyrillic as UTF-8.
    writer.writerow([LABELS.get(key, key) for key in fields])
    for title, _, rows in datasets:
        for row in rows:
            writer.writerow([
                csv_value(title if key == "record_type" else row.get(key))
                for key in fields
            ])


def write_xlsx(path, datasets):
    from openpyxl import Workbook
    from openpyxl.cell import WriteOnlyCell
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.utils.exceptions import IllegalCharacterError

    workbook = Workbook(write_only=True)
    try:
        for title, columns, rows in datasets:
            sheet = workbook.create_sheet(title)
            sheet.freeze_panes = "A2"
            for index, key in enumerate(columns, 1):
                sheet.column_dimensions[get_column_letter(index)].width = min(
                    45, max(18, len(LABELS.get(key, key)) + 2)
                )

            def cells(values, header=False):
                result = []
                for value in values:
                    value = export_value(value)
                    # Excel silently truncates longer cells; fail explicitly instead.
                    if isinstance(value, str) and len(value) > 32767:
                        raise ValueError("Поле превышает лимит Excel. Выберите CSV.")
                    try:
                        cell = WriteOnlyCell(sheet, value=value)
                    except IllegalCharacterError:
                        raise ValueError("Данные содержат символы, несовместимые с Excel. Выберите CSV.") from None
                    if isinstance(value, str):
                        cell.data_type = "s"  # Preserve phones, IDs, leading zeros and literal formulas.
                    if header:
                        cell.font = Font(bold=True, color="FFFFFF")
                        cell.fill = PatternFill("solid", fgColor="6B5D52")
                    result.append(cell)
                return result

            sheet.append(cells([LABELS.get(key, key) for key in columns], header=True))
            for row in rows:
                sheet.append(cells([row.get(key) for key in columns]))
            sheet.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{len(rows) + 1}"
        workbook.save(path)
    finally:
        workbook.close()


def write_export(path, format, datasets):
    if format == "csv":
        with open(path, "w", encoding="utf-8", newline="") as output:
            write_csv(output, datasets)
    else:
        write_xlsx(path, datasets)
