"""
Additional utilities for the quotation automation system.
"""
import csv
from pathlib import Path


def convert_to_csv(price_list_dict, output_path):
    """
    Convert a dictionary-based price list to CSV format.
    
    Usage:
        data = {
            "products": [
                {"name": "Product 1", "price": 100, "unit": "pcs"},
                {"name": "Product 2", "price": 50, "unit": "m"}
            ]
        }
        convert_to_csv(data, "catalog.csv")
    """
    products = price_list_dict.get("products", [])
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['product_id', 'product_name', 'latest_price', 'unit', 'description'])
        writer.writeheader()
        
        for idx, product in enumerate(products, start=1):
            writer.writerow({
                'product_id': f"P{idx:03d}",
                'product_name': product.get('name', ''),
                'latest_price': product.get('price', 0),
                'unit': product.get('unit', 'pcs'),
                'description': product.get('description', '')
            })
    
    print(f"✓ Created catalog: {output_path}")


def validate_catalog_file(filepath):
    """Validate that a catalog file has the required structure."""
    path = Path(filepath)
    
    if not path.exists():
        return False, "File does not exist"
    
    if path.suffix.lower() == '.csv':
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                required = {'product_id', 'product_name', 'latest_price', 'unit'}
                headers = set(reader.fieldnames) if reader.fieldnames else set()
                
                if not required.issubset(headers):
                    return False, f"Missing columns: {required - headers}"
                
                rows = list(reader)
                if not rows:
                    return False, "Catalog is empty"
                
                return True, f"Valid catalog with {len(rows)} products"
        except Exception as e:
            return False, str(e)
    
    return False, "Only CSV and JSON files are supported"


def merge_catalogs(catalog1_path, catalog2_path, output_path):
    """Merge two catalog files into one."""
    all_rows = []
    max_id = 0
    
    # Read first catalog
    with open(catalog1_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            all_rows.append(row)
            try:
                pid = int(row['product_id'].replace('P', ''))
                max_id = max(max_id, pid)
            except:
                pass
    
    # Read second catalog and renumber
    with open(catalog2_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            max_id += 1
            row['product_id'] = f"P{max_id:03d}"
            all_rows.append(row)
    
    # Write merged
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['product_id', 'product_name', 'latest_price', 'unit', 'description'])
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"✓ Merged {len(all_rows)} products to: {output_path}")


if __name__ == '__main__':
    # Example usage
    print("Quotation Automation Utilities")
    print("Import this module to use helper functions:")
    print("  - convert_to_csv()")
    print("  - validate_catalog_file()")
    print("  - merge_catalogs()")
