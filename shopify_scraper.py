# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import csv
import re
import math
import hashlib
from itertools import product
import time


def transliterate(text):
    mapping = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g', 'д': 'd', 'е': 'e', 'є': 'ie',
        'ж': 'zh', 'з': 'z', 'и': 'y', 'і': 'i', 'ї': 'i', 'й': 'i', 'к': 'k', 'л': 'l',
        'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ь': '', 'ю': 'iu',
        'я': 'ia', ' ': '-', '(': '', ')': ''
    }
    text = text.lower()
    result = ''.join(mapping.get(char, char) for char in text)
    result = re.sub(r'[^a-z0-9\-]+', '', result)
    result = re.sub(r'--+', '-', result).strip('-')
    return result


def translate_option_to_ukrainian(label, value):
    option_translations = {
        'vehicle has electronic damper': 'Автомобіль має електронний амортизатор',
        'electronic damper': 'Електронний амортизатор',
        'strut diameter front axle (mm)': 'Діаметр стійки передньої осі (мм)',
        'strut diameter front axle': 'Діаметр стійки передньої осі',
        'content of delivery': 'Комплектація поставки',
        'rear axle type': 'Тип задньої осі',
        'note (car assignment)': 'Примітка (призначення автомобіля)',
        'car assignment': 'Призначення автомобіля',
        'axle weight ra': 'Вага на задню вісь',
        'rear axle weight': 'Вага на задню вісь',
        'axle load': 'Навантаження на вісь',
        'front axle diameter': 'Діаметр передньої осі',
        'rear axle diameter': 'Діаметр задньої осі',
        'suspension type': 'Тип підвіски',
        'spring type': 'Тип пружини',
        'shock absorber type': 'Тип амортизатора',
        'lowering': 'Заниження',
        'adjustment range': 'Діапазон регулювання',
        'damper adjustment': 'Регулювання демпфера',
        'variant': 'Варіант',
        'model year': 'Рік моделі',
        'equipment': 'Обладнання',
        'engine type': 'Тип двигуна',
        'drive type': 'Тип приводу',
        'brake system': 'Гальмівна система',
        'twist-beam rear axle (rigid axle)': 'Балка заднього моста (жорстка вісь)',
        'multi-link rear axle (independent wheel suspension)': 'Багаторичажна задня вісь (незалежна підвіска)'
    }

    value_translations = {
        'yes': 'так',
        'no': 'ні',
        'not selected': 'не обрано',
        'not yet selected': 'не обрано',
        'complete kit': 'повний комплект',
        'partial': 'часткова',
        'standard': 'стандарт',
        'sport': 'спорт',
        'comfort': 'комфорт',
        'front': 'передня',
        'rear': 'задня',
        'all': 'всі',
        'left': 'ліва',
        'right': 'права'
    }

    label_lower = str(label).lower().strip()

    if isinstance(value, list):
        return label, value

    value_lower = str(value).lower().strip()

    translated_label = option_translations.get(label_lower, label)
    translated_value = value_translations.get(value_lower, value)

    return translated_label, translated_value


class ShopifyProductFormatter:
    def create_sku(self, base_sku, make, model, engine, options_dict):
        unique_part = f"{make}-{model}-{engine}".replace(' ', '-').replace('(', '').replace(')', '')
        for value in sorted(options_dict.values()):
            unique_part += f"-{value}"
        unique_part = re.sub(r'[^a-zA-Z0-9\-]', '', unique_part)
        hash_part = hashlib.md5(unique_part.encode()).hexdigest()[:6]
        return f"{base_sku}-{hash_part}"

    def format_product(self, base_title, initial_make, initial_model, selected_options, info_options, base_sku, has_electronic_damper, price_eur, price_uah, description, image_urls, additional_data_html, compatibility):
        suspension_type = self.extract_suspension_type(base_title)
        damper_variants_available, damper_info = self.check_damper_variants(info_options)

        has_electronic_damper = 'not applicable'
        if damper_variants_available:
            has_electronic_damper = 'both_available'

        damper_sku_info = self.format_damper_sku_info(damper_variants_available, damper_info, base_sku)
        options_description = self.format_options_description(info_options, selected_options)

        full_description = f"{description}{damper_sku_info}{options_description}{additional_data_html}"

        cars = compatibility
        if not cars:
            cars = [{'make': initial_make, 'model': initial_model, 'engine': 'Standard'}]

        products = []
        seen = set()

        for car in cars:
            make = car['make'] or initial_make
            model = car['model'] or initial_model
            engine = car['engine'] or 'Standard'

            clean_model = re.sub(r'\s+\d{2}/\d{4}[-].*$', '', model).strip()
            key = f"{make}|{clean_model}|{engine}|{str(sorted(selected_options.items()))}"
            if key in seen:
                continue
            seen.add(key)

            title_suffix = self.format_title_suffix(selected_options)
            product_title = f"{base_title} для {make} {clean_model} {engine}{title_suffix}".strip()
            unique_sku = self.create_sku(base_sku, make, clean_model, engine, selected_options)

            product = self.build_product_dict(product_title, full_description, unique_sku, price_uah, price_eur, make, clean_model, engine, suspension_type, has_electronic_damper, selected_options)
            products.append(product)

        products_with_images = self.apply_images_to_products(products, image_urls)

        opts_summary = {k: v for k, v in selected_options.items() if v != 'not selected'}
        print(f"VARIANT: {len(products_with_images)}, {price_eur}EUR, {opts_summary if opts_summary else 'none'}")
        return products_with_images

    def extract_suspension_type(self, title):
        title_upper = title.upper()
        patterns = [r'\bV[1-4]\b', r'\bDDC\b', r'\bCLUBSPORT\b', r'\bLEVELING\b', r'\bST\b', r'\bHLS\b']
        for pattern in patterns:
            match = re.search(pattern, title_upper)
            if match:
                suspension_type = match.group(0)
                print(f"SUSPENSION_TYPE: {suspension_type}")
                return suspension_type
        print("SUSPENSION_TYPE: Unknown")
        return "Unknown"

    def check_damper_variants(self, info_options):
        if not info_options:
            return False, {}
        for opt_label, opt_values in info_options.items():
            opt_label_lower = opt_label.lower()
            if 'electronic damper' in opt_label_lower or 'vehicle has electronic damper' in opt_label_lower:
                if isinstance(opt_values, list) and len(opt_values) >= 2:
                    damper_info = {'label': opt_label, 'options': opt_values}
                    print(f"DAMPER_VARIANTS_AVAILABLE: {opt_values}")
                    return True, damper_info
        return False, {}

    def format_damper_sku_info(self, damper_variants_available, damper_info, base_sku):
        if not damper_variants_available:
            return ""
        damper_sku_info = "<h3>Доступні варіанти з електронними демпферами</h3>"
        damper_sku_info += "<p>Цей продукт доступний у двох конфігураціях:</p><ul>"
        for opt_value in damper_info['options']:
            opt_value_str = str(opt_value).upper()
            variant_sku = f"{base_sku}-{opt_value_str}"
            if opt_value_str == 'YES':
                damper_sku_info += f"<li><strong>З електронними демпферами</strong> - SKU: <code>{variant_sku}</code></li>"
            elif opt_value_str == 'NO':
                damper_sku_info += f"<li><strong>Без електронних демпферів</strong> - SKU: <code>{variant_sku}</code></li>"
        damper_sku_info += "</ul><p><em>При замовленні, будь ласка, вкажіть потрібний SKU в залежності від того, чи має ваш автомобіль електронні демпфери.</em></p>"
        return damper_sku_info

    def format_options_description(self, info_options, selected_options):
        if not info_options and not selected_options:
            return ""
        options_html = "<h3>Опції конфігурації</h3>"
        if selected_options:
            selected_opts = {k: v for k, v in selected_options.items() if v and v != 'not selected' and 'electronic damper' not in k.lower() and 'vehicle has electronic damper' not in k.lower()}
            if selected_opts:
                options_html += "<h4>Обрані опції для цього варіанту:</h4><ul>"
                for opt_label, opt_value in selected_opts.items():
                    translated_label, translated_value = translate_option_to_ukrainian(opt_label, opt_value)
                    options_html += f"<li><strong>{translated_label}:</strong> {translated_value}</li>"
                options_html += "</ul>"
        if info_options:
            options_html += "<h4>Інші доступні опції:</h4><ul>"
            for opt_label, opt_values in info_options.items():
                if 'electronic damper' in opt_label.lower() or 'vehicle has electronic damper' in opt_label.lower():
                    continue
                translated_label, _ = translate_option_to_ukrainian(opt_label, "")
                if isinstance(opt_values, list) and len(opt_values) > 1:
                    current_selected = selected_options.get(opt_label)
                    translated_values = []
                    for val in opt_values:
                        _, tr_val = translate_option_to_ukrainian(opt_label, val)
                        if current_selected and val.lower() == str(current_selected).lower():
                            translated_values.append(f"<strong>{tr_val}</strong> (обрано)")
                        else:
                            translated_values.append(tr_val)
                    options_html += f"<li><strong>{translated_label}:</strong> {', '.join(translated_values)}</li>"
            options_html += "</ul><p><em>Примітка: Для уточнення або зміни опцій конфігурації для вашого конкретного автомобіля, будь ласка, зв'яжіться з нами.</em></p>"
        return options_html

    def format_title_suffix(self, selected_options):
        if not selected_options:
            return ""
        selected_opts = {k: v for k, v in selected_options.items() if v != 'not selected' and 'electronic damper' not in k.lower() and 'vehicle has electronic damper' not in k.lower()}
        if not selected_opts:
            return ""
        translated_opts = [f"{translate_option_to_ukrainian(k, v)[0]}: {translate_option_to_ukrainian(k, v)[1]}" for k, v in selected_opts.items()]
        return f" ({', '.join(translated_opts)})"

    def build_product_dict(self, title, description, sku, price_uah, price_eur, make, model, engine, suspension_type, has_electronic_damper, selected_options):
        product = {
            'Handle': '', 'Title': title, 'Body (HTML)': description, 'Vendor': 'KW',
            'Product Category': 'Automotive > Vehicle Parts & Accessories > Motor Vehicle Parts > Motor Vehicle Suspension Parts',
            'Type': 'Suspension', 'Tags': 'KW, Suspension', 'Published': 'TRUE',
            'Option1 Name': 'Title', 'Option1 Value': 'Default Title', 'Variant SKU': sku,
            'Variant Inventory Qty': '10', 'Variant Inventory Policy': 'deny',
            'Variant Fulfillment Service': 'manual', 'Variant Price': str(price_uah),
            'Variant Requires Shipping': 'TRUE', 'Variant Taxable': 'TRUE', 'Image Src': '',
            'Image Position': '', 'Image Alt Text': '', 'Gift Card': 'FALSE',
            'SEO Title': '', 'SEO Description': '', 'Google Shopping / MPN': sku,
            'Variant Weight Unit': 'kg', 'Status': 'active',
            'metafield:custom.price_eur[single_line_text_field]': str(price_eur),
            'metafield:custom.vehicle_make[single_line_text_field]': make,
            'metafield:custom.vehicle_model[single_line_text_field]': model,
            'metafield:custom.vehicle_engine[single_line_text_field]': engine,
            'metafield:custom.suspension_type[single_line_text_field]': suspension_type,
            'metafield:custom.electronic_damper[single_line_text_field]': has_electronic_damper
        }
        for opt_label, opt_value in selected_options.items():
            safe_label = re.sub(r'[^a-z0-9_]', '', opt_label.lower().replace(' ', '_'))
            product[f'metafield:custom.{safe_label}[single_line_text_field]'] = str(opt_value)

        transliterated = transliterate(product['Title'])
        product['Handle'] = f"{transliterated}-{sku.lower()}"
        product['SEO Title'] = product['Title']
        product['Image Alt Text'] = product['Title']
        clean_desc = re.sub(r'<[^>]+>', ' ', description).strip()
        clean_desc = re.sub(r'&[^;]+;', ' ', clean_desc)
        product['SEO Description'] = ' '.join(clean_desc.split())[:320]
        return product

    def apply_images_to_products(self, products, image_urls):
        products_with_images = []
        for product in products:
            if image_urls:
                for i, image_url in enumerate(image_urls):
                    product_copy = product.copy()
                    product_copy['Image Src'] = image_url
                    product_copy['Image Position'] = i + 1
                    products_with_images.append(product_copy)
            else:
                products_with_images.append(product)
        return products_with_images


class ProductDataExtractor:
    def __init__(self, driver, wait, short_wait, safe_click):
        self.driver = driver
        self.wait = wait
        self.short_wait = short_wait
        self.safe_click = safe_click

    def get_title(self):
        try:
            title_elem = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.product__title")))
            title = title_elem.text.strip()
            print(f"TITLE: {title}")
            return title
        except Exception as e:
            print(f"TITLE_ERROR: {e}")
            return "Unknown Product"

    def get_sku(self):
        try:
            sku_elem = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".product__article-number > span:last-of-type")))
            for attempt in range(5):
                sku = sku_elem.text.strip().upper()
                if "NOT YET SELECTED" not in sku and sku:
                    print(f"SKU: {sku}")
                    return sku
                time.sleep(0.7)
            print(f"SKU_STILL_PENDING")
            return f"PENDING_{hash(str(self.get_title())) % 100000}"
        except Exception as e:
            print(f"SKU_ERROR: {e}")
            return f"NO_SKU_{hash(str(e)) % 10000}"

    def get_price(self):
        try:
            js_price = self.driver.execute_script("""
                var prices = [];
                var elements = document.querySelectorAll('[data-bind*="getFormatedPrice"], .price, [class*="price"]');
                for (var i = 0; i < elements.length; i++) {
                    var text = elements[i].textContent || elements[i].innerText || '';
                    if (text.includes('€')) {
                        var matches = text.match(/€\\s*(\\d+(?:[.,]\\d+)*)/g);
                        if (matches) {
                            matches.forEach(function(match) {
                                var num = parseFloat(match.replace(/[€,]/g, '').trim());
                                if (num >= 100 && num <= 20000) {
                                    prices.push(num);
                                }
                            });
                        }
                    }
                }
                return prices.length > 0 ? Math.max(...prices) : null;
            """)
            if js_price:
                eur = math.ceil(js_price)
                uah = math.ceil(eur * 49)
                print(f"PRICE: {eur}EUR/{uah}UAH")
                return eur, uah
        except Exception as e:
            print(f"PRICE_ERROR: {e}")
        print("NO_PRICE")
        return 1000, 49000

    def get_description(self):
        try:
            desc_tab = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='#beschreibung']")))
            self.safe_click(desc_tab)
            self.short_wait.until(EC.visibility_of_element_located((By.ID, "beschreibung")))
            desc_elem = self.driver.find_element(By.ID, "beschreibung")
            html = desc_elem.get_attribute('innerHTML').strip()
            clean_html = re.sub(r'\s*data-bind=".*?"', '', html)
            clean_html = re.sub(r'<!--\s*ko\s.*?-->', '', clean_html, flags=re.DOTALL)
            clean_html = re.sub(r'<!--\s*/ko\s*-->', '', clean_html)
            print("DESC_OK")
            return f"<h3>Description</h3>{clean_html}"
        except Exception as e:
            print(f"DESC_ERROR: {e}")
            return "<h3>Description</h3><p>Product description not available</p>"

    def get_image_urls(self):
        try:
            image_urls = []
            gallery_container = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".gallery-slider-container")))
            image_elements = gallery_container.find_elements(By.CSS_SELECTOR, "img.gallery-slider-image")
            for img in image_elements:
                src = img.get_attribute('src')
                if src and src not in image_urls:
                    image_urls.append(src)
            print(f"IMAGES_FOUND: {len(image_urls)}")
            return image_urls
        except Exception as e:
            print(f"IMAGES_ERROR: {e}")
            return []

    def get_technical_data_and_documents(self):
        additional_data_html = ""
        try:
            # Technical Data
            try:
                tech_data_tab = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='#technischedaten']")))
                self.safe_click(tech_data_tab)
                time.sleep(0.5)
                tech_data_content = self.driver.find_element(By.ID, "technischedaten")
                additional_data_html += f"<h3>Technical Data</h3>{tech_data_content.get_attribute('innerHTML')}"
            except TimeoutException:
                print("NO_TECH_DATA_TAB")
            # Documents
            try:
                documents_tab = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='#dokumente']")))
                self.safe_click(documents_tab)
                time.sleep(0.5)
                documents_content = self.driver.find_element(By.ID, "dokumente")
                additional_data_html += f"<h3>Documents</h3>{documents_content.get_attribute('innerHTML')}"
            except TimeoutException:
                print("NO_DOCUMENTS_TAB")
            return additional_data_html
        except Exception as e:
            print(f"ADDITIONAL_DATA_ERROR: {e}")
            return ""

    def get_compatibility(self):
        try:
            comp_tab = self.short_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='#kompatibel']")))
            self.safe_click(comp_tab)
            time.sleep(0.5)
            self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#kompatibel table tbody tr td")))
            table = self.driver.find_element(By.CSS_SELECTOR, "#kompatibel table")
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
            cars = []
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 3:
                    car = {'make': cells[0].text.strip(), 'model': cells[1].text.strip(), 'engine': cells[2].text.strip()}
                    if car['make'] and car['model']:
                        cars.append(car)
            print(f"COMPAT: {len(cars)}")
            return cars
        except TimeoutException:
            print("NO_COMPAT_TAB")
            return []
        except Exception as e:
            print(f"COMPAT_ERROR: {e}")
            return []


class KWParser:
    def __init__(self):
        print("START")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'--user-data-dir=/tmp/user-data-{int(time.time())}')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        options.add_argument('--disable-images')
        options.add_argument('--blink-settings=imagesEnabled=false')
        options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.cookies": 1,
            "profile.managed_default_content_settings.javascript": 1,
            "profile.managed_default_content_settings.plugins": 1,
            "profile.managed_default_content_settings.popups": 2,
            "profile.managed_default_content_settings.geolocation": 2,
            "profile.managed_default_content_settings.media_stream": 2,
        })

        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.set_page_load_timeout(30)
        self.base_url = "https://store.kwautomotive.de/de-en/kw/shop"
        self.wait = WebDriverWait(self.driver, 10)
        self.short_wait = WebDriverWait(self.driver, 3)
        self.extractor = ProductDataExtractor(self.driver, self.wait, self.short_wait, self.safe_click)
        self.formatter = ShopifyProductFormatter()
        self.all_products = []

    def safe_click(self, element):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.2)
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except Exception as e:
            print(f"CLICK_ERROR: {e}")
            return False

    def handle_cookies(self):
        try:
            cookie_button = self.short_wait.until(EC.element_to_be_clickable((By.ID, "uc-btn-accept-banner")))
            cookie_button.click()
            print("COOKIES_OK")
        except TimeoutException:
            print("NO_COOKIES")

    def reset_car_selection(self):
        try:
            selected_car = self.short_wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".car-selector--car-selected"))
            )
            reset_button = selected_car.find_element(By.CSS_SELECTOR, ".selectedCar__reset")
            self.safe_click(reset_button)
            self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".makesInput")))
            print("CAR_RESET")
            return True
        except TimeoutException:
            return False

    def extract_year_from_engine(self, engine_text):
        """Витягує рік з тексту двигуна. Формат: '... 12/2018 -' або '... 08/2019 - ...'"""
        import re
        match = re.search(r'(\d{2})/(\d{4})', engine_text)
        if match:
            return int(match.group(2))
        return None

    def open_vehicle_selector(self):
        """Натискає кнопку Select Vehicle якщо вона є"""
        try:
            # Спробуємо різні варіанти пошуку кнопки
            selectors = [
                # Найточніший селектор на основі HTML
                (By.CSS_SELECTOR, "button.btn--outline-selectable[data-bind*='onButtonUniversalProductsNoteClick']"),
                (By.XPATH, "//button[@class='btn--outline-selectable' and contains(text(), 'Please select vehicle')]"),
                (By.XPATH, "//button[contains(text(), 'Please select vehicle')]"),
                (By.XPATH, "//button[contains(., 'Please select vehicle')]"),
                (By.XPATH, "//button[contains(text(), 'PLEASE SELECT VEHICLE')]"),
                (By.CSS_SELECTOR, "button.btn--outline-selectable"),
            ]

            for selector_type, selector_value in selectors:
                try:
                    select_vehicle_button = self.short_wait.until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    print(f"SELECT_VEHICLE_FOUND: {selector_value}")

                    # Scroll до елементу та натискаємо
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_vehicle_button)
                    time.sleep(0.5)

                    # Використовуємо JavaScript для кліку (найнадійніший метод)
                    self.driver.execute_script("arguments[0].click();", select_vehicle_button)

                    print("SELECT_VEHICLE_CLICKED")
                    time.sleep(1.5)
                    return True
                except TimeoutException:
                    continue
                except Exception as e:
                    print(f"SELECTOR_TRY_ERROR: {e}")
                    continue

            print("SELECT_VEHICLE_NOT_FOUND")
            return False

        except Exception as e:
            print(f"SELECT_VEHICLE_ERROR: {e}")
            return False

    def select_make_model_engine(self, make, model, engine_index=0, filter_year_from=2019):
        time.sleep(0.3)

        make_input = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".makesInput")))
        self.safe_click(make_input)
        time.sleep(0.2)
        make_input.clear()
        make_input.send_keys(make)
        time.sleep(0.3)

        make_options = self.wait.until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".makesList .carselector-list-element span")))
        selected_make = next((opt for opt in make_options if opt.text.strip().upper() == make.upper()),
                             make_options[0] if make_options else None)
        if not selected_make:
            raise Exception("NO_MAKE_FOUND")

        print(f"MAKE: {selected_make.text.strip()}")
        self.safe_click(selected_make)
        time.sleep(0.5)
        self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".carselector-list.makesList")))

        model_input = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".modelsInput:not([readonly])")))
        self.safe_click(model_input)
        time.sleep(0.2)
        model_input.clear()
        model_input.send_keys(model)
        time.sleep(0.3)

        model_options = self.wait.until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".modelsList .carselector-list-element")))

        # Debug: виводимо всі доступні моделі (тільки якщо потрібно)
        if len(model_options) <= 10:
            print(f"AVAILABLE_MODELS: {len(model_options)}")
            for idx, opt in enumerate(model_options):
                print(f"  {idx + 1}. {opt.text.strip()}")
        else:
            print(f"AVAILABLE_MODELS: {len(model_options)} (showing first 5)")
            for idx, opt in enumerate(model_options[:5]):
                print(f"  {idx + 1}. {opt.text.strip()}")
            print(f"  ... та ще {len(model_options) - 5} моделей")

        # Спочатку шукаємо точний збіг
        selected_model = None
        model_upper = model.upper()
        for opt in model_options:
            opt_text_upper = opt.text.strip().upper()
            # Точний збіг або модель міститься в тексті опції
            if model_upper in opt_text_upper:
                selected_model = opt
                print(f"MATCH_FOUND: {opt.text.strip()}")
                break

        # Якщо не знайшли, беремо перший варіант
        if not selected_model and model_options:
            selected_model = model_options[0]
            print(f"NO_MATCH_USING_FIRST")

        if not selected_model:
            raise Exception("NO_MODEL_FOUND")

        print(f"MODEL: {selected_model.text.strip()}")
        self.safe_click(selected_model)
        time.sleep(0.5)
        self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".modelsList .carselector-list-element")))

        engine_input = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".carsInput:not([readonly])")))
        self.safe_click(engine_input)
        time.sleep(0.5)

        engine_options = self.wait.until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".carsList .carselector-list-element")))

        # Фільтруємо двигуни за роком (тільки 2019+)
        if filter_year_from:
            filtered_engines = []
            for opt in engine_options:
                engine_text = opt.text.strip()
                year = self.extract_year_from_engine(engine_text)
                if year and year >= filter_year_from:
                    filtered_engines.append(opt)
                elif not year:
                    # Якщо не вдалося визначити рік, включаємо двигун
                    filtered_engines.append(opt)

            if filtered_engines:
                engine_options = filtered_engines
                print(f"FILTERED_ENGINES: {len(engine_options)} (year >= {filter_year_from})")
            else:
                print(f"NO_ENGINES_AFTER_FILTER (year >= {filter_year_from})")

        if engine_index == -1:
            return [opt.text.strip() for opt in engine_options]

        if engine_index >= len(engine_options):
            engine_index = 0

        selected_engine = engine_options[engine_index]
        print(f"ENGINE: {selected_engine.text.strip()}")
        self.safe_click(selected_engine)
        time.sleep(0.5)

        return True

    def get_available_engines(self, make, model):
        print(f"GET_ENGINES: {make} {model}")
        try:
            self.driver.get(self.base_url)
            time.sleep(2)
            self.handle_cookies()
            time.sleep(1)

            # Натискаємо кнопку Select Vehicle
            self.open_vehicle_selector()

            engines = self.select_make_model_engine(make, model, engine_index=-1)
            print(f"ENGINES_FOUND: {len(engines)}")
            return engines

        except Exception as e:
            print(f"GET_ENGINES_ERROR: {e}")
            return []

    def select_car(self, make, model, engine_index=0, force_refresh=True):
        print(f"SELECT_CAR: {make} {model} engine_{engine_index}")
        try:
            if force_refresh:
                self.driver.delete_all_cookies()
                self.driver.get(self.base_url)
                time.sleep(2)
                self.handle_cookies()
                time.sleep(1)

                # Спробуємо натиснути кнопку Select Vehicle одразу після завантаження
                self.open_vehicle_selector()
            else:
                self.reset_car_selection()

            result = self.select_make_model_engine(make, model, engine_index)
            if result is True:
                self.wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='All Products']")))
                print("CAR_SELECTED")
                return True
            return False

        except Exception as e:
            print(f"CAR_ERROR: {e}")
            return False

    def go_to_catalog(self):
        print("CATALOG")
        try:
            try:
                select_vehicle_btn = self.short_wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Please select vehicle')]"))
                )
                self.safe_click(select_vehicle_btn)
                time.sleep(0.5)
            except:
                pass

            all_products_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='All Products']")))
            self.safe_click(all_products_btn)

            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#product-overview__product-boxes")))
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-box.card")))

            products_count = len(self.driver.find_elements(By.CSS_SELECTOR, ".product-box.card"))
            print(f"CATALOG_OK: {products_count}")
            return True

        except Exception as e:
            print(f"CATALOG_ERROR: {e}")
            return False

    def click_product(self, index):
        print(f"CLICK_{index + 1}")
        try:
            time.sleep(0.3)

            products = self.driver.find_elements(By.CSS_SELECTOR, ".product-box.card")
            if index >= len(products):
                print(f"NO_PRODUCT_{index + 1}")
                return False

            button = products[index].find_element(By.CSS_SELECTOR, ".button--to-product")
            self.safe_click(button)

            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product__title")))
            print("OPENED")
            return True

        except Exception as e:
            print(f"CLICK_ERROR_{index + 1}: {e}")
            return False

    def go_back(self):
        print("BACK")
        try:
            self.driver.back()
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#product-overview__product-boxes")))
            time.sleep(0.3)
            print("BACK_OK")
            return True
        except Exception as e:
            print(f"BACK_ERROR: {e}")
            return self.go_to_catalog()

    def find_all_option_groups(self):
        try:
            option_groups = self.driver.find_elements(By.CSS_SELECTOR, ".list-group-item.att_group")
            result = []

            for group_idx, group in enumerate(option_groups):
                try:
                    label_elem = group.find_element(By.CSS_SELECTOR, "h4.label span")
                    group_label = re.sub(r'^\d+\.\s*', '', label_elem.text.strip()).replace('\n', ' ').strip()

                    options = group.find_elements(By.CSS_SELECTOR, "a.btn--outline-selectable")
                    option_texts = []

                    for opt in options:
                        opt_text = opt.text.strip().replace('\n', ' ')
                        if opt_text:
                            option_texts.append(opt_text)

                    not_selected_elem = group.find_elements(By.CSS_SELECTOR, ".none-selected")
                    is_not_selected = len(not_selected_elem) > 0

                    if not option_texts and not is_not_selected:
                        continue

                    if is_not_selected and not option_texts:
                        all_buttons = group.find_elements(By.CSS_SELECTOR, "button, a")
                        for btn in all_buttons:
                            btn_text = btn.text.strip()
                            if btn_text and btn_text.upper() not in ['NOT YET SELECTED', '']:
                                options.append(btn)
                                option_texts.append(btn_text)

                    if not option_texts:
                        option_texts = ["not yet selected"]

                    result.append({
                        'label': group_label,
                        'element': group,
                        'options': options,
                        'option_texts': option_texts,
                        'is_not_selected': is_not_selected,
                        'group_index': group_idx
                    })

                    opts_preview = ', '.join(option_texts[:2])
                    if len(option_texts) > 2:
                        opts_preview += f'... +{len(option_texts) - 2}'
                    status = "UNSELECTED" if is_not_selected else "SELECTED"
                    print(f"GROUP_{group_idx + 1}: {group_label} [{status}] ({len(option_texts)}: {opts_preview})")

                except Exception as e:
                    print(f"GROUP_{group_idx}_ERROR: {e}")
                    continue

            print(f"TOTAL_GROUPS: {len(result)}")
            return result

        except Exception as e:
            print(f"GROUPS_ERROR: {e}")
            return []

    def force_select_option_in_group(self, group_info, option_index=0):
        try:
            if not group_info['options'] or option_index >= len(group_info['options']):
                print(f"  NO_OPTIONS_TO_SELECT")
                return False

            option_elem = group_info['options'][option_index]
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option_elem)
            time.sleep(0.3)

            self.driver.execute_script("arguments[0].click();", option_elem)
            time.sleep(0.6)

            print(
                f"  CLICKED: {group_info['option_texts'][option_index] if option_index < len(group_info['option_texts']) else 'option_' + str(option_index)}")
            return True

        except Exception as e:
            print(f"  CLICK_FAILED: {e}")
            return False

    def ensure_all_options_selected(self):
        max_attempts = 3

        for attempt in range(max_attempts):
            print(f"ENSURE_PASS_{attempt + 1}")

            option_groups = self.find_all_option_groups()
            if not option_groups:
                print("NO_GROUPS_FOUND")
                return False

            unselected_count = 0

            for group_info in option_groups:
                if group_info['is_not_selected'] and group_info['options']:
                    unselected_count += 1
                    print(f"  SELECTING: {group_info['label']}")
                    self.force_select_option_in_group(group_info, 0)

            if unselected_count == 0:
                print("ALL_OPTIONS_SELECTED")
                return True
            else:
                print(f"UNSELECTED_REMAIN: {unselected_count}")
                time.sleep(1)

        print("ENSURE_FAILED")
        return False

    def get_selected_options_values(self, option_groups):
        options_dict = {}
        try:
            for group_info in option_groups:
                group_label = group_info['label']
                selected_value = None

                for idx, opt in enumerate(group_info['options']):
                    elem_class = opt.get_attribute('class') or ''
                    if 'selected' in elem_class or 'active' in elem_class:
                        selected_value = group_info['option_texts'][idx] if idx < len(
                            group_info['option_texts']) else opt.text.strip()
                        break

                options_dict[group_label] = selected_value if selected_value else 'not selected'

        except Exception as e:
            print(f"GET_SELECTED_ERROR: {e}")

        return options_dict

    def check_electronic_damper(self, option_groups):
        """
        Перевіряє наявність електронних демпферів у групах опцій.
        Повертає: 'yes', 'no', або 'unknown'
        """
        try:
            for group_info in option_groups:
                group_label = group_info['label'].lower()

                # Шукаємо опції пов'язані з електронним амортизатором
                if 'vehicle has electronic damper' in group_label or \
                   'electronic damper' in group_label or \
                   ('electronic' in group_label and 'damper' in group_label):

                    print(f"DAMPER_GROUP_FOUND: {group_info['label']}")
                    print(f"DAMPER_OPTIONS: {group_info['option_texts']}")

                    # Якщо група ще не вибрана (UNSELECTED), дивимось на доступні опції
                    if group_info.get('is_not_selected', False):
                        # Дивимось на доступні опції - якщо є YES і NO, значить потрібен вибір
                        options_text = ' '.join([str(opt).upper() for opt in group_info['option_texts']])
                        if 'YES' in options_text and 'NO' in options_text:
                            print(f"ELECTRONIC_DAMPER: unknown (needs selection - both YES and NO available)")
                            return 'unknown'
                        elif 'YES' in options_text:
                            print(f"ELECTRONIC_DAMPER: yes (only YES available)")
                            return 'yes'
                        elif 'NO' in options_text:
                            print(f"ELECTRONIC_DAMPER: no (only NO available)")
                            return 'no'

                    # Перевіряємо вибране значення
                    for idx, opt in enumerate(group_info['options']):
                        try:
                            elem_class = opt.get_attribute('class') or ''
                            if 'selected' in elem_class or 'active' in elem_class:
                                selected_value = group_info['option_texts'][idx] if idx < len(
                                    group_info['option_texts']) else opt.text.strip()
                                selected_value_upper = str(selected_value).upper()

                                print(f"DAMPER_SELECTED_VALUE: {selected_value}")

                                if selected_value_upper == 'YES':
                                    print(f"ELECTRONIC_DAMPER: yes")
                                    return 'yes'
                                elif selected_value_upper == 'NO':
                                    print(f"ELECTRONIC_DAMPER: no")
                                    return 'no'
                        except:
                            continue

                    # Якщо є група з електронними демпферами, але не визначено значення
                    print(f"ELECTRONIC_DAMPER: unknown (group found but no clear selection)")
                    return 'unknown'

            # Якщо не знайдено жодної групи з електронними демпферами
            print("ELECTRONIC_DAMPER: not applicable (no damper options found)")
            return 'not applicable'

        except Exception as e:
            print(f"CHECK_DAMPER_ERROR: {e}")
            return 'unknown'

    def extract_suspension_type(self, title):
        """Витягує тип підвіски з назви продукту (V1, V2, V3, V4, DDC і т.д.)"""
        import re

        title_upper = title.upper()

        # Шукаємо різні типи підвісок
        patterns = [
            r'\bV1\b',
            r'\bV2\b',
            r'\bV3\b',
            r'\bV4\b',
            r'\bDDC\b',
            r'\bCLUBSPORT\b',
            r'\bLEVELING\b',
            r'\bST\b',
            r'\bHLS\b',
        ]

        for pattern in patterns:
            match = re.search(pattern, title_upper)
            if match:
                suspension_type = match.group(0)
                print(f"SUSPENSION_TYPE: {suspension_type}")
                return suspension_type

        print("SUSPENSION_TYPE: Unknown")
        return "Unknown"

    def get_title(self):
        try:
            title_elem = self.wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.product__title"))
            )
            title = title_elem.text.strip()
            print(f"TITLE: {title}")
            return title
        except Exception as e:
            print(f"TITLE_ERROR: {e}")
            return "Unknown Product"

    def get_sku(self):
        try:
            sku_elem = self.wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".product__article-number > span:last-of-type"))
            )

            for attempt in range(5):
                sku = sku_elem.text.strip().upper()
                if "NOT YET SELECTED" not in sku and sku:
                    print(f"SKU: {sku}")
                    return sku
                time.sleep(0.7)

            print(f"SKU_STILL_PENDING")
            return f"PENDING_{hash(str(self.get_title())) % 100000}"

        except Exception as e:
            print(f"SKU_ERROR: {e}")
            return f"NO_SKU_{hash(str(e)) % 10000}"

    def get_price(self):
        try:
            js_price = self.driver.execute_script("""
                var prices = [];
                var elements = document.querySelectorAll('[data-bind*="getFormatedPrice"], .price, [class*="price"]');

                for (var i = 0; i < elements.length; i++) {
                    var text = elements[i].textContent || elements[i].innerText || '';
                    if (text.includes('€')) {
                        var matches = text.match(/€\\s*(\\d+(?:[.,]\\d+)*)/g);
                        if (matches) {
                            matches.forEach(function(match) {
                                var num = parseFloat(match.replace(/[€,]/g, '').trim());
                                if (num >= 100 && num <= 20000) {
                                    prices.push(num);
                                }
                            });
                        }
                    }
                }

                return prices.length > 0 ? Math.max(...prices) : null;
            """)

            if js_price:
                eur = math.ceil(js_price)
                uah = math.ceil(eur * 49)
                print(f"PRICE: {eur}EUR/{uah}UAH")
                return eur, uah
        except Exception as e:
            print(f"PRICE_ERROR: {e}")

        print("NO_PRICE")
        return 1000, 49000

    def get_description(self):
        try:
            desc_tab = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='#beschreibung']"))
            )
            self.safe_click(desc_tab)

            self.short_wait.until(EC.visibility_of_element_located((By.ID, "beschreibung")))

            desc_elem = self.driver.find_element(By.ID, "beschreibung")
            html = desc_elem.get_attribute('innerHTML').strip()

            clean_html = re.sub(r'\s*data-bind=".*?"', '', html)
            clean_html = re.sub(r'<!--\s*ko\s.*?-->', '', clean_html, flags=re.DOTALL)
            clean_html = re.sub(r'<!--\s*/ko\s*-->', '', clean_html)

            print("DESC_OK")
            return f"<h3>Description</h3>{clean_html}"
        except Exception as e:
            print(f"DESC_ERROR: {e}")
            return "<h3>Description</h3><p>Product description not available</p>"

    def get_image_urls(self):
        try:
            image_urls = []

            gallery_container = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".gallery-slider-container"))
            )

            image_elements = gallery_container.find_elements(By.CSS_SELECTOR, "img.gallery-slider-image")

            for img in image_elements:
                src = img.get_attribute('src')
                if src and src not in image_urls:
                    image_urls.append(src)

            print(f"IMAGES_FOUND: {len(image_urls)}")
            return image_urls

        except Exception as e:
            print(f"IMAGES_ERROR: {e}")
            return []

    def get_technical_data_and_documents(self):
        """Extracts technical data and documents from the product page."""
        additional_data_html = ""
        try:
            # --- Extract Technical Data ---
            try:
                tech_data_tab = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='#technischedaten']"))
                )
                self.safe_click(tech_data_tab)
                time.sleep(0.5)

                tech_data_content = self.driver.find_element(By.ID, "technischedaten")
                additional_data_html += f"<h3>Technical Data</h3>{tech_data_content.get_attribute('innerHTML')}"
            except TimeoutException:
                print("NO_TECH_DATA_TAB")

            # --- Extract Documents ---
            try:
                documents_tab = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='#dokumente']"))
                )
                self.safe_click(documents_tab)
                time.sleep(0.5)

                documents_content = self.driver.find_element(By.ID, "dokumente")
                additional_data_html += f"<h3>Documents</h3>{documents_content.get_attribute('innerHTML')}"
            except TimeoutException:
                print("NO_DOCUMENTS_TAB")

            return additional_data_html

        except Exception as e:
            print(f"ADDITIONAL_DATA_ERROR: {e}")
            return ""

    def get_compatibility(self):
        try:
            comp_tab = self.short_wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='#kompatibel']"))
            )
            self.safe_click(comp_tab)
            time.sleep(0.5)

            self.wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#kompatibel table tbody tr td"))
            )

            table = self.driver.find_element(By.CSS_SELECTOR, "#kompatibel table")
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")

            cars = []
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 3:
                    car = {
                        'make': cells[0].text.strip(),
                        'model': cells[1].text.strip(),
                        'engine': cells[2].text.strip()
                    }
                    if car['make'] and car['model']:
                        cars.append(car)

            print(f"COMPAT: {len(cars)}")
            return cars

        except TimeoutException:
            print("NO_COMPAT_TAB")
            return []
        except Exception as e:
            print(f"COMPAT_ERROR: {e}")
            return []

    def create_sku(self, base_sku, make, model, engine, options_dict):
        unique_part = f"{make}-{model}-{engine}".replace(' ', '-').replace('(', '').replace(')', '')
        for value in sorted(options_dict.values()):
            unique_part += f"-{value}"
        hash_part = hashlib.md5(unique_part.encode()).hexdigest()[:6]
        return f"{base_sku}-{hash_part}"

    def process_product_variant(self, base_title, initial_make, initial_model, selected_options, info_options, base_sku, has_electronic_damper=None):
        price_eur, price_uah = self.extractor.get_price()
        description = self.extractor.get_description()
        image_urls = self.extractor.get_image_urls()
        additional_data_html = self.extractor.get_technical_data_and_documents()
        compatibility = self.extractor.get_compatibility()

        return self.formatter.format_product(base_title, initial_make, initial_model, selected_options, info_options, base_sku, has_electronic_damper, price_eur, price_uah, description, image_urls, additional_data_html, compatibility)

    def process_product(self, initial_make, initial_model, base_sku):
        print("PROCESS")

        title = self.extractor.get_title()
        all_variants = []

        option_groups = self.find_all_option_groups()

        if not option_groups:
            print("NO_OPTIONS")
            variant_products = self.process_product_variant(title, initial_make, initial_model, {}, {}, base_sku, has_electronic_damper='not applicable')
            all_variants.extend(variant_products)
            return all_variants

        print(f"INITIAL_GROUPS: {len(option_groups)}")

        # ВАЖЛИВО: Зберігаємо інформацію про електронні демпфери ДО того як вибирати опції
        has_electronic_damper_initial = self.check_electronic_damper(option_groups)

        print("ENSURING_ALL_SELECTED")
        self.ensure_all_options_selected()

        time.sleep(1)
        option_groups = self.find_all_option_groups()

        all_options_info = {group_info['label']: group_info['option_texts'] for group_info in option_groups}

        # НЕ створюємо окремі варіанти для демпферів - тільки для інших опцій
        groups_to_combine = []

        for g in option_groups:
            group_label_lower = g['label'].lower()
            # Перевіряємо чи це група демпферів
            is_damper_group = 'vehicle has electronic damper' in group_label_lower or 'electronic damper' in group_label_lower

            # Групу демпферів пропускаємо - не включаємо в комбінації
            if is_damper_group:
                print(f"DAMPER_GROUP_SKIPPED: {g['label']} (буде в описі)")
                continue

            # Звичайні групи опцій
            if 2 <= len(g['options']) <= 4 and not g['is_not_selected']:
                groups_to_combine.append(g)

        if not groups_to_combine:
            print("NO_COMBINABLE")
            selected_options = self.get_selected_options_values(option_groups)
            variant_products = self.process_product_variant(title, initial_make, initial_model, selected_options,
                                                            all_options_info, base_sku, has_electronic_damper_initial)
            all_variants.extend(variant_products)
        else:
            from itertools import product as itertools_product

            combinations = list(itertools_product(*[range(len(g['options'])) for g in groups_to_combine]))
            total_combinations = len(combinations)

            if total_combinations > 24:
                print(f"TOO_MANY: {total_combinations}")
                selected_options = self.get_selected_options_values(option_groups)
                variant_products = self.process_product_variant(title, initial_make, initial_model, selected_options,
                                                                all_options_info, base_sku, has_electronic_damper_initial)
                all_variants.extend(variant_products)
            else:
                print(f"COMBOS: {total_combinations}")

                for combo_idx, combination in enumerate(combinations):
                    print(f"COMBO_{combo_idx + 1}/{total_combinations}")

                    try:
                        option_groups_fresh = self.find_all_option_groups()
                        if not option_groups_fresh:
                            print(f"NO_GROUPS_{combo_idx + 1}")
                            break

                        groups_to_combine_refresh = [g for g in option_groups_fresh if
                                                     2 <= len(g['options']) <= 4 and not g['is_not_selected']]

                        combo_iter = iter(combination)

                        for group_info in option_groups_fresh:
                            is_combinable = any(g['label'] == group_info['label'] for g in groups_to_combine_refresh)
                            if is_combinable and groups_to_combine_refresh:
                                try:
                                    idx = next(combo_iter)
                                    self.force_select_option_in_group(group_info, idx)
                                except StopIteration:
                                    pass

                        time.sleep(0.7)
                        selected_options = self.get_selected_options_values(option_groups_fresh)

                        variant_products = self.process_product_variant(title, initial_make, initial_model,
                                                                        selected_options, all_options_info, base_sku, has_electronic_damper_initial)
                        all_variants.extend(variant_products)

                    except Exception as e:
                        print(f"COMBO_ERROR_{combo_idx + 1}: {e}")
                        continue

        print(f"TOTAL: {len(all_variants)}")
        return all_variants

    def run_parsing(self, make="VW", model="GOLF VIII (CD1, DA1)", max_engines=None):
        print(f"RUN: {make} {model}")

        current_run_products = []

        print("Getting available engines...")
        engines = self.get_available_engines(make, model)
        if not engines:
            print("NO_ENGINES")
            return []

        if max_engines:
            engines = engines[:max_engines]

        print(f"ENGINES: {len(engines)}")

        seen_products = set()
        seen_skus = set()
        processed_product_titles = set()  # Відстежуємо оброблені назви товарів

        # Спочатку обробимо перший двигун щоб отримати всі продукти
        print(f"ENGINE_1/{len(engines)}: {engines[0]}")

        try:
            print("Selecting car...")
            if not self.select_car(make, model, 0, force_refresh=True):
                print(f"SKIP_ENGINE_1")
                return []
            print("Car selected.")

            print("Going to catalog...")
            if not self.go_to_catalog():
                print(f"SKIP_CATALOG_1")
                return []
            print("In catalog.")

            products = self.driver.find_elements(By.CSS_SELECTOR, ".product-box.card")
            total = len(products)
            print(f"PRODUCTS: {total}")

            for i in range(total):
                print(f"PRODUCT_{i + 1}/{total}")

                try:
                    print(f"Clicking product {i+1}...")
                    if not self.click_product(i):
                        continue
                    print(f"Product {i+1} clicked.")

                    title = self.get_title()
                    base_sku = self.get_sku()

                    if base_sku in seen_skus:
                        print(f"DUP_SKU: {base_sku}")
                        if i < total - 1:
                            self.go_back()
                        continue

                    seen_skus.add(base_sku)
                    processed_product_titles.add(title)

                    product_key = f"{make}|{model}|{title}"
                    if product_key in seen_products:
                        print(f"DUP_TITLE")
                        if i < total - 1:
                            self.go_back()
                        continue

                    seen_products.add(product_key)

                    variants = self.process_product(make, model, base_sku)
                    if variants:
                        current_run_products.extend(variants)
                        print(f"ADDED: {len(variants)}")

                    if i < total - 1:
                        self.go_back()

                except Exception as e:
                    print(f"ERROR_{i + 1}: {e}")
                    if i < total - 1:
                        try:
                            self.go_back()
                        except:
                            break

        except Exception as e:
            print(f"ENGINE_ERROR_1: {e}")

        # Тепер перевіримо інші двигуни на унікальні продукти
        print(f"\nCHECKING_OTHER_ENGINES for unique products...")

        for engine_idx in range(1, min(3, len(engines))):  # Перевіримо тільки 2-3 двигуни для оптимізації
            engine_name = engines[engine_idx]
            print(f"ENGINE_{engine_idx + 1}/{len(engines)}: {engine_name}")

            try:
                if not self.select_car(make, model, engine_idx, force_refresh=True):
                    print(f"SKIP_ENGINE_{engine_idx + 1}")
                    continue

                if not self.go_to_catalog():
                    print(f"SKIP_CATALOG_{engine_idx + 1}")
                    continue

                products = self.driver.find_elements(By.CSS_SELECTOR, ".product-box.card")
                total = len(products)

                new_products_found = 0
                for i in range(total):
                    try:
                        if not self.click_product(i):
                            continue

                        title = self.get_title()

                        # Якщо цей продукт вже оброблений, пропускаємо
                        if title in processed_product_titles:
                            if i < total - 1:
                                self.go_back()
                            continue

                        # Знайшли новий унікальний продукт!
                        print(f"NEW_PRODUCT_FOUND: {title}")
                        new_products_found += 1

                        base_sku = self.get_sku()
                        seen_skus.add(base_sku)
                        processed_product_titles.add(title)

                        product_key = f"{make}|{model}|{title}"
                        seen_products.add(product_key)

                        variants = self.process_product(make, model, base_sku)
                        if variants:
                            current_run_products.extend(variants)
                            print(f"ADDED: {len(variants)}")

                        if i < total - 1:
                            self.go_back()

                    except Exception as e:
                        print(f"ERROR_{i + 1}: {e}")
                        if i < total - 1:
                            try:
                                self.go_back()
                            except:
                                break

                print(f"NEW_PRODUCTS_IN_ENGINE_{engine_idx + 1}: {new_products_found}")

                # Якщо не знайшли нових продуктів, можна припинити перевірку інших двигунів
                if new_products_found == 0:
                    print("NO_NEW_PRODUCTS - stopping engine check")
                    break

            except Exception as e:
                print(f"ENGINE_ERROR_{engine_idx + 1}: {e}")
                continue

        print(f"\nFINISHED: {len(current_run_products)} total variants from {len(processed_product_titles)} unique products")
        print(f"Finished scraping for {make} {model}.")
        return current_run_products

    def close(self):
        if hasattr(self, 'driver'):
            self.driver.quit()
            print("CLOSED")


def save_csv(products, filename):
    if not products:
        print("NO_PRODUCTS")
        return False

    fields = [
        'Handle', 'Title', 'Body (HTML)', 'Vendor', 'Product Category', 'Type', 'Tags', 'Published',
        'Option1 Name', 'Option1 Value', 'Option2 Name', 'Option2 Value', 'Option3 Name', 'Option3 Value',
        'Variant SKU', 'Variant Grams', 'Variant Inventory Tracker', 'Variant Inventory Qty',
        'Variant Inventory Policy', 'Variant Fulfillment Service', 'Variant Price', 'Variant Compare At Price',
        'Variant Requires Shipping', 'Variant Taxable', 'Variant Barcode', 'Image Src', 'Image Position',
        'Image Alt Text', 'Gift Card', 'SEO Title', 'SEO Description', 'Google Shopping / Google Product Category',
        'Google Shopping / MPN', 'Google Shopping / Age Group', 'Google Shopping / Gender',
        'Google Shopping / Custom Product',
        'Google Shopping / Custom Label 0', 'Google Shopping / Custom Label 1', 'Google Shopping / Custom Label 2',
        'Google Shopping / Custom Label 3', 'Google Shopping / Custom Label 4', 'Variant Image', 'Variant Weight Unit',
        'Variant Tax Code', 'Cost per item', 'Price / International', 'Compare At Price / International', 'Status',
        'metafield:custom.price_eur[single_line_text_field]',
        'metafield:custom.vehicle_make[single_line_text_field]',
        'metafield:custom.vehicle_model[single_line_text_field]',
        'metafield:custom.vehicle_engine[single_line_text_field]',
        'metafield:custom.electronic_damper[single_line_text_field]'
    ]

    processed_handles = set()

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()

            for i, product in enumerate(products):
                handle = product.get('Handle')
                if handle not in processed_handles:
                    # First time seeing this handle, write the full product row
                    row = {field: str(product.get(field, '')) if product.get(field) is not None else '' for field in fields}
                    writer.writerow(row)
                    processed_handles.add(handle)
                else:
                    # Subsequent rows for the same handle should only contain image data
                    image_row = {
                        'Handle': handle,
                        'Image Src': product.get('Image Src', ''),
                        'Image Position': product.get('Image Position', '')
                    }
                    writer.writerow(image_row)

        print(f"CSV: {filename} ({len(products)})")
        return True

    except Exception as e:
        print(f"CSV_ERROR: {e}")
        return False


def main():
    CARS_TO_SCRAPE = [
        {"make": "BMW", "models": ["G80", "G82", "X5"]},
        {"make": "PORSCHE", "models": ["911", "Taycan"]},
        {"make": "AUDI", "models": ["RS6", "R8"]},
        {"make": "MERCEDES-BENZ", "models": ["C-Klasse", "S-Klasse", "G-Klasse"]},
        {"make": "TOYOTA", "models": ["Supra", "Yaris"]},
        {"make": "FORD", "models": ["Mustang"]},
    ]

    all_products = []
    parser = KWParser()

    try:
        for car in CARS_TO_SCRAPE:
            make = car["make"]
            for model in car["models"]:
                print(f"--- Scraping {make} {model} ---")
                products = parser.run_parsing(make, model)
                if products:
                    all_products.extend(products)
                    print(f"--- Found {len(products)} products for {make} {model} ---")
                else:
                    print(f"--- No products found for {make} {model} ---")
                time.sleep(5)

        if all_products:
            filename = "shopify_products.csv"
            save_csv(all_products, filename)
        else:
            print("NO_RESULTS_FOUND_AT_ALL")

    except Exception as e:
        print(f"MAIN_ERROR: {e}")
    finally:
        parser.close()


if __name__ == "__main__":
    main()
