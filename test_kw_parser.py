#!/usr/bin/env python3
"""
Test script for KW Parser - uses mock data to verify functionality
"""

import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kw_parser import KWParser


def test_extract_product_data():
    """Test product data extraction"""
    
    # Mock product data similar to Shopify API response
    mock_product = {
        'id': 12345678,
        'title': 'KW V1 Coilover Kit - BMW 3 Series E90',
        'handle': 'kw-v1-coilover-kit-bmw-3-series-e90',
        'vendor': 'KW Suspensions',
        'product_type': 'Coilovers',
        'created_at': '2023-01-15T10:30:00Z',
        'updated_at': '2023-10-15T14:20:00Z',
        'published_at': '2023-01-16T09:00:00Z',
        'tags': ['BMW', 'E90', 'Coilover', 'KW V1'],
        'variants': [
            {
                'id': 987654321,
                'price': '1299.99',
                'compare_at_price': '1499.99',
                'sku': 'KW-V1-E90-001',
                'inventory_quantity': 5,
                'available': True
            }
        ],
        'images': [
            {
                'id': 111111,
                'src': 'https://cdn.shopify.com/s/files/1/0000/0000/products/kw-v1-e90.jpg'
            },
            {
                'id': 222222,
                'src': 'https://cdn.shopify.com/s/files/1/0000/0000/products/kw-v1-e90-2.jpg'
            }
        ],
        'body_html': '<p>High-quality KW V1 Coilover suspension kit for BMW E90...</p>'
    }
    
    parser = KWParser()
    extracted = parser.extract_product_data(mock_product)
    
    # Verify extracted data
    assert extracted['id'] == 12345678
    assert extracted['title'] == 'KW V1 Coilover Kit - BMW 3 Series E90'
    assert extracted['handle'] == 'kw-v1-coilover-kit-bmw-3-series-e90'
    assert extracted['vendor'] == 'KW Suspensions'
    assert extracted['product_type'] == 'Coilovers'
    assert extracted['price'] == '1299.99'
    assert extracted['sku'] == 'KW-V1-E90-001'
    assert extracted['inventory_quantity'] == 5
    assert extracted['available'] == True
    assert extracted['variant_count'] == 1
    assert extracted['image_count'] == 2
    assert 'kw-v1-e90' in extracted['image_url']
    assert 'BMW' in extracted['tags']
    
    print("✓ Test extract_product_data passed")


def test_save_to_csv():
    """Test CSV export functionality"""
    
    # Mock products
    mock_products = [
        {
            'id': 12345678,
            'title': 'KW V1 Coilover Kit - BMW 3 Series E90',
            'handle': 'kw-v1-coilover-kit-bmw-3-series-e90',
            'vendor': 'KW Suspensions',
            'product_type': 'Coilovers',
            'created_at': '2023-01-15T10:30:00Z',
            'updated_at': '2023-10-15T14:20:00Z',
            'published_at': '2023-01-16T09:00:00Z',
            'tags': ['BMW', 'E90', 'Coilover'],
            'variants': [
                {
                    'price': '1299.99',
                    'sku': 'KW-V1-E90-001',
                    'inventory_quantity': 5,
                    'available': True
                }
            ],
            'images': [
                {'src': 'https://example.com/image1.jpg'}
            ],
            'body_html': '<p>Description</p>'
        },
        {
            'id': 87654321,
            'title': 'KW V2 Coilover Kit - Audi A4 B8',
            'handle': 'kw-v2-coilover-kit-audi-a4-b8',
            'vendor': 'KW Suspensions',
            'product_type': 'Coilovers',
            'created_at': '2023-02-10T11:00:00Z',
            'updated_at': '2023-10-16T15:30:00Z',
            'published_at': '2023-02-11T10:00:00Z',
            'tags': ['Audi', 'A4', 'B8', 'Coilover'],
            'variants': [
                {
                    'price': '1599.99',
                    'sku': 'KW-V2-B8-001',
                    'inventory_quantity': 3,
                    'available': True
                }
            ],
            'images': [
                {'src': 'https://example.com/image2.jpg'}
            ],
            'body_html': '<p>Premium suspension kit</p>'
        }
    ]
    
    parser = KWParser()
    output_file = '/tmp/test_kw_products.csv'
    result = parser.save_to_csv(mock_products, output_file)
    
    # Verify file was created
    assert os.path.exists(output_file)
    
    # Read and verify CSV content
    import csv
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['title'] == 'KW V1 Coilover Kit - BMW 3 Series E90'
        assert rows[0]['price'] == '1299.99'
        assert rows[1]['title'] == 'KW V2 Coilover Kit - Audi A4 B8'
        assert rows[1]['price'] == '1599.99'
    
    # Cleanup
    os.remove(output_file)
    
    print("✓ Test save_to_csv passed")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Running KW Parser Tests")
    print("=" * 60)
    
    try:
        test_extract_product_data()
        test_save_to_csv()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
