import os
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse, Response
from starlette.concurrency import run_in_threadpool

from bull_project.bull_bot.api.utils import check_passport_expiry
from bull_project.bull_bot.config.constants import ABS_UPLOADS_DIR
from bull_project.bull_bot.core.parsers.passport_parser import PassportParserEasyOCR as PassportParser
from bull_project.bull_bot.core.passport_storage import resolve_passport_file_path
from bull_project.bull_bot.database.requests import get_booking_by_id, get_latest_passport_for_person


router = APIRouter()

# uploads dir is shared via volume on API service
os.makedirs(ABS_UPLOADS_DIR, exist_ok=True)

# Инициализация парсера паспортов
passport_parser = PassportParser(debug=False)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@router.post("/api/passport/parse")
async def api_passport_parse(file: UploadFile = File(...)):
    """Парсинг паспорта и извлечение данных + сохранение файла."""
    try:
        import time
        from pdf2image import convert_from_path
        from PIL import Image

        # Создаем директорию для uploads если её нет
        uploads_dir = os.path.join(PROJECT_ROOT, "tmp", "uploads")
        os.makedirs(uploads_dir, exist_ok=True)

        # Генерируем уникальное имя файла
        timestamp = int(time.time() * 1000)
        ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
        temp_path = f"/tmp/passport_{timestamp}_temp{ext}"

        # Сохраняем временный файл
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        print(f"📥 Веб-форма: файл загружен {temp_path}")

        # Конвертируем в PNG
        png_path = os.path.join(uploads_dir, f"web_{timestamp}.png")

        try:
            if temp_path.lower().endswith('.pdf'):
                # Конвертируем PDF в PNG
                print(f"🔄 Конвертация PDF в PNG...")
                poppler_path = os.getenv("POPPLER_PATH", "/opt/homebrew/bin")
                pages = convert_from_path(temp_path, dpi=500, poppler_path=poppler_path)
                if pages:
                    pages[0].save(png_path, 'PNG')
                    print(f"✅ PDF сконвертирован: {png_path}")
            else:
                # Конвертируем изображение в PNG
                img = Image.open(temp_path)
                img.save(png_path, 'PNG')
                print(f"✅ Изображение сохранено: {png_path}")
        except Exception as conv_err:
            print(f"⚠️ Ошибка конвертации: {conv_err}, используем оригинал")
            png_path = temp_path

        # Парсим паспорт
        passport_data = await run_in_threadpool(passport_parser.parse, temp_path)

        # Удаляем временный файл (если это не финальный файл)
        if temp_path != png_path and os.path.exists(temp_path):
            os.remove(temp_path)

        if not passport_data.is_valid:
            # Удаляем сохраненный файл если данные невалидны
            if os.path.exists(png_path):
                os.remove(png_path)
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "Не удалось распознать данные паспорта"}
            )

        result_data = passport_data.to_dict()
        result_data['passport_image_path'] = png_path

        print(f"✅ Веб-форма: паспорт сохранен в {png_path}")

        return {
            "ok": True,
            "data": result_data
        }

    except Exception as e:
        print(f"❌ Ошибка парсинга паспорта через веб-форму: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": f"Ошибка обработки файла: {str(e)}"}
        )


@router.post("/api/passports/upload")
async def api_passport_upload(file: UploadFile = File(...)):
    """
    Принимает файл паспорта от бота/веб-интерфейса, сохраняет, парсит и возвращает распознанные данные.
    """
    try:
        print(f"📥 Получен файл для загрузки: {file.filename}, тип: {file.content_type}")

        # Создаем директорию если не существует
        os.makedirs(ABS_UPLOADS_DIR, exist_ok=True)

        # Генерируем уникальное имя
        ts = int(datetime.now().timestamp() * 1000)
        orig_ext = os.path.splitext(file.filename or "")[1] or ".png"
        safe_ext = orig_ext if len(orig_ext) <= 5 else ".png"
        filename = f"bot_upload_{ts}{safe_ext}"
        target_path = os.path.join(ABS_UPLOADS_DIR, filename)

        print(f"💾 Сохранение файла: {target_path}")

        # Сохраняем файл
        try:
            with open(target_path, "wb") as f:
                content = await file.read()
                f.write(content)

            file_size = os.path.getsize(target_path)
            print(f"✅ Файл сохранен: {file_size / 1024:.2f} KB")
        except Exception as e:
            print(f"❌ Ошибка сохранения файла: {e}")
            raise Exception(f"Не удалось сохранить файл: {str(e)}")

        # Парсим паспорт с таймаутом
        passport_data = None
        try:
            print(f"🔍 Запуск распознавания паспорта...")

            from bull_project.bull_bot.core.parsers.passport_parser import PassportParser

            def parse_passport():
                try:
                    parser = PassportParser(debug=True)
                    return parser.parse(target_path)
                except Exception as e:
                    print(f"⚠️ Ошибка парсера: {e}")
                    return None

            import asyncio
            passport_data = await asyncio.wait_for(
                run_in_threadpool(parse_passport),
                timeout=45.0
            )

            if passport_data:
                print(f"✅ Паспорт распознан:")
                print(f"   Имя: {passport_data.first_name}")
                print(f"   Фамилия: {passport_data.last_name}")
                print(f"   Пол: {passport_data.gender}")
                print(f"   Дата рождения: {passport_data.dob}")
                print(f"   Номер документа: {passport_data.document_number}")
                print(f"   Срок действия: {passport_data.expiration_date}")
                print(f"   ИИН: {passport_data.iin}")
            else:
                print(f"⚠️ Паспорт не распознан, вернем только путь к файлу")

        except asyncio.TimeoutError:
            print(f"⏱️ Таймаут распознавания паспорта (>45 сек)")
            passport_data = None
        except Exception as e:
            print(f"⚠️ Ошибка распознавания паспорта: {e}")
            import traceback
            traceback.print_exc()
            passport_data = None

        # Формируем ответ
        parsed_data = {}
        passport_warning = None
        if passport_data:
            parsed_data = {
                "first_name": passport_data.first_name or "",
                "last_name": passport_data.last_name or "",
                "gender": passport_data.gender or "",
                "date_of_birth": passport_data.dob or "",
                "passport_num": passport_data.document_number or "",
                "passport_expiry": passport_data.expiration_date or "",
                "iin": passport_data.iin or "",
                "document_type": passport_data.document_type or "passport"
            }

            # 🔥 Предупреждение по паспорту — чтобы WebApp показывал сразу
            document_type = parsed_data.get("document_type") or "passport"
            expiry = (parsed_data.get("passport_expiry") or "").strip()
            if document_type == "id_card":
                passport_warning = "⚠️ Загружено удостоверение личности, требуется заграничный паспорт"
            elif not expiry or expiry == "-":
                passport_warning = "⚠️ Срок действия не распознан"
            else:
                passport_warning = check_passport_expiry(expiry)

            parsed_data["passport_warning"] = passport_warning

        # ВАЖНО: Возвращаем относительный путь (только имя файла)
        # Это позволяет использовать его в разных окружениях
        return {
            "ok": True,
            "path": filename,  # Возвращаем только имя файла, не полный путь
            "absolute_path": target_path,  # Для отладки
            "parsed_data": parsed_data,    # основной ключ
            "data": parsed_data,           # алиас для фронтов, ожидающих data
            "passport_warning": passport_warning,  # алиас на верхнем уровне для удобства
            "parsed": passport_data is not None
        }

    except Exception as e:
        print(f"❌ Критическая ошибка загрузки паспорта: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@router.get("/api/care/passport-photo/{booking_id}")
async def get_passport_photo(booking_id: int):
    """
    Возвращает фото паспорта для конкретной брони.
    """
    try:
        booking = await get_booking_by_id(booking_id)

        if not booking:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": "Booking not found"}
            )

        # Ищем актуальный путь: сначала в самой брони, иначе берём самое свежее фото по ФИО
        passport_path = booking.passport_image_path
        if not passport_path and booking.guest_last_name and booking.guest_first_name:
            passport_path = await get_latest_passport_for_person(
                booking.guest_last_name,
                booking.guest_first_name
            )

        if not passport_path:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": "No passport image for this booking"}
            )

        # Резолвим путь к паспорту (поддерживает и абсолютные, и относительные пути)
        resolved_path = resolve_passport_file_path(passport_path)

        # Проверяем существование файла
        if not resolved_path or not os.path.exists(resolved_path):
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": f"Passport image file not found. Original path: {passport_path}, tried to resolve to: {resolved_path or 'N/A'}"}
            )

        passport_path = resolved_path

        # Определяем тип файла по расширению
        file_ext = os.path.splitext(passport_path)[1].lower()
        media_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.pdf': 'application/pdf'
        }
        media_type = media_types.get(file_ext, 'image/png')  # По умолчанию PNG

        # Отдаем файл
        return FileResponse(
            passport_path,
            media_type=media_type,
            filename=f"passport_{booking_id}{file_ext}"
        )

    except Exception as e:
        print(f"❌ Ошибка получения фото паспорта: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@router.get("/api/care/passport-original/{booking_id}")
async def get_passport_original(booking_id: int):
    """
    Возвращает оригинальный файл паспорта (как он сохранен в uploads).
    Это полезно для внешнего OCR (Tesseract): без PDF-конвертации и без сжатия.
    """
    try:
        booking = await get_booking_by_id(booking_id)
        if not booking:
            return JSONResponse(status_code=404, content={"ok": False, "error": "Booking not found"})

        passport_path = booking.passport_image_path
        if not passport_path and booking.guest_last_name and booking.guest_first_name:
            passport_path = await get_latest_passport_for_person(booking.guest_last_name, booking.guest_first_name)

        if not passport_path:
            return JSONResponse(status_code=404, content={"ok": False, "error": "No passport file for this booking"})

        resolved_path = resolve_passport_file_path(passport_path)
        if not resolved_path or not os.path.exists(resolved_path):
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": f"Passport file not found: {passport_path}"}
            )

        file_ext = os.path.splitext(resolved_path)[1].lower()
        media_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.pdf': 'application/pdf'
        }
        media_type = media_types.get(file_ext, 'application/octet-stream')

        # Формируем имя файла из ФИО (как в PDF)
        import re
        last = (booking.guest_last_name or "passport").strip()
        first = (booking.guest_first_name or "").strip()
        safe = re.sub(r"[^a-zA-Z0-9_\\-]+", "_", f"{last}_{first}".strip("_"))
        download_name = f"{safe}_passport{file_ext}" if safe else f"passport_{booking_id}{file_ext}"

        return FileResponse(
            resolved_path,
            media_type=media_type,
            filename=download_name,
        )

    except Exception as e:
        print(f"❌ Ошибка получения оригинала паспорта: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@router.get("/api/care/passport-pdf/{booking_id}")
async def get_passport_pdf(
    booking_id: int,
    mode: str = Query("compact"),  # compact | ocr
    limit_mb: float = Query(1.0),
):
    """
    Возвращает паспорт в формате PDF с текстовым слоем (searchable PDF).
    Если оригинал - изображение, конвертирует в PDF с OCR.
    Если уже PDF - возвращает как есть.
    """
    try:
        booking = await get_booking_by_id(booking_id)

        if not booking:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": "Booking not found"}
            )

        # Формируем имя файла из ФИО
        import re
        last_name = (booking.guest_last_name or "").strip()
        first_name = (booking.guest_first_name or "").strip()

        # Безопасное имя файла: убираем спецсимволы
        safe_last_name = re.sub(r'[^\w\s-]', '', last_name).strip()
        safe_first_name = re.sub(r'[^\w\s-]', '', first_name).strip()

        if safe_last_name and safe_first_name:
            pdf_filename = f"{safe_last_name}_{safe_first_name}_passport.pdf"
        else:
            pdf_filename = f"passport_{booking_id}.pdf"

        # Ищем актуальный путь к паспорту
        passport_path = booking.passport_image_path
        if not passport_path and booking.guest_last_name and booking.guest_first_name:
            passport_path = await get_latest_passport_for_person(
                booking.guest_last_name,
                booking.guest_first_name
            )

        if not passport_path:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": "No passport image for this booking"}
            )

        # Резолвим путь к паспорту (поддерживает и абсолютные, и относительные пути)
        resolved_path = resolve_passport_file_path(passport_path)

        # Проверяем существование файла
        if not resolved_path or not os.path.exists(resolved_path):
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": f"Passport image file not found. Original path: {passport_path}, tried to resolve to: {resolved_path or 'N/A'}"}
            )

        passport_path = resolved_path

        mode = (mode or "compact").strip().lower()
        if mode not in {"compact", "ocr"}:
            mode = "compact"

        # Если уже PDF
        if passport_path.lower().endswith('.pdf'):
            # Для OCR режима отдаем оригинал (он уже в хорошем качестве)
            if mode == "ocr":
                return FileResponse(
                    passport_path,
                    media_type='application/pdf',
                    filename=pdf_filename,
                    headers={
                        'Content-Disposition': f'attachment; filename="{pdf_filename}"'
                    }
                )

            # Для compact режима: конвертируем PDF → изображение → компактный PDF
            # Проверяем размер оригинала
            original_size = os.path.getsize(passport_path)
            target_max_bytes = max(200_000, int(float(limit_mb or 1.0) * 1024 * 1024))

            # Если оригинал уже меньше лимита - отдаем как есть
            if original_size <= target_max_bytes:
                print(f"✅ PDF уже компактный ({original_size / 1024:.1f}KB ≤ {target_max_bytes / 1024:.1f}KB)")
                return FileResponse(
                    passport_path,
                    media_type='application/pdf',
                    filename=pdf_filename,
                    headers={
                        'Content-Disposition': f'attachment; filename="{pdf_filename}"'
                    }
                )

            # Нужно сжать PDF: конвертируем в изображение
            print(f"🔄 PDF слишком большой ({original_size / 1024:.1f}KB > {target_max_bytes / 1024:.1f}KB), конвертируем...")
            try:
                from pdf2image import convert_from_path

                # Конвертируем первую страницу PDF в изображение
                images = convert_from_path(passport_path, dpi=300, first_page=1, last_page=1)
                if not images:
                    raise Exception("Не удалось конвертировать PDF в изображение")

                img = images[0]
                print(f"✅ PDF конвертирован в изображение {img.size}")

                # Далее обрабатываем как обычное изображение (код ниже)

            except Exception as pdf_convert_error:
                print(f"⚠️ Ошибка конвертации PDF: {pdf_convert_error}")
                # Fallback: отдаем оригинал
                return FileResponse(
                    passport_path,
                    media_type='application/pdf',
                    filename=pdf_filename,
                    headers={
                        'Content-Disposition': f'attachment; filename="{pdf_filename}"'
                    }
                )
        else:
            # Если изображение - открываем его
            from PIL import Image
            img = Image.open(passport_path)
            img.load()

        # Общий код для создания компактного/OCR PDF из изображения
        try:
            import tempfile
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader
            import urllib.parse

            # Создаем временный PDF файл
            temp_pdf = tempfile.NamedTemporaryFile(
                suffix='.pdf',
                delete=False,
                dir=os.path.dirname(passport_path)
            )
            temp_pdf_path = temp_pdf.name
            temp_pdf.close()

            # Создаем PDF с изображением
            print(f"🔄 Создание PDF для паспорта {booking_id} (режим: {mode})...")

            # img уже открыто выше (либо из Image.open, либо из convert_from_path)

            # Для OCR/MRZ важен DPI: 250–300+.
            target_dpi = 300 if mode == "ocr" else 300
            target_max_bytes = max(200_000, int(float(limit_mb or 1.0) * 1024 * 1024))

            def prepare_jpeg(max_side: Optional[int], quality: int) -> tuple[bytes, int, int]:
                from PIL import Image as PILImage

                if img.mode != "RGB":
                    img_rgb = img.convert("RGB")
                else:
                    img_rgb = img

                w, h = img_rgb.size
                if max_side and max(w, h) > max_side:
                    scale = max_side / float(max(w, h))
                    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
                    img_rgb = img_rgb.resize(new_size, PILImage.LANCZOS)
                    w, h = img_rgb.size

                buf = io.BytesIO()
                img_rgb.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
                return buf.getvalue(), w, h

            def write_pdf_from_jpeg(jpeg_bytes: bytes, px_w: int, px_h: int):
                # Физический размер страницы подбираем под target_dpi, чтобы OCR видел четкий текст.
                page_w = px_w * 72.0 / float(target_dpi)
                page_h = px_h * 72.0 / float(target_dpi)
                c = canvas.Canvas(temp_pdf_path, pagesize=(page_w, page_h))
                c.setPageCompression(1)
                c.drawImage(ImageReader(io.BytesIO(jpeg_bytes)), 0, 0, width=page_w, height=page_h)
                c.save()

            if mode == "ocr":
                # OCR режим: максимум качества, не пытаемся ужать до лимита.
                jpeg_bytes, w, h = prepare_jpeg(max_side=None, quality=95)
                write_pdf_from_jpeg(jpeg_bytes, w, h)
            else:
                # compact: стараемся уложиться в limit_mb, но держим DPI 300 и не режем слишком сильно.
                presets = [
                    (3200, 92),
                    (3000, 90),
                    (2800, 88),
                    (2600, 86),
                    (2400, 84),
                    (2200, 82),
                    (2000, 80),
                    (1800, 78),
                ]
                last_size = None
                for (max_side, quality) in presets:
                    jpeg_bytes, w, h = prepare_jpeg(max_side=max_side, quality=quality)
                    write_pdf_from_jpeg(jpeg_bytes, w, h)
                    try:
                        last_size = os.path.getsize(temp_pdf_path)
                    except Exception:
                        last_size = None
                    if last_size is not None and last_size <= target_max_bytes:
                        break

            result_path = temp_pdf_path

            # Проверяем что файл создан и не пустой
            if not os.path.exists(result_path):
                raise Exception(f"PDF не создан: {result_path}")

            file_size = os.path.getsize(result_path)
            if file_size == 0:
                raise Exception("PDF файл пустой")

            print(f"✅ PDF создан: {file_size} байт, путь: {result_path}")

            # Читаем файл в память для гарантированной отправки
            with open(result_path, 'rb') as f:
                pdf_content = f.read()

            print(f"✅ PDF прочитан в память: {len(pdf_content)} байт")

            # Удаляем временный файл
            try:
                os.remove(result_path)
                print(f"🗑️ Временный файл удален: {result_path}")
            except Exception as e:
                print(f"⚠️ Не удалось удалить временный файл: {e}")

            # Кодируем имя файла по RFC 5987 для поддержки non-ASCII
            encoded_filename = urllib.parse.quote(pdf_filename)

            print(f"📤 Отправка PDF: {pdf_filename} ({encoded_filename})")

            # Возвращаем через Response с явным содержимым
            return Response(
                content=pdf_content,
                media_type='application/pdf',
                headers={
                    'Content-Disposition': f'attachment; filename="{pdf_filename}"; filename*=UTF-8\'\'{encoded_filename}',
                    'Content-Length': str(len(pdf_content)),
                    'Cache-Control': 'no-cache',
                }
            )

        except Exception as pdf_error:
            print(f"❌ Ошибка создания PDF: {pdf_error}")
            import traceback
            traceback.print_exc()

            # Fallback: отдаем оригинальное изображение
            file_ext = os.path.splitext(passport_path)[1].lower()
            media_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
            }
            media_type = media_types.get(file_ext, 'image/png')

            return FileResponse(
                passport_path,
                media_type=media_type,
                filename=f"passport_{booking_id}{file_ext}"
            )

    except Exception as e:
        print(f"❌ Ошибка получения паспорта в PDF: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )
