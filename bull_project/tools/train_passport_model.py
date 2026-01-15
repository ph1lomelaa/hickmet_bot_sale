"""
Скрипт обучения ML модели для парсинга паспортов

Требования:
    pip install transformers datasets torch scikit-learn

Использование:
    python train_passport_model.py --dataset passport_dataset.json --output model/
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict
import numpy as np

# ML библиотеки
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification
)
from datasets import Dataset
from sklearn.model_selection import train_test_split


class PassportNERTrainer:
    """Обучение Named Entity Recognition модели для паспортов"""

    # Метки для NER
    LABELS = {
        'O': 0,           # Outside (не важный текст)
        'B-SURNAME': 1,   # Beginning of surname
        'I-SURNAME': 2,   # Inside surname
        'B-FIRSTNAME': 3, # Beginning of firstname
        'I-FIRSTNAME': 4, # Inside firstname
        'B-IIN': 5,       # Beginning of IIN
        'I-IIN': 6,       # Inside IIN
        'B-DOC': 7,       # Beginning of document number
        'I-DOC': 8,       # Inside document number
        'B-DOB': 9,       # Beginning of date of birth
        'I-DOB': 10,      # Inside date of birth
    }

    LABEL_NAMES = {v: k for k, v in LABELS.items()}

    def __init__(self, model_name: str = "distilbert-base-multilingual-cased"):
        """
        Args:
            model_name: Базовая модель для fine-tuning
                       Рекомендуется: distilbert-base-multilingual-cased (быстрая)
                       Или: bert-base-multilingual-cased (точнее, но медленнее)
        """
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(
            model_name,
            num_labels=len(self.LABELS),
            id2label=self.LABEL_NAMES,
            label2id=self.LABELS
        )

    def load_dataset(self, json_path: str) -> List[Dict]:
        """Загрузка размеченного датасета"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"✅ Загружено {len(data)} паспортов")
        return data

    def prepare_ner_data(self, annotations: List[Dict]) -> Dataset:
        """Преобразование аннотаций в NER формат"""
        examples = []

        for ann in annotations:
            text = ann['ocr_text']
            labels_dict = ann['labels']

            # Токенизируем текст
            tokens = text.split()
            ner_tags = ['O'] * len(tokens)  # По умолчанию все Outside

            # Помечаем токены с данными
            for i, token in enumerate(tokens):
                # Фамилия
                if labels_dict.get('last_name') and labels_dict['last_name'] in token:
                    ner_tags[i] = 'B-SURNAME' if ner_tags[i] == 'O' else 'I-SURNAME'

                # Имя
                if labels_dict.get('first_name') and labels_dict['first_name'] in token:
                    ner_tags[i] = 'B-FIRSTNAME' if ner_tags[i] == 'O' else 'I-FIRSTNAME'

                # ИИН
                if labels_dict.get('iin') and labels_dict['iin'] in token:
                    ner_tags[i] = 'B-IIN' if ner_tags[i] == 'O' else 'I-IIN'

                # Номер документа
                if labels_dict.get('document_number') and labels_dict['document_number'] in token:
                    ner_tags[i] = 'B-DOC' if ner_tags[i] == 'O' else 'I-DOC'

                # Дата рождения
                if labels_dict.get('date_of_birth') and labels_dict['date_of_birth'] in token:
                    ner_tags[i] = 'B-DOB' if ner_tags[i] == 'O' else 'I-DOB'

            # Конвертируем метки в ID
            ner_tag_ids = [self.LABELS[tag] for tag in ner_tags]

            examples.append({
                'tokens': tokens,
                'ner_tags': ner_tag_ids
            })

        return Dataset.from_list(examples)

    def tokenize_and_align_labels(self, examples):
        """Токенизация с выравниванием меток"""
        tokenized_inputs = self.tokenizer(
            examples['tokens'],
            truncation=True,
            is_split_into_words=True,
            padding='max_length',
            max_length=512
        )

        labels = []
        for i, label in enumerate(examples['ner_tags']):
            word_ids = tokenized_inputs.word_ids(batch_index=i)
            label_ids = []
            previous_word_idx = None

            for word_idx in word_ids:
                if word_idx is None:
                    label_ids.append(-100)  # Игнорируем padding
                elif word_idx != previous_word_idx:
                    label_ids.append(label[word_idx])
                else:
                    label_ids.append(-100)  # Игнорируем подтокены
                previous_word_idx = word_idx

            labels.append(label_ids)

        tokenized_inputs['labels'] = labels
        return tokenized_inputs

    def train(self, dataset_path: str, output_dir: str = 'model/',
              epochs: int = 3, batch_size: int = 16):
        """
        Обучение модели

        Args:
            dataset_path: Путь к JSON файлу с аннотациями
            output_dir: Папка для сохранения модели
            epochs: Количество эпох обучения (3-5 оптимально)
            batch_size: Размер батча (16 для GPU 8GB, 8 для 4GB)
        """

        print("📚 Загрузка данных...")
        annotations = self.load_dataset(dataset_path)

        print("🔄 Подготовка NER данных...")
        dataset = self.prepare_ner_data(annotations)

        # Разделение на train/val
        dataset = dataset.train_test_split(test_size=0.15, seed=42)
        train_dataset = dataset['train']
        val_dataset = dataset['test']

        print(f"📊 Train: {len(train_dataset)}, Val: {len(val_dataset)}")

        # Токенизация
        print("🔤 Токенизация...")
        train_dataset = train_dataset.map(
            self.tokenize_and_align_labels,
            batched=True
        )
        val_dataset = val_dataset.map(
            self.tokenize_and_align_labels,
            batched=True
        )

        # Настройки обучения
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir=f'{output_dir}/logs',
            logging_steps=50,
            evaluation_strategy='epoch',
            save_strategy='epoch',
            load_best_model_at_end=True,
            metric_for_best_model='eval_loss',
        )

        # Data collator
        data_collator = DataCollatorForTokenClassification(
            tokenizer=self.tokenizer
        )

        # Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            data_collator=data_collator,
        )

        # Обучение
        print("🚀 Начинаем обучение...")
        trainer.train()

        # Сохранение
        print(f"💾 Сохранение модели в {output_dir}...")
        trainer.save_model(output_dir)
        self.tokenizer.save_pretrained(output_dir)

        print("✅ Обучение завершено!")

        # Оценка
        results = trainer.evaluate()
        print(f"\n📊 Результаты на валидации:")
        print(f"   Loss: {results['eval_loss']:.4f}")

        return trainer


def main():
    parser = argparse.ArgumentParser(description='Обучение ML модели для паспортов')
    parser.add_argument('--dataset', type=str, required=True,
                        help='Путь к JSON файлу с аннотациями')
    parser.add_argument('--output', type=str, default='passport_model/',
                        help='Папка для сохранения модели')
    parser.add_argument('--epochs', type=int, default=3,
                        help='Количество эпох обучения')
    parser.add_argument('--batch-size', type=int, default=16,
                        help='Размер батча')
    parser.add_argument('--model', type=str,
                        default='distilbert-base-multilingual-cased',
                        help='Базовая модель')

    args = parser.parse_args()

    # Создаем директорию для модели
    Path(args.output).mkdir(parents=True, exist_ok=True)

    # Обучение
    trainer = PassportNERTrainer(model_name=args.model)
    trainer.train(
        dataset_path=args.dataset,
        output_dir=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size
    )


if __name__ == '__main__':
    main()
