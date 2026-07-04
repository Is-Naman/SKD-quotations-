#!/usr/bin/env python3
"""
Verification test script for the improved quotation matching engine.
Tests the user's real enquiry and the sample enquiry against the clean catalog.
"""
import sys
import os

# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from quotation_automation import (
    load_catalog,
    parse_enquiry_with_fallback,
    build_quote_rows,
    normalize_enquiry_input,
)

# Use the clean catalog
CATALOG_PATH = os.path.join(os.path.dirname(__file__), "catalogs", "master_product_catalog_clean.csv")

USER_ENQUIRY = """Matera
Material Description
Unit
Quantity
Contactor
CONTACTOR MO C15 WITH MO-SA1L MAKE:-L&T 240VOLTS 50HZ
NOS
2
Fuse Link - HRC 4A
GE (General Electric) 4A HRC Fuse Link V230
NOS
10
Air Blower
Hand Blower for Cleaning GBL650- Make Bosch
NOS
4
SMPS 24V, 10A for PLC
SMPS 24V, 10A for PLC
NOS
6
Junction Boxes 25mm  3-way / 4-way
PVC JUNCTION BOX MAKE SUDHAKER
NOS
30
LED Wall Light
40WATTS WALL LIGHT 40X 4 FEETS MAKE HAVELS
NOS
40
Over Lode Relay 3UA 55 16-25Amps
Make: Siemens
NOS
4
Over Load Relay 3UA 50 6.3-10Amps
Make: Siemens
NOS
4
Over Load Relay MK1-6-10Amps
Make: Siemens
NOS
4
MCB 32A 3 Pole
Make: LEGRAND
NOS
6
MCB 63A 4 Pole
Make: LEGRAND
NOS
6
MCB 3 Pole 16 Amps
Make: LEGRAND
NOS
6"""

SAMPLE_ENQUIRY = """We are looking for electrical supplies for our new office renovation project.

We need:
- 50 meters of Polycab 4 sqmm PVC Insulated Wire for main wiring
- 20 pcs of Schneider 16A Socket Outlet for wall installations
- 100 pcs of Anchor Roma 10A MCB for the distribution board

Please quote with current pricing. We need delivery within 2 weeks.
"""


def print_divider(title=""):
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)


def test_enquiry(name, enquiry_text, catalog, expected_matches=None):
    """Test an enquiry and print detailed results."""
    print_divider(f"TEST: {name}")

    # Step 1: Show normalized segments
    print("\n--- Normalized Segments ---")
    segments = normalize_enquiry_input(enquiry_text)
    for i, seg in enumerate(segments):
        print(f"  [{i+1}] {seg}")

    # Step 2: Parse and match
    print("\n--- Parsed Items ---")
    parsed = parse_enquiry_with_fallback(enquiry_text, catalog)
    for i, item in enumerate(parsed):
        print(f"  [{i+1}] Product: {item['product_name']}")
        print(f"       Quantity: {item['quantity']}")
        print(f"       Requirement: {item.get('requirement', '')[:80]}")

    # Step 3: Build quote rows
    print("\n--- Quote Rows ---")
    rows = build_quote_rows(parsed, catalog)
    matched_count = 0
    unmatched_count = 0
    for i, row in enumerate(rows):
        is_matched = row["note"] == "matched" or "Compare option" in row["note"]
        status = "[OK] MATCHED" if is_matched else "[!!] NOT FOUND"
        if is_matched:
            matched_count += 1
        else:
            unmatched_count += 1
        print(f"  [{i+1}] {status} ({row['note']})")
        print(f"       Product:  {row['product_name']}")
        print(f"       ID:       {row['product_id']}")
        print(f"       Qty:      {row['requested_quantity']} {row['unit']}")
        print(f"       Price:    ₹{row['unit_price']:.2f} each")
        print(f"       Total:    ₹{row['total_price']:.2f}")
        if row.get("requirement"):
            print(f"       Req:      {row['requirement'][:80]}")

    print(f"\n--- Summary: {matched_count} matched, {unmatched_count} not found ---")

    # Step 4: Check expected matches
    if expected_matches:
        print("\n--- Expected Match Verification ---")
        for expected_name, expected_id in expected_matches.items():
            found = False
            for row in rows:
                if row["product_id"] == expected_id:
                    found = True
                    print(f"  [OK] {expected_name} -> {expected_id} ({row['product_name']})")
                    break
            if not found:
                print(f"  [!!] MISSING: {expected_name} -> expected {expected_id}")

    return rows


def main():
    print("Loading catalog from:", CATALOG_PATH)
    catalog = load_catalog(CATALOG_PATH)
    print(f"Catalog loaded: {len(catalog)} products\n")

    # Test 1: User's real enquiry
    user_expected = {
        "L&T Contactor MO C15": "LT005",
        "Siemens Overload Relay 3UA55 16-25A": "SIM007",
        "Siemens Overload Relay 3UA50 6.3-10A": "SIM008",
        "Siemens Overload Relay MK1 6-10A": "SIM009",
        "Legrand 3 Pole MCB 32A": "LEGR003",
        "Legrand 4 Pole MCB 63A": "LEGR008",
        "Legrand 3 Pole MCB 16A": "LEGR007",
        "Sudhakar PVC Junction Box 25mm": "SUK007",
    }
    test_enquiry("User's Real Enquiry (Block Table Format)", USER_ENQUIRY, catalog, user_expected)

    # Test 2: Sample enquiry
    sample_expected = {
        "Polycab 4 sqmm Copper Wire": "PC003",
        "Schneider 16A Socket Outlet": "SH003",
        "Anchor Roma MCB 10A": "AR005",
    }
    test_enquiry("Sample Enquiry (Bullet List Format)", SAMPLE_ENQUIRY, catalog, sample_expected)

    # Test 3: Multi-brand comparison (Enquiry without brand)
    generic_enquiry = "Please quote for 10 pcs of MCB 16A 3 Pole"
    test_enquiry("Generic Enquiry (Multi-brand Comparison)", generic_enquiry, catalog)

    print_divider("ALL TESTS COMPLETE")


if __name__ == "__main__":
    main()
