import os
from app import parse_excel_enquiry

excel_file = "RFQ-LIGHT FIXTURES-KOSMO ONE 12TH FLOOR-CHENNAI.xlsx"
if os.path.exists(excel_file):
    print("Excel file found! Starting extraction...")
    result_text = parse_excel_enquiry(excel_file)
    print(f"Extraction complete! Extracted character count: {len(result_text)}")
    
    # Save the output
    out_path = "scratch/extracted_test_excel.txt"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result_text)
    print(f"Saved results to {out_path}")
    
    # Print the first 1000 characters
    print("\n--- Preview (First 1000 chars) ---")
    print(result_text[:1000])
else:
    print(f"Error: {excel_file} not found.")
