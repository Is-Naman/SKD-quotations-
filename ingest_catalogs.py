#!/usr/bin/env python3
"""
Smart catalog ingestion: Extract products from uploaded PDFs using
pdfplumber's table extraction, with improved filtering and brand-aware naming.
"""
import csv
import json
import os
import re
import sys
from pathlib import Path

# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed")
    sys.exit(1)

ROOT = Path(r'c:\Users\Asus\Documents\LP of SKD')
UPLOAD_DIR = ROOT / 'uploads'
OUT_PATH = ROOT / 'catalogs' / 'master_product_catalog_clean.csv'

# ---------------------------------------------------------------------------
# Brand detection from filename
# ---------------------------------------------------------------------------
FILENAME_BRAND_MAP = {
    "a1 legrand": "A1 Legrand",
    "legrand": "Legrand",
    "densons": "DENSONS",
    "dowell": "DOWELL",
    "gland": "GLAND",
    "gold medal": "GOLD Medal",
    "h - seal": "H-SEAL",
    "h-seal": "H-SEAL",
    "hdc": "HDC Net",
    "industrial socket ruchi": "Industrial Socket Ruchi",
    "l&t": "L&T",
    "ldc": "LDC",
    "pcc": "Polycab",
    "polycab": "Polycab",
    "schneider": "Schneider",
    "siemens": "Siemens",
    "sudhakar": "Sudhakar",
    "wipro": "Wipro",
    "anchor": "Anchor Roma",
    "relay rates schneider": "Schneider",
}

def detect_brand_from_filename(filename):
    fname_lower = filename.lower()
    # Sort by length desc to match "a1 legrand" before "legrand"
    for key in sorted(FILENAME_BRAND_MAP, key=len, reverse=True):
        if key in fname_lower:
            return FILENAME_BRAND_MAP[key]
    return None


# ---------------------------------------------------------------------------
# Table-based extraction (much better than line regex for structured PDFs)
# ---------------------------------------------------------------------------
def extract_products_from_tables(pdf_path, brand):
    """Extract products from PDF tables using pdfplumber.extract_tables()."""
    products = []
    seen = set()
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            # Try table extraction first
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 2:
                    continue
                products_from_table = parse_product_table(table, brand, page_num)
                for p in products_from_table:
                    key = p["product_name"].lower().strip()
                    if key not in seen and len(key) >= 5:
                        seen.add(key)
                        products.append(p)
            
            # Also try text-based extraction for pages without tables
            text = page.extract_text() or ""
            if text.strip():
                text_products = parse_text_products(text, brand, page_num)
                for p in text_products:
                    key = p["product_name"].lower().strip()
                    if key not in seen and len(key) >= 5:
                        seen.add(key)
                        products.append(p)
    
    return products


def is_header_row(row):
    """Check if a table row looks like a header."""
    header_kws = {"s.no", "s. no", "sr.no", "sr. no", "sl.no", "sl. no",
                  "size", "cat.no", "cat no", "catalogue", "rate", "price",
                  "description", "product", "item", "particular", "unit",
                  "hsn", "code", "ref", "range", "model", "type"}
    row_text = " ".join(str(c).lower().strip() for c in row if c)
    matches = sum(1 for kw in header_kws if kw in row_text)
    return matches >= 2


def parse_product_table(table, brand, page_num):
    """Parse a table from pdfplumber into product entries."""
    products = []
    
    if not table or len(table) < 2:
        return products
    
    # Try to identify columns: look for a price column and a name/description column
    header_row = table[0] if table else []
    
    # Find column indices
    price_col = None
    name_col = None
    size_col = None
    cat_col = None
    
    for i, cell in enumerate(header_row):
        cell_str = str(cell).lower().strip() if cell else ""
        if any(kw in cell_str for kw in ["rate", "price", "mrp", "lp", "list price", "net price"]):
            price_col = i
        if any(kw in cell_str for kw in ["description", "particular", "product", "item", "material"]):
            name_col = i
        if any(kw in cell_str for kw in ["size", "range", "type", "specification"]):
            size_col = i
        if any(kw in cell_str for kw in ["cat", "code", "ref", "part"]):
            cat_col = i
    
    # Process data rows
    for row_idx, row in enumerate(table):
        if row_idx == 0 and is_header_row(row):
            continue
        if is_header_row(row):
            continue
        
        # Skip empty rows
        non_empty = [c for c in row if c and str(c).strip()]
        if len(non_empty) < 2:
            continue
        
        # Try to extract price
        price = None
        price_source_col = None
        
        if price_col is not None and price_col < len(row) and row[price_col]:
            price = try_parse_price(str(row[price_col]))
            if price:
                price_source_col = price_col
        
        # If no designated price column, look for prices in any column
        if price is None:
            for i, cell in enumerate(row):
                if cell and i != name_col:
                    p = try_parse_price(str(cell))
                    if p and p > 1 and p < 500000:
                        price = p
                        price_source_col = i
                        break
        
        if price is None or price <= 0 or price > 500000:
            continue
        
        # Extract product name/description
        name_parts = []
        for i, cell in enumerate(row):
            if cell and i != price_source_col:
                cell_str = str(cell).strip()
                # Skip pure numbers, serial numbers, empty cells
                if not cell_str or re.fullmatch(r"\d+", cell_str):
                    continue
                if re.fullmatch(r"[\d\.\,\s₹]+", cell_str):
                    continue
                # Skip cells that are just prices
                if try_parse_price(cell_str) and i != name_col and i != size_col:
                    continue
                name_parts.append(cell_str)
        
        if not name_parts:
            continue
        
        product_name = " ".join(name_parts).strip()
        product_name = clean_product_name(product_name, brand)
        
        if not product_name or len(product_name) < 5:
            continue
        
        # Determine unit
        unit = "pcs"
        name_lower = product_name.lower()
        if any(kw in name_lower for kw in ["wire", "cable", "pipe", "conduit", "busbar", "tray"]):
            unit = "m"
        if any(kw in name_lower for kw in ["/m", "per m", "per meter", "per mtr"]):
            unit = "m"
        
        products.append({
            "product_name": product_name,
            "latest_price": price,
            "unit": unit,
            "description": f"From {brand} catalog" if brand else "Imported from uploaded catalog",
        })
    
    return products


def parse_text_products(text, brand, page_num):
    """Extract products from plain text (fallback when tables aren't detected)."""
    products = []
    
    # Skip pages that are mostly index/about/contact
    text_lower = text.lower()
    skip_kws = ["index", "about dowell", "product category", "terms and condition",
                 "bank details", "contact us", "manufactured by", "client list",
                 "symbol of quality", "disclaimer"]
    if any(kw in text_lower for kw in skip_kws):
        return products
    
    price_re = re.compile(
        r"(?P<name>.{8,80}?)\s+(?:₹\s*)?(?P<price>\d{1,3}(?:[,]\d{3})*(?:\.\d{1,2})?)\s*$"
    )
    
    for line in text.splitlines():
        line = line.strip()
        if not line or len(line) < 10:
            continue
        
        m = price_re.match(line)
        if not m:
            continue
        
        name = m.group("name").strip()
        price_str = m.group("price").replace(",", "")
        
        try:
            price = float(price_str)
        except ValueError:
            continue
        
        if price <= 1 or price > 500000:
            continue
        
        name = clean_product_name(name, brand)
        if not name or len(name) < 5:
            continue
        
        # Must have at least one meaningful word
        words = [w for w in re.split(r"\W+", name) if w.isalpha() and len(w) >= 3]
        if not words:
            continue
        
        unit = "pcs"
        if any(kw in name.lower() for kw in ["wire", "cable", "pipe", "conduit"]):
            unit = "m"
        
        products.append({
            "product_name": name,
            "latest_price": price,
            "unit": unit,
            "description": f"From {brand} catalog" if brand else "Imported from uploaded catalog",
        })
    
    return products


def try_parse_price(text):
    """Try to parse a price value from text."""
    if not text:
        return None
    cleaned = text.strip()
    # Remove currency symbols
    cleaned = re.sub(r"[₹$]", "", cleaned).strip()
    cleaned = re.sub(r"^Rs\.?\s*", "", cleaned, flags=re.I).strip()
    cleaned = re.sub(r"^INR\s*", "", cleaned, flags=re.I).strip()
    # Remove trailing units
    cleaned = re.sub(r"\s*(per\s+)?(pc|pcs|unit|m|mtr|meter|set|kg|no|nos|ea|each)\s*$", "", cleaned, flags=re.I).strip()
    # Handle Indian number format: 1,23,456.78 or 1,234.56
    cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def clean_product_name(name, brand):
    """Clean up extracted product name."""
    if not name:
        return ""
    
    # Remove serial numbers at start
    name = re.sub(r"^\d+\s*[\.\)]\s*", "", name).strip()
    # Remove cat.no / ref patterns
    name = re.sub(r"\b(?:cat\.?\s*no|ref|hsn|sno|s\.no|sl\.?\s*no)\b.*$", "", name, flags=re.I).strip()
    # Remove trailing prices/numbers that got concatenated
    name = re.sub(r"\s+\d{4,}$", "", name).strip()
    # Remove marketing text indicators
    name = re.sub(r"\b(new|latest|revised|effective|valid|w\.e\.f|wef)\b.*$", "", name, flags=re.I).strip()
    
    # Clean up whitespace
    name = re.sub(r"\s+", " ", name).strip()
    name = name.strip(" .,-|/:")
    
    # Skip if it's a garbage entry
    garbage_patterns = [
        r"^(page|total|subtotal|gst|tax|note|disclaimer|terms)",
        r"^(index|section|chapter|about|contact|address)",
        r"^(bank|account|ifsc|branch|tin|gstin|pan)",
        r"^(email|phone|fax|mobile|web|www|http)",
        r"^(price\s*list|pricelist|catalogue|catalog|list\s*price)",
        r"^(manufactured|maker|designer|house of)",
        r"^(connecting|trust|quality|client)",
    ]
    for pat in garbage_patterns:
        if re.match(pat, name.lower()):
            return ""
    
    # Don't add brand prefix if it's already there
    if brand and not name.lower().startswith(brand.lower()):
        # Only prefix with brand if the name looks like it needs it
        # (short descriptive names like "MCB 16A" or "Cable 4 sqmm")
        has_brand = any(b.lower() in name.lower() for b in FILENAME_BRAND_MAP.values())
        if not has_brand and len(name) < 60:
            name = f"{brand} {name}"
    
    return name


# ---------------------------------------------------------------------------
# Main ingestion
# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("  Smart Catalog Ingestion from Uploaded PDFs")
    print("=" * 70)
    
    # Load existing clean catalog
    existing = []
    existing_names = set()
    if OUT_PATH.exists():
        with OUT_PATH.open('r', encoding='utf-8', newline='') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                existing.append(row)
                existing_names.add(re.sub(r'\s+', ' ', row['product_name'].strip().lower()))
    
    print(f"Existing catalog: {len(existing)} products")
    print()
    
    new_rows = []
    stats = []
    
    for path in sorted(UPLOAD_DIR.iterdir()):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        
        if ext == '.pdf':
            brand = detect_brand_from_filename(path.name)
            print(f"Processing: {path.name}")
            print(f"  Brand: {brand or 'Unknown'}")
            
            try:
                products = extract_products_from_tables(str(path), brand)
                added = 0
                for item in products:
                    name_key = re.sub(r'\s+', ' ', item['product_name'].strip().lower())
                    if name_key in existing_names:
                        continue
                    existing_names.add(name_key)
                    new_rows.append({
                        'product_id': f'UP{len(existing)+len(new_rows)+1:04d}',
                        'product_name': item['product_name'],
                        'latest_price': item['latest_price'],
                        'unit': item['unit'],
                        'description': item['description'],
                    })
                    added += 1
                stats.append((path.name, len(products), added, None))
                print(f"  Extracted: {len(products)}, New: {added}")
            except Exception as exc:
                stats.append((path.name, 0, 0, str(exc)))
                print(f"  ERROR: {exc}")
        
        elif ext in {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}:
            print(f"Skipping image (no Tesseract OCR): {path.name}")
            stats.append((path.name, 0, 0, "Tesseract OCR not installed"))
        
        print()
    
    # Write merged catalog
    all_rows_data = existing + new_rows
    with OUT_PATH.open('w', encoding='utf-8', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=['product_id','product_name','latest_price','unit','description'])
        writer.writeheader()
        writer.writerows(all_rows_data)
    
    print("=" * 70)
    print(f"  SUMMARY")
    print("=" * 70)
    print(f"  Existing rows:        {len(existing)}")
    print(f"  New rows added:       {len(new_rows)}")
    print(f"  Total catalog size:   {len(all_rows_data)}")
    print(f"  Output: {OUT_PATH}")
    print()
    
    for name, extracted, added, error in stats:
        status = f"extracted={extracted}, added={added}" if not error else f"ERROR: {error}"
        print(f"  {name}: {status}")


if __name__ == '__main__':
    main()
