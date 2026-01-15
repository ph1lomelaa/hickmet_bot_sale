#!/bin/bash
# Скрипт для автоматической разметки 500 паспортов

echo "🚀 Запуск автоматической разметки паспортов..."
echo ""

# Переходим в директорию tools
cd "$(dirname "$0")"

# Проверяем наличие ZIP файла
if [ ! -f "$1" ]; then
    echo "❌ Использование: ./RUN_BATCH_ANNOTATION.sh /path/to/passports.zip"
    exit 1
fi

ZIP_FILE="$1"
OUTPUT_FILE="${2:-passport_dataset.json}"

echo "📦 Входной файл: $ZIP_FILE"
echo "💾 Выходной файл: $OUTPUT_FILE"
echo ""

# Запускаем разметку
python3 auto_annotate_batch.py \
    --input "$ZIP_FILE" \
    --output "$OUTPUT_FILE" \
    --debug

echo ""
echo "✅ Готово!"
echo ""
echo "📊 Следующие шаги:"
echo "   1. Проверьте статистику выше"
echo "   2. Откройте passport_annotator.html для проверки низкой уверенности"
echo "   3. Когда готовы - обучайте модель:"
echo "      python train_passport_model.py --dataset $OUTPUT_FILE --output ../models/passport_model"
