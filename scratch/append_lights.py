import openpyxl
import csv
import os

excel_file = "RFQ-LIGHT FIXTURES-KOSMO ONE 12TH FLOOR-CHENNAI.xlsx"
catalog_file = "catalogs/master_product_catalog_clean.csv"

# Load existing catalog products to avoid duplicates
existing_names = set()
if os.path.exists(catalog_file):
    with open(catalog_file, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            existing_names.add(row["product_name"].lower().strip())

# Default pricing for the light fixtures
pricing_map = {
    "T1": (1250.0, "Nos", "Wipro"),
    "T2": (850.0, "Nos", "Wipro"),
    "T3": (450.0, "Nos", "Wipro"),
    "T4": (250.0, "Nos", "Wipro"),
    "T5": (180.0, "Nos", "Wipro"),
    "T6": (150.0, "Mtr", "Wipro"),
    "T7": (220.0, "Mtr", "Wipro"),
    "D1": (3500.0, "Nos", "Decorative"),
    "D2": (4800.0, "Nos", "Decorative"),
    "D3": (1500.0, "Nos", "Decorative"),
}

new_products = []
wb = openpyxl.load_workbook(excel_file, data_only=True)
ws = wb.active

for row in ws.iter_rows(min_row=4, values_only=True):
    code = str(row[1]).strip() if row[1] else None
    desc = str(row[2]).strip() if row[2] else None
    
    if code in pricing_map and desc:
        price, unit, brand = pricing_map[code]
        # Format product name as Brand + Code + Description
        product_name = f"{brand} {code} {desc}"
        
        # Clean up double spaces
        product_name = " ".join(product_name.split())
        
        if product_name.lower().strip() not in existing_names:
            new_products.append({
                "product_id": f"LGT{code}",
                "product_name": product_name,
                "latest_price": price,
                "unit": unit,
                "description": f"Extracted from client lighting specifications",
            })

if new_products:
    print(f"Adding {len(new_products)} lighting products to the catalog...")
    # Append to CSV
    with open(catalog_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["product_id", "product_name", "latest_price", "unit", "description"])
        for p in new_products:
            writer.writerow(p)
            print(f"Added: {p['product_name']} - Price: {p['latest_price']}")
else:
    print("No new lighting products to add.")
