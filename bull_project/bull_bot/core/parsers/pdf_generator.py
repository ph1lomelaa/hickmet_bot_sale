"""
Генератор PDF с текстовым слоем из изображений паспортов
Использует EasyOCR для распознавания текста и ReportLab для создания PDF
"""

import os
import tempfile
from typing import Optional
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
import easyocr
from bull_project.bull_bot.core.passport_storage import resolve_passport_file_path


class PassportPDFGenerator:
    """
    Генератор PDF с текстовым слоем для паспортов
    Создает searchable PDF - изображение паспорта + невидимый текстовый слой для копирования
    """

    def __init__(self, debug: bool = False):
        self.debug = debug
        # Инициализация EasyOCR (используем ту же модель, что и в passport_parser)
        self.reader = easyocr.Reader(['en', 'ru'])

    def extract_text_with_positions(self, image_path: str) -> list:
        """
        Извлекает текст с координатами из изображения
        Возвращает список (bbox, text, confidence)
        """
        temp_path = None
        try:
            # Конвертируем и улучшаем изображение для OCR
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Небольшое увеличение и усиление контраста/резкости
            scale = 1.4
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.LANCZOS)

            from PIL import ImageEnhance
            img = ImageEnhance.Contrast(img).enhance(1.35)
            img = ImageEnhance.Sharpness(img).enhance(1.2)

            # Сохраняем во временный JPG для easyocr
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tf:
                temp_path = tf.name
                img.save(temp_path, 'JPEG', quality=96)

            # Распознаем текст с координатами
            result = self.reader.readtext(
                temp_path,
                paragraph=False,     # Не объединяем в параграфы
                contrast_ths=0.3,
                adjust_contrast=0.7
            )

            if self.debug:
                print(f"📄 Распознано {len(result)} текстовых блоков")
                # Показываем распознанный текст для отладки
                high_conf = [text for (_, text, conf) in result if conf > 0.5]
                print(f"   Высокая уверенность (>50%): {len(high_conf)} блоков")

            return result

        except Exception as e:
            if self.debug:
                print(f"❌ Ошибка OCR: {e}")
            return []
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def create_searchable_pdf(
        self,
        image_path: str,
        output_pdf_path: str,
        add_ocr_layer: bool = True
    ) -> bool:
        """
        Создает searchable PDF из изображения паспорта

        Args:
            image_path: путь к изображению паспорта
            output_pdf_path: путь для сохранения PDF
            add_ocr_layer: добавлять ли OCR текстовый слой (по умолчанию True)

        Returns:
            True если успешно, False если ошибка
        """
        try:
            # Открываем изображение
            img = Image.open(image_path)
            img_width, img_height = img.size

            if self.debug:
                print(f"🖼️  Размер изображения: {img_width}x{img_height}")

            # Определяем размер страницы PDF (адаптируем под изображение)
            # Используем соотношение сторон изображения
            aspect_ratio = img_width / img_height

            # Базовый размер A4 (595x842 points)
            if aspect_ratio > 1:
                # Горизонтальная ориентация
                page_width = 842
                page_height = 842 / aspect_ratio
            else:
                # Вертикальная ориентация
                page_height = 842
                page_width = 842 * aspect_ratio

            # Создаем PDF
            c = canvas.Canvas(output_pdf_path, pagesize=(page_width, page_height))

            # Добавляем изображение на всю страницу
            c.drawImage(
                image_path,
                0,
                0,
                width=page_width,
                height=page_height,
                preserveAspectRatio=True
            )

            # Добавляем OCR текстовый слой
            if add_ocr_layer:
                ocr_results = self.extract_text_with_positions(image_path)

                # Коэффициенты масштабирования
                scale_x = page_width / img_width
                scale_y = page_height / img_height

                if self.debug:
                    print(f"📊 Масштаб: X={scale_x:.2f}, Y={scale_y:.2f}")

                # Добавляем каждый текстовый блок как невидимый текст
                for (bbox, text, confidence) in ocr_results:
                    # Пропускаем текст с низкой уверенностью (повышен порог с 0.4 до 0.5)
                    if confidence < 0.5:
                        continue

                    # bbox = [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                    # Берем левый нижний угол для позиционирования
                    x = bbox[0][0] * scale_x
                    # В PDF координаты Y идут снизу вверх, поэтому инвертируем
                    y = page_height - (bbox[0][1] * scale_y)

                    # Вычисляем ширину и высоту текстового блока
                    text_width = (bbox[1][0] - bbox[0][0]) * scale_x
                    text_height = (bbox[2][1] - bbox[0][1]) * scale_y

                    # Вычисляем размер шрифта на основе высоты блока
                    font_size = max(8, min(text_height * 0.8, 14))

                    # Добавляем невидимый текст (renderMode=3 делает текст невидимым)
                    text_obj = c.beginText(x, y)
                    text_obj.setTextRenderMode(3)  # Невидимый текст
                    text_obj.setFont("Helvetica", font_size)
                    text_obj.textLine(text)
                    c.drawText(text_obj)

                    if self.debug:
                        print(f"  ✓ Добавлен текст: '{text}' на позиции ({x:.1f}, {y:.1f})")

            # Сохраняем PDF
            c.save()

            if self.debug:
                print(f"✅ PDF создан: {output_pdf_path}")

            return True

        except Exception as e:
            if self.debug:
                print(f"❌ Ошибка создания PDF: {e}")
                import traceback
                traceback.print_exc()
            return False

    def convert_passport_to_pdf(
        self,
        passport_image_path: str,
        output_pdf_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Конвертирует изображение паспорта в searchable PDF

        Args:
            passport_image_path: путь к изображению паспорта
            output_pdf_path: путь для сохранения PDF (если None, создается рядом с оригиналом)

        Returns:
            Путь к созданному PDF или None если ошибка
        """
        try:
            resolved_passport_path = resolve_passport_file_path(passport_image_path) or passport_image_path

            # Если путь не указан, создаем рядом с оригиналом
            if output_pdf_path is None:
                base_name = os.path.splitext(resolved_passport_path)[0]
                output_pdf_path = f"{base_name}_searchable.pdf"

            # Проверяем существование файла
            if not os.path.exists(resolved_passport_path):
                if self.debug:
                    print(f"❌ Файл не найден: {resolved_passport_path}")
                return None

            # Создаем PDF
            success = self.create_searchable_pdf(
                resolved_passport_path,
                output_pdf_path,
                add_ocr_layer=True
            )

            if success:
                return output_pdf_path
            else:
                return None

        except Exception as e:
            if self.debug:
                print(f"❌ Ошибка конвертации: {e}")
            return None


def test_pdf_generator(image_path: str):
    """Тестирование генератора PDF"""
    generator = PassportPDFGenerator(debug=True)

    output_pdf = image_path.rsplit('.', 1)[0] + '_test.pdf'
    result = generator.convert_passport_to_pdf(image_path, output_pdf)

    if result:
        print(f"\n✅ PDF успешно создан: {result}")
        print(f"📝 Теперь можно открыть PDF и попробовать скопировать текст")
    else:
        print("\n❌ Ошибка создания PDF")

    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_pdf_generator(sys.argv[1])
    else:
        print("Использование: python pdf_generator.py <путь_к_изображению>")
