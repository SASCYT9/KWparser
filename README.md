# KWparser

Python скрипт для парсингу всіх товарів KW suspensions з магазину KW automotive (Shopify) та експорту в CSV файл.

Python script to parse all KW suspension products from the KW automotive Shopify store and export to CSV file.

## Features / Функції

- Автоматично парсить всі товари з KW automotive Shopify магазину
- Експортує дані в CSV формат
- Витягує детальну інформацію про товари: назва, ціна, SKU, наявність, зображення, тощо
- Підтримує пагінацію для великої кількості товарів
- Обробка помилок та відображення прогресу

---

- Automatically parses all products from KW automotive Shopify store
- Exports data to CSV format
- Extracts detailed product information: title, price, SKU, availability, images, etc.
- Supports pagination for large product catalogs
- Error handling and progress display

## Installation / Встановлення

1. Клонуйте репозиторій / Clone the repository:
```bash
git clone https://github.com/SASCYT9/KWparser.git
cd KWparser
```

2. Встановіть залежності / Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage / Використання

### Базове використання / Basic usage:
```bash
python kw_parser.py
```

Це створить CSV файл з назвою `kw_products_YYYYMMDD_HHMMSS.csv` з всіма товарами.

This will create a CSV file named `kw_products_YYYYMMDD_HHMMSS.csv` with all products.

### З кастомною назвою файлу / With custom output filename:
```bash
python kw_parser.py -o my_products.csv
```

### З кастомним URL магазину / With custom store URL:
```bash
python kw_parser.py -u https://kw-automotive.com
```

### Переглянути всі опції / View all options:
```bash
python kw_parser.py --help
```

## Output Format / Формат виводу

CSV файл містить наступні колонки / CSV file contains the following columns:

- `id` - Унікальний ідентифікатор товару / Product unique identifier
- `title` - Назва товару / Product title
- `handle` - URL-friendly назва / URL-friendly product name
- `vendor` - Виробник / Vendor
- `product_type` - Тип товару / Product type
- `created_at` - Дата створення / Creation date
- `updated_at` - Дата оновлення / Update date
- `published_at` - Дата публікації / Publication date
- `tags` - Теги / Tags
- `price` - Ціна / Price
- `compare_at_price` - Порівняльна ціна / Compare at price
- `sku` - Артикул / SKU
- `inventory_quantity` - Кількість на складі / Inventory quantity
- `available` - Доступність / Availability
- `url` - URL товару / Product URL
- `variant_count` - Кількість варіантів / Number of variants
- `image_url` - URL головного зображення / Main image URL
- `image_count` - Кількість зображень / Number of images
- `description` - Опис товару / Product description

## Requirements / Вимоги

- Python 3.6+
- requests

## License / Ліцензія

MIT