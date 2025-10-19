#!/usr/bin/env python3
"""
Example usage of KW Parser

This script demonstrates how to use the KW Parser with different configurations
"""

from kw_parser import KWParser


def example_basic_usage():
    """Example: Basic usage with default settings"""
    print("\n" + "=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)
    
    parser = KWParser()
    output_file = parser.run()
    
    if output_file:
        print(f"Success! Products saved to: {output_file}")


def example_custom_output():
    """Example: Custom output filename"""
    print("\n" + "=" * 60)
    print("Example 2: Custom Output Filename")
    print("=" * 60)
    
    parser = KWParser()
    output_file = parser.run(output_file='my_custom_products.csv')
    
    if output_file:
        print(f"Success! Products saved to: {output_file}")


def example_custom_store():
    """Example: Different store URL"""
    print("\n" + "=" * 60)
    print("Example 3: Custom Store URL")
    print("=" * 60)
    
    # You can parse from a different Shopify store
    parser = KWParser(store_url='https://example-store.myshopify.com')
    
    # Fetch products
    products = parser.parse_all_products()
    
    if products:
        # Save to CSV
        output_file = parser.save_to_csv(products, 'custom_store_products.csv')
        print(f"Success! Products saved to: {output_file}")


def example_manual_control():
    """Example: Manual control over the parsing process"""
    print("\n" + "=" * 60)
    print("Example 4: Manual Control")
    print("=" * 60)
    
    parser = KWParser()
    
    # Fetch products
    print("Fetching products...")
    products = parser.parse_all_products()
    
    if not products:
        print("No products found!")
        return
    
    # Process products (you can add custom logic here)
    print(f"\nProcessing {len(products)} products...")
    
    # Filter only specific product types (example)
    coilover_products = [
        p for p in products 
        if 'coilover' in p.get('product_type', '').lower()
    ]
    
    print(f"Found {len(coilover_products)} coilover products")
    
    # Save filtered products
    if coilover_products:
        output_file = parser.save_to_csv(coilover_products, 'kw_coilovers_only.csv')
        print(f"Filtered products saved to: {output_file}")


def example_product_inspection():
    """Example: Inspect product data before saving"""
    print("\n" + "=" * 60)
    print("Example 5: Product Data Inspection")
    print("=" * 60)
    
    parser = KWParser()
    
    # Fetch first page only
    data = parser.fetch_products_page(page=1, limit=10)
    
    if data and 'products' in data:
        products = data['products']
        print(f"Fetched {len(products)} products from first page")
        
        # Inspect first product
        if products:
            first_product = products[0]
            print(f"\nFirst product details:")
            print(f"  Title: {first_product.get('title')}")
            print(f"  Vendor: {first_product.get('vendor')}")
            print(f"  Type: {first_product.get('product_type')}")
            print(f"  Tags: {first_product.get('tags')}")
            
            # Extract and display formatted data
            extracted = parser.extract_product_data(first_product)
            print(f"\nExtracted data:")
            for key, value in extracted.items():
                print(f"  {key}: {value}")


def main():
    """Run examples"""
    print("=" * 60)
    print("KW Parser - Usage Examples")
    print("=" * 60)
    
    # Note: These examples will fail in environments without network access
    # or when the store is unreachable. They are provided for demonstration.
    
    print("\nNote: Examples are provided for demonstration.")
    print("They require network access to the KW automotive store.")
    print("\nTo run the parser with real data, use:")
    print("  python kw_parser.py")
    print("\nFor help and options:")
    print("  python kw_parser.py --help")


if __name__ == '__main__':
    main()
