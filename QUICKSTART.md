# Quick Start Guide / Швидкий старт

## Для українських користувачів

### Встановлення і запуск за 3 кроки:

1. **Встановіть Python** (якщо ще не встановлено):
   - Завантажте з https://www.python.org/downloads/
   - Версія 3.6 або новіша

2. **Встановіть залежності**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Запустіть парсер**:
   ```bash
   python kw_parser.py
   ```

Готово! Файл з товарами буде збережено у поточній директорії.

### Додаткові опції:

- **Вказати ім'я файлу**:
  ```bash
  python kw_parser.py -o мої_товари.csv
  ```

- **Вказати інший магазин**:
  ```bash
  python kw_parser.py -u https://інший-магазин.myshopify.com
  ```

---

## For English users

### Install and run in 3 steps:

1. **Install Python** (if not already installed):
   - Download from https://www.python.org/downloads/
   - Version 3.6 or newer

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the parser**:
   ```bash
   python kw_parser.py
   ```

Done! The products file will be saved in the current directory.

### Additional options:

- **Specify output filename**:
  ```bash
  python kw_parser.py -o my_products.csv
  ```

- **Specify different store**:
  ```bash
  python kw_parser.py -u https://other-store.myshopify.com
  ```

---

## What data is extracted? / Які дані витягуються?

The parser extracts comprehensive product information including:

Парсер витягує повну інформацію про товари, включаючи:

- Product ID / ID товару
- Title / Назва
- Price / Ціна
- SKU / Артикул
- Availability / Наявність
- Images / Зображення
- Description / Опис
- Tags / Теги
- Inventory / Кількість на складі
- And more... / І більше...

## Troubleshooting / Вирішення проблем

### Error: "No products found" / Помилка: "Товари не знайдено"

This usually means:
Це зазвичай означає:

1. Network connectivity issue / Проблема з мережею
2. Store URL is incorrect / Неправильний URL магазину
3. Store blocks automated access / Магазин блокує автоматичний доступ

**Solution / Рішення:**
- Check your internet connection / Перевірте інтернет-з'єднання
- Verify the store URL / Перевірте URL магазину
- Try again later / Спробуйте пізніше

### Error: "requests module not found" / Помилка: "модуль requests не знайдено"

**Solution / Рішення:**
```bash
pip install requests
```

---

## Advanced Usage / Розширене використання

See `examples.py` for more advanced usage examples.

Дивіться `examples.py` для прикладів розширеного використання.

Run tests to verify functionality:
Запустіть тести для перевірки функціональності:

```bash
python test_kw_parser.py
```
