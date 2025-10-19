#!/usr/bin/env python3
"""
KW Suspensions Parser
Parses all KW suspension products from KW automotive Shopify store and exports to CSV
"""

import requests
import csv
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import sys

# Constants
DEFAULT_DESCRIPTION_LENGTH = 500  # Maximum length for product description in CSV


class KWParser:
    """Parser for KW automotive Shopify store"""
    
    def __init__(self, store_url: str = "https://kw-automotive.com"):
        """
        Initialize the parser
        
        Args:
            store_url: Base URL of the KW automotive Shopify store
        """
        self.store_url = store_url.rstrip('/')
        self.products_api = f"{self.store_url}/products.json"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def fetch_products_page(self, page: int = 1, limit: int = 250) -> Optional[Dict]:
        """
        Fetch a page of products from the Shopify store
        
        Args:
            page: Page number to fetch
            limit: Number of products per page (max 250 for Shopify)
            
        Returns:
            Dictionary containing products data or None on error
        """
        try:
            params = {
                'page': page,
                'limit': limit
            }
            response = self.session.get(self.products_api, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            return None
    
    def parse_all_products(self) -> List[Dict]:
        """
        Parse all products from the store
        
        Returns:
            List of all products
        """
        all_products = []
        page = 1
        
        print(f"Fetching products from {self.store_url}...")
        
        while True:
            print(f"Fetching page {page}...")
            data = self.fetch_products_page(page)
            
            if not data or 'products' not in data:
                print(f"No data returned for page {page}")
                break
            
            products = data['products']
            
            if not products:
                print(f"No more products found at page {page}")
                break
            
            all_products.extend(products)
            print(f"Found {len(products)} products on page {page} (Total: {len(all_products)})")
            
            # Check if we've reached the last page
            if len(products) < 250:
                break
            
            page += 1
            time.sleep(0.5)  # Be polite to the server
        
        print(f"\nTotal products fetched: {len(all_products)}")
        return all_products
    
    def extract_product_data(self, product: Dict) -> Dict:
        """
        Extract relevant data from a product
        
        Args:
            product: Raw product data from Shopify API
            
        Returns:
            Dictionary with extracted product information
        """
        # Get the first variant data (or default values)
        variants = product.get('variants', [])
        first_variant = variants[0] if variants else {}
        
        # Extract basic product info
        extracted = {
            'id': product.get('id', ''),
            'title': product.get('title', ''),
            'handle': product.get('handle', ''),
            'vendor': product.get('vendor', ''),
            'product_type': product.get('product_type', ''),
            'created_at': product.get('created_at', ''),
            'updated_at': product.get('updated_at', ''),
            'published_at': product.get('published_at', ''),
            'tags': ', '.join(product.get('tags', [])),
            'price': first_variant.get('price', ''),
            'compare_at_price': first_variant.get('compare_at_price', ''),
            'sku': first_variant.get('sku', ''),
            'inventory_quantity': first_variant.get('inventory_quantity', ''),
            'available': first_variant.get('available', False),
            'url': f"{self.store_url}/products/{product.get('handle', '')}",
            'variant_count': len(variants),
        }
        
        # Add images
        images = product.get('images', [])
        if images:
            extracted['image_url'] = images[0].get('src', '')
            extracted['image_count'] = len(images)
        else:
            extracted['image_url'] = ''
            extracted['image_count'] = 0
        
        # Add description (truncated to avoid overly large CSV fields)
        description = product.get('body_html', '')
        extracted['description'] = description[:DEFAULT_DESCRIPTION_LENGTH] if description else ''
        
        return extracted
    
    def save_to_csv(self, products: List[Dict], filename: str = None) -> str:
        """
        Save products to CSV file
        
        Args:
            products: List of product dictionaries
            filename: Output filename (default: kw_products_TIMESTAMP.csv)
            
        Returns:
            Path to the saved CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'kw_products_{timestamp}.csv'
        
        if not products:
            print("No products to save!")
            return filename
        
        # Extract data from all products
        extracted_products = [self.extract_product_data(p) for p in products]
        
        # Get all unique keys for CSV headers
        fieldnames = list(extracted_products[0].keys())
        
        # Write to CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(extracted_products)
        
        print(f"\nProducts saved to: {filename}")
        print(f"Total products in CSV: {len(extracted_products)}")
        
        return filename
    
    def run(self, output_file: str = None) -> str:
        """
        Run the complete parsing process
        
        Args:
            output_file: Optional output filename
            
        Returns:
            Path to the saved CSV file
        """
        print("=" * 60)
        print("KW Suspensions Parser")
        print("=" * 60)
        
        # Fetch all products
        products = self.parse_all_products()
        
        if not products:
            print("No products found!")
            return None
        
        # Save to CSV
        return self.save_to_csv(products, output_file)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Parse KW suspension products from KW automotive Shopify store'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output CSV filename (default: kw_products_TIMESTAMP.csv)',
        default=None
    )
    parser.add_argument(
        '-u', '--url',
        help='Store URL (default: https://kw-automotive.com)',
        default='https://kw-automotive.com'
    )
    
    args = parser.parse_args()
    
    # Create parser and run
    kw_parser = KWParser(store_url=args.url)
    output_file = kw_parser.run(output_file=args.output)
    
    if output_file:
        print(f"\n✓ Successfully parsed KW products to {output_file}")
        return 0
    else:
        print("\n✗ Failed to parse products")
        return 1


if __name__ == '__main__':
    sys.exit(main())
