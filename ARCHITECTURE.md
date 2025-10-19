# KW Parser Architecture / Архітектура KW Parser

```
┌──────────────────────────────────────────────────────────────────┐
│                      KW Parser System                             │
│                  Система KW Parser                                │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│   User / CLI    │  python kw_parser.py -o output.csv
│ Користувач/CLI  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    KWParser Class                                │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ __init__(store_url)                                        │ │
│  │ • Initialize session                                        │ │
│  │ • Set headers (User-Agent)                                 │ │
│  │ • Configure API endpoints                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           │                                       │
│                           ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ fetch_products_page(page, limit)                           │ │
│  │ • Build API request                                        │ │
│  │ • Handle pagination                                        │ │
│  │ • Error handling                                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           │                                       │
│                           ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ parse_all_products()                                       │ │
│  │ • Loop through all pages                                   │ │
│  │ • Collect all products                                     │ │
│  │ • Display progress                                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           │                                       │
│                           ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ extract_product_data(product)                              │ │
│  │ • Extract 19 fields                                        │ │
│  │ • Format data                                              │ │
│  │ • Handle missing values                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           │                                       │
│                           ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ save_to_csv(products, filename)                            │ │
│  │ • Create CSV file                                          │ │
│  │ • Write headers                                            │ │
│  │ • Write product rows                                       │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  CSV Output     │  kw_products_20231019_143000.csv
│  CSV Вивід      │  (all products with 19 fields each)
└─────────────────┘


Data Flow / Потік даних:
═══════════════════════════

   Shopify Store                      KW Parser                     CSV File
   Магазин Shopify                    KW Parser                     CSV файл
   
   ┌──────────────┐                  ┌──────────────┐             ┌──────────────┐
   │              │   GET request    │              │   Write     │              │
   │  products    │ ───────────────> │   Parse &    │ ──────────> │  Product     │
   │  .json API   │   with params    │   Extract    │   UTF-8     │  Data        │
   │              │ <─────────────── │   Data       │             │              │
   └──────────────┘   JSON response  └──────────────┘             └──────────────┘
   
   • Page 1 (250)                    • Extract fields              • Headers
   • Page 2 (250)                    • Format data                 • Row 1
   • Page 3 (...)                    • Handle errors               • Row 2
   • Page N                          • Progress display            • Row N
   

API Request Example / Приклад API запиту:
═════════════════════════════════════════

GET https://kw-automotive.com/products.json?page=1&limit=250

Response format:
{
  "products": [
    {
      "id": 12345678,
      "title": "KW V1 Coilover Kit - BMW 3 Series E90",
      "handle": "kw-v1-coilover-kit-bmw-3-series-e90",
      "vendor": "KW Suspensions",
      "product_type": "Coilovers",
      "tags": ["BMW", "E90", "Coilover"],
      "variants": [...],
      "images": [...],
      ...
    },
    ...
  ]
}


CSV Output Format / Формат CSV виводу:
═══════════════════════════════════════

id,title,handle,vendor,product_type,price,sku,...
12345678,"KW V1 Coilover...","kw-v1-coilover...","KW Suspensions",...
87654321,"KW V2 Coilover...","kw-v2-coilover...","KW Suspensions",...
...


Error Handling / Обробка помилок:
═══════════════════════════════════

┌─────────────────┐
│ Network Error   │ → Retry with timeout
│ Помилка мережі  │   Повторити з таймаутом
└─────────────────┘

┌─────────────────┐
│ Empty Response  │ → Stop pagination
│ Порожня відп.   │   Зупинити пагінацію
└─────────────────┘

┌─────────────────┐
│ Missing Fields  │ → Use default values
│ Відсутні поля   │   Використати значення за замовчуванням
└─────────────────┘

┌─────────────────┐
│ Rate Limit      │ → Add delay (0.5s)
│ Обмеж. швидк.   │   Додати затримку (0.5с)
└─────────────────┘


Performance / Продуктивність:
══════════════════════════════

• Pagination: 250 products per request (Shopify max)
  Пагінація: 250 товарів на запит (максимум Shopify)

• Delay: 0.5 seconds between requests
  Затримка: 0.5 секунди між запитами

• Memory: Efficient streaming processing
  Пам'ять: Ефективна потокова обробка

• Estimated time: ~2-5 seconds per 250 products
  Орієнтовний час: ~2-5 секунд на 250 товарів
```
