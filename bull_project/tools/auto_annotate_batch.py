"""
Автоматическая разметка паспортов для обучения ML модели

Использует текущий regex парсер для первичной разметки,
затем сохраняет результаты для ручной проверки.

Использование:
    python auto_annotate_batch.py --input passports.zip --output dataset.json
"""

import argparse
import json
import os
import sys
from pathlib import Path
import zipfile
from typing import List, Dict
from datetime import datetime

# Добавляем путь к парсеру
sys.path.insert(0, str(Path(__file__).parent.parent))

from bull_bot.core.parsers.passport_parser import PassportParserEasyOCR


class BatchAnnotator:
    """Массовая автоматическая разметка паспортов"""

    def __init__(self, debug: bool = False):
        self.parser = PassportParserEasyOCR(debug=debug)
        self.debug = debug
        self.stats = {
            'total': 0,
            'success': 0,
            'low_confidence': 0,
            'failed': 0
        }

    def extract_zip(self, zip_path: str, extract_to: str = 'temp_passports/') -> List[str]:
        """Распаковка ZIP архива с паспортами"""
        print(f"📦 Распаковка {zip_path}...")

        Path(extract_to).mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

        # Находим все файлы паспортов
        passport_files = []
        for ext in ['*.pdf', '*.png', '*.jpg', '*.jpeg']:
            passport_files.extend(Path(extract_to).rglob(ext))

        # Фильтруем временные файлы
        passport_files = [
            str(f) for f in passport_files
            if '_temp' not in f.name and '_preprocessed' not in f.name
        ]

        print(f"✅ Найдено {len(passport_files)} паспортов")
        return passport_files

    def calculate_confidence(self, data) -> float:
        """Расчет уверенности в результате парсинга"""
        score = 0.0

        # Критические поля
        if data.last_name and len(data.last_name) > 2:
            score += 0.25
        if data.first_name and len(data.first_name) > 2:
            score += 0.25
        if data.iin and len(data.iin) == 12 and data.iin.isdigit():
            score += 0.20
            # Бонус: валидная контрольная сумма ИИН
            if self.parser.validate_iin_checksum(data.iin):
                score += 0.10
        if data.dob and self._is_valid_date(data.dob):
            score += 0.10
        if data.document_number and len(data.document_number) > 5:
            score += 0.10

        return min(score, 1.0)

    def _is_valid_date(self, date_str: str) -> bool:
        """Проверка даты"""
        try:
            from datetime import datetime
            d = datetime.strptime(date_str, "%d.%m.%Y")
            now = datetime.now()
            return 1900 <= d.year <= now.year
        except:
            return False

    def annotate_single(self, file_path: str) -> Dict:
        """Разметка одного паспорта"""
        try:
            # Парсинг
            result = self.parser.parse(file_path)

            # Получаем OCR текст
            ocr_text = self.parser.extract_text_easyocr(file_path)

            # Расчет уверенности
            confidence = self.calculate_confidence(result)

            annotation = {
                'file': os.path.basename(file_path),
                'file_path': file_path,
                'timestamp': datetime.now().isoformat(),
                'confidence': round(confidence, 3),
                'needs_review': confidence < 0.85,
                'ocr_text': ocr_text,
                'labels': {
                    'last_name': result.last_name or '',
                    'first_name': result.first_name or '',
                    'iin': result.iin or '',
                    'document_number': result.document_number or '',
                    'date_of_birth': result.dob or '',
                    'gender': result.gender or '',
                    'expiration_date': result.expiration_date or '',
                    'nationality': result.nationality or 'KAZ'
                }
            }

            # Статистика
            self.stats['total'] += 1
            if confidence >= 0.85:
                self.stats['success'] += 1
            else:
                self.stats['low_confidence'] += 1

            return annotation

        except Exception as e:
            self.stats['total'] += 1
            self.stats['failed'] += 1

            if self.debug:
                print(f"❌ Ошибка обработки {file_path}: {e}")

            return {
                'file': os.path.basename(file_path),
                'file_path': file_path,
                'timestamp': datetime.now().isoformat(),
                'confidence': 0.0,
                'needs_review': True,
                'error': str(e),
                'ocr_text': '',
                'labels': {}
            }

    def annotate_batch(self, passport_files: List[str],
                       progress_callback=None) -> List[Dict]:
        """Массовая разметка паспортов"""
        annotations = []

        print(f"\n🚀 Начинаем автоматическую разметку {len(passport_files)} паспортов...")
        print("="*80)

        for i, file_path in enumerate(passport_files, 1):
            # Прогресс
            if i % 10 == 0 or i == 1:
                print(f"[{i}/{len(passport_files)}] Обработано: {i}, "
                      f"Успешно: {self.stats['success']}, "
                      f"Требуют проверки: {self.stats['low_confidence']}")

            # Разметка
            annotation = self.annotate_single(file_path)
            annotations.append(annotation)

            # Callback для прогресса
            if progress_callback:
                progress_callback(i, len(passport_files), annotation)

        print("="*80)
        return annotations

    def save_dataset(self, annotations: List[Dict], output_path: str):
        """Сохранение датасета"""
        # Сортируем: сначала уверенные, потом требующие проверки
        annotations.sort(key=lambda x: (-x['confidence'], x['needs_review']))

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(annotations, f, ensure_ascii=False, indent=2)

        print(f"💾 Датасет сохранен: {output_path}")

    def print_stats(self):
        """Вывод статистики"""
        print("\n" + "="*80)
        print("📊 СТАТИСТИКА АВТОМАТИЧЕСКОЙ РАЗМЕТКИ")
        print("="*80)

        total = self.stats['total']
        if total == 0:
            print("Нет обработанных паспортов")
            return

        success = self.stats['success']
        low_conf = self.stats['low_confidence']
        failed = self.stats['failed']

        print(f"Всего обработано:     {total}")
        print(f"✅ Успешно (conf≥85%): {success} ({success/total*100:.1f}%)")
        print(f"⚠️  Требуют проверки:   {low_conf} ({low_conf/total*100:.1f}%)")
        print(f"❌ Ошибки:             {failed} ({failed/total*100:.1f}%)")

        print(f"\n💡 Рекомендации:")
        if low_conf > total * 0.3:
            print(f"   ⚠️  Много паспортов требуют проверки ({low_conf})")
            print(f"   → Проверьте качество сканов")
            print(f"   → Улучшите regex правила")
        else:
            print(f"   ✅ Качество разметки хорошее!")
            print(f"   → Можно сразу обучать модель")
            print(f"   → Проверьте только {low_conf} паспортов с низкой уверенностью")

        print("="*80)


def main():
    parser = argparse.ArgumentParser(
        description='Автоматическая разметка паспортов для ML обучения'
    )
    parser.add_argument('--input', '-i', type=str, required=True,
                        help='ZIP архив или папка с паспортами')
    parser.add_argument('--output', '-o', type=str, default='passport_dataset.json',
                        help='Выходной JSON файл с аннотациями')
    parser.add_argument('--debug', action='store_true',
                        help='Режим отладки')
    parser.add_argument('--extract-dir', type=str, default='temp_passports/',
                        help='Папка для распаковки ZIP')

    args = parser.parse_args()

    # Создаем аннотатор
    annotator = BatchAnnotator(debug=args.debug)

    # Получаем список файлов
    input_path = Path(args.input)
    if input_path.suffix == '.zip':
        # Распаковываем ZIP
        passport_files = annotator.extract_zip(str(input_path), args.extract_dir)
    elif input_path.is_dir():
        # Ищем файлы в папке
        passport_files = []
        for ext in ['*.pdf', '*.png', '*.jpg', '*.jpeg']:
            passport_files.extend(input_path.rglob(ext))
        passport_files = [str(f) for f in passport_files]
    else:
        print(f"❌ Ошибка: {input_path} не является ZIP файлом или папкой")
        sys.exit(1)

    if not passport_files:
        print("❌ Не найдено паспортов для обработки")
        sys.exit(1)

    # Массовая разметка
    annotations = annotator.annotate_batch(passport_files)

    # Сохранение
    annotator.save_dataset(annotations, args.output)

    # Статистика
    annotator.print_stats()

    # Создаем файл только для проверки (низкая уверенность)
    if annotator.stats['low_confidence'] > 0:
        review_annotations = [a for a in annotations if a['needs_review']]
        review_path = args.output.replace('.json', '_review_only.json')
        with open(review_path, 'w', encoding='utf-8') as f:
            json.dump(review_annotations, f, ensure_ascii=False, indent=2)
        print(f"\n📋 Паспорты для проверки сохранены: {review_path}")

    print(f"\n🎯 Следующий шаг:")
    print(f"   1. Проверьте {annotator.stats['low_confidence']} паспортов в review_checker.html")
    print(f"   2. Или сразу обучайте модель: python train_passport_model.py --dataset {args.output}")


if __name__ == '__main__':
    main()
