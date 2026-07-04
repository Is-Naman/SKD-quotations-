#!/usr/bin/env python3
import argparse
import csv
import difflib
import json
import os
import re
import shutil
import sys
import urllib.request
import urllib.error
from datetime import datetime

try:
    import pdfplumber
except ImportError:  # pragma: no cover
    pdfplumber = None

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

try:
    import pytesseract
except ImportError:  # pragma: no cover
    pytesseract = None


CSV_HEADERS = [
    "product_id",
    "product_name",
    "latest_price",
    "unit",
    "description",
]

QUOTE_HEADERS = [
    "product_id",
    "product_name",
    "requirement",
    "requested_quantity",
    "unit",
    "unit_price",
    "discount",
    "total_price",
    "note",
]

UNITS_RE = r"pcs|pieces?|pc|units?|qty|qtys|quantity|nos?|no\.?|numbers?|mtrs?|meters?|metres?|m|bundles?|pkts?|packets?|coils?|boxes?"
QUANTITY_PATTERN = re.compile(rf"(\d+)\s*(?:{UNITS_RE})\b", re.IGNORECASE)
CATALOG_PRICE_LINE_RE = re.compile(r"(?P<name>.+?)\s+(?:₹|Rs\.?|INR\s*)?(?P<price>\d{1,3}(?:[.,]\d{3})*(?:\.[0-9]+)?)\b", re.IGNORECASE)
CATALOG_IGNORE_RE = re.compile(r"\b(index|page|total|subtotal|gst|rate list|price list|catalogue|catalog|terms|condition|serial|s\.no|tin|email|www\.|http|fax|phone|invoice|bank|account|effective|valid till|revision|symbol of quality|pricelist|list|section|about|contact|address|manufactured by|product category|download)\b", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Known brands in the electrical supply domain
# ---------------------------------------------------------------------------
KNOWN_BRANDS = [
    "a1 legrand", "legrand", "anchor roma", "anchor", "schneider",
    "siemens", "polycab", "havells", "havels", "l&t", "l & t",
    "wipro", "gold medal", "dowell", "densons", "sudhakar", "sudhaker",
    "hdc net", "hdc", "h-seal", "gland", "bosch", "ge", "general electric",
    "crompton", "finolex", "rr kabel", "ldc", "pcc", "ruchi",
]

# Spec patterns: captures electrical/physical specifications
SPEC_PATTERN = re.compile(
    r"""
    (\d+(?:\.\d+)?)\s*                      # numeric value
    (sqmm|sq\.?\s*mm|amps?|kvar|kw|watts?|  # unit
     volts?|hz|mm|pole|core|phase|way|       # more units
     mA|a|w|v|p|feets?|ft)                   # short units
    """,
    re.IGNORECASE | re.VERBOSE
)

# Ampere rating pattern (matches "16A", "32A", "63A", "6.3-10A", "16-25A")
AMP_PATTERN = re.compile(r"(\d+(?:\.\d+)?(?:\s*[-–]\s*\d+(?:\.\d+)?)?)\s*(?:amps?|a)\b", re.IGNORECASE)

# Pole pattern (matches "3 Pole", "Single Pole", "4 Pole", "3P", "4P")
POLE_PATTERN = re.compile(r"(\d)\s*(?:pole|p)\b|(?:(single|double|triple|four))\s*pole", re.IGNORECASE)

# Product type keywords for classification
PRODUCT_TYPE_KEYWORDS = {
    "mcb": ["mcb", "miniature circuit breaker"],
    "mccb": ["mccb", "molded case", "moulded case"],
    "rccb": ["rccb", "residual current"],
    "rcbo": ["rcbo"],
    "contactor": ["contactor"],
    "relay": ["relay", "overload relay", "over load relay", "over lode relay", "thermal overload"],
    "switch": ["switch", "modular switch"],
    "socket": ["socket", "socket outlet"],
    "wire": ["wire", "cable", "conductor"],
    "conduit": ["conduit"],
    "pipe": ["pipe"],
    "gland": ["gland", "cable gland"],
    "lug": ["lug", "terminal lug", "lugs"],
    "led": ["led", "bulb", "light", "wall light", "tube light"],
    "junction_box": ["junction box", "junction boxes", "jb"],
    "capacitor": ["capacitor", "kvar"],
    "smps": ["smps", "power supply"],
    "fuse": ["fuse", "fuse link", "hrc"],
    "blower": ["blower", "air blower", "hand blower"],
    "cable_tray": ["cable tray"],
    "busbar": ["busbar", "bus bar", "bus duct"],
    "earthing": ["earthing", "earth pit", "grounding"],
    "isolation_switch": ["isolation switch", "isolator"],
    "vfd": ["vfd", "variable frequency drive", "drive", "inverter"],
    "enclosure": ["enclosure", "panel enclosure", "panel board", "db box", "distribution board", "metal enclosure", "electrical panel"],
}


def safe_float(value, default=0.0):
    try:
        return float(str(value).strip())
    except Exception:
        return default


def extract_text_from_pdf_file(path):
    if pdfplumber is None:
        raise RuntimeError("pdfplumber is not installed")

    text_chunks = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_chunks.append(page_text)
    return "\n".join(text_chunks)


def extract_text_from_image_file(path):
    if Image is None:
        raise RuntimeError("Pillow is not installed")
    if pytesseract is None or not shutil.which("tesseract"):
        raise RuntimeError("OCR is unavailable because Tesseract is not installed")

    with Image.open(path) as img:
        return pytesseract.image_to_string(img)


def parse_catalog_text(text):
    """Extract product rows from raw catalog text.

    Improved filtering to reject garbage entries (table headers, page numbers,
    reference codes, marketing copy) that were previously polluting the catalog.
    """
    rows = []
    seen = set()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or len(line) < 4:
            continue
        if CATALOG_IGNORE_RE.search(line.lower()):
            continue
        if re.fullmatch(r"[\d\W]+", line):
            continue

        match = CATALOG_PRICE_LINE_RE.search(line)
        if not match:
            continue

        product_name = match.group("name").strip(" .,-|/:")
        product_name = re.sub(r"\b(?:cat\.?no|cat no|code|s\.no|sno|sl\.?no|part|ref)\b.*$", "", product_name, flags=re.IGNORECASE)
        product_name = re.sub(r"^\d+\s*", "", product_name).strip(" .,-|/:")

        # --- IMPROVED FILTERING ---
        # Reject names shorter than 8 characters (catches "Size", "32A", "Pole", etc.)
        if not product_name or len(product_name) < 8:
            continue

        # Must contain at least one alphabetic word of 3+ characters
        alpha_words = [w for w in re.split(r"\W+", product_name) if w.isalpha() and len(w) >= 3]
        if not alpha_words:
            continue

        # Reject entries that are purely reference codes / catalog numbers
        if re.fullmatch(r"[A-Z0-9\s\-\.]+", product_name) and not any(c.islower() for c in product_name):
            alpha_count = sum(1 for c in product_name if c.isalpha())
            digit_count = sum(1 for c in product_name if c.isdigit())
            if digit_count > alpha_count:
                continue

        price_text = match.group("price").replace(",", "")
        try:
            latest_price = float(price_text)
        except ValueError:
            continue

        # Reject unreasonable prices
        if latest_price <= 0 or latest_price > 500000:
            continue
        # Reject prices that look like page numbers (single digit prices for non-accessory items)
        if latest_price < 2.0 and len(product_name) < 20:
            continue

        key = product_name.lower()
        if key in seen:
            continue
        seen.add(key)

        unit = "pcs"
        if re.search(r"\b(?:m|meter|metre|mts|mtrs)\b", product_name.lower()):
            unit = "m"

        rows.append({
            "product_name": product_name,
            "latest_price": latest_price,
            "unit": unit,
            "description": "Imported from uploaded catalog",
        })

    return rows


def parse_catalog_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        text = extract_text_from_pdf_file(path)
    elif ext in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}:
        text = extract_text_from_image_file(path)
    else:
        raise ValueError(f"Unsupported catalog file type: {ext}")

    rows = parse_catalog_text(text)
    if not rows:
        raise ValueError("No product lines could be extracted from the uploaded catalog")

    return rows


def load_catalog(path):
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for filename in files:
                if filename.lower().endswith(".csv"):
                    return load_catalog(os.path.join(root, filename))
        raise FileNotFoundError(f"No CSV catalog found under directory: {path}")

    if path.lower().endswith(".csv"):
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = []
            for raw in reader:
                rows.append({
                    "product_id": raw.get("product_id", "").strip(),
                    "product_name": raw.get("product_name", "").strip(),
                    "latest_price": safe_float(raw.get("latest_price", "")),
                    "unit": raw.get("unit", "").strip(),
                    "description": raw.get("description", "").strip(),
                })
            return rows

    if path.lower().endswith(".json"):
        with open(path, encoding="utf-8") as fh:
            catalog = json.load(fh)
            return [
                {
                    "product_id": str(row.get("product_id", "")).strip(),
                    "product_name": str(row.get("product_name", "")).strip(),
                    "latest_price": safe_float(row.get("latest_price", "")),
                    "unit": str(row.get("unit", "")).strip(),
                    "description": str(row.get("description", "")).strip(),
                }
                for row in catalog
            ]

    raise ValueError(f"Unsupported catalog format: {path}. Use CSV or JSON.")


def format_prompt(enquiry):
    return (
        "You are a quotation assistant. Extract product names, requested quantities, "
        "and requirement details from the enquiry text. Return only valid JSON in the following schema:\n"
        "{\"items\": [{\"product_name\": \"...\", \"quantity\": 10, \"requirement\": \"...\"}]}\n\n"
        "If the enquiry does not mention quantity, return quantity = 1. \n\n"
        "Enquiry text:\n" + enquiry.strip()
    )


def extract_text_from_response(resp_json):
    if not isinstance(resp_json, dict):
        return None

    if "output" in resp_json:
        output = resp_json["output"]
        if isinstance(output, list) and output:
            first = output[0]
            if isinstance(first, dict):
                if "content" in first and isinstance(first["content"], list):
                    texts = [item.get("text") for item in first["content"] if isinstance(item, dict) and "text" in item]
                    if texts:
                        return "\n".join(texts)
                if "text" in first:
                    return first["text"]
    if "choices" in resp_json:
        choices = resp_json["choices"]
        if isinstance(choices, list) and choices:
            text = choices[0].get("text") or choices[0].get("message", {}).get("content")
            return text
    return None


def call_gemini_api(enquiry):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("Missing GEMINI_API_KEY environment variable.")

    url = os.environ.get("GEMINI_API_URL", "https://api.openai.com/v1/responses")
    model = os.environ.get("GEMINI_MODEL", "gemini-pro")
    prompt = format_prompt(enquiry)
    payload = {"model": model, "input": prompt}
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request) as response:
            response_data = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f"Gemini API request failed: {error.code} {error.reason} {error.read().decode('utf-8', errors='ignore')}"
        )

    raw_text = extract_text_from_response(response_data)
    if not raw_text:
        raise RuntimeError("Could not extract text from Gemini API response.")

    try:
        parsed = json.loads(raw_text)
        return parsed.get("items", []) if isinstance(parsed, dict) else []
    except json.JSONDecodeError:
        raise ValueError("Gemini API returned text that was not valid JSON.\n" + raw_text)


def find_quantity(enquiry, product_name=None):
    # Prioritize quantity at the very end of the line (e.g. "- 13 Nos" or " - 500 Mtrs")
    # This prevents matching specification numbers (like "2No" or "12no's") inside parentheses earlier in the description.
    end_match = re.search(rf"\b(\d+)\s*(?:{UNITS_RE})\s*$", enquiry, re.IGNORECASE)
    if end_match:
        return int(end_match.group(1))

    # Next, check for our own "Please supply N UNIT of ..." format
    supply_match = re.search(rf"please supply\s+(\d+)\s+(?:{UNITS_RE})\s+of\b", enquiry, re.IGNORECASE)
    if supply_match:
        return int(supply_match.group(1))

    if product_name:
        # Try to find quantity near product name (standard format: "20 pcs product")
        pattern = re.compile(
            rf"(\d+)\s*(?:{UNITS_RE})\b.*?{re.escape(product_name)}|"
            rf"{re.escape(product_name)}.*?(\d+)\s*(?:{UNITS_RE})\b",
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(enquiry)
        if match:
            return int(match.group(1) or match.group(2))

        # Try tabular format with flexible spacing/case for product name
        product_tokens = [t for t in re.split(r"\W+", product_name.lower()) if t and len(t) > 2]
        if product_tokens:
            token_pattern = r".*?".join(re.escape(t) for t in product_tokens)
            tabular_pattern = re.compile(
                rf"({token_pattern})[^0-9]*(?:pcs|pkts?|m|meters|units|nos?)[^0-9]*(\d+)",
                re.IGNORECASE | re.DOTALL,
            )
            match = tabular_pattern.search(enquiry)
            if match:
                return int(match.group(2))

    # Generic quantity pattern
    match = QUANTITY_PATTERN.search(enquiry)
    if match:
        return int(match.group(1))

    return 1


# ---------------------------------------------------------------------------
# Brand extraction
# ---------------------------------------------------------------------------
def extract_brand(text):
    """Extract a known brand name from text, returning it lowercased or None."""
    text_lower = text.lower()
    # Sort brands longest-first to match "a1 legrand" before "legrand"
    for brand in sorted(KNOWN_BRANDS, key=len, reverse=True):
        pattern = rf"\b{re.escape(brand)}\b"
        if re.search(pattern, text_lower):
            return brand
    return None


# ---------------------------------------------------------------------------
# Spec extraction
# ---------------------------------------------------------------------------
def extract_specs(text):
    """Extract electrical/physical specifications from text.

    Returns a dict with normalized spec keys:
        {"amps": "16", "pole": "3", "sqmm": "4", ...}
    """
    specs = {}
    text_lower = text.lower()

    # Extract ampere rating (handles ranges like "6.3-10A" and "16-25A")
    amp_match = AMP_PATTERN.search(text_lower)
    if amp_match:
        specs["amps"] = amp_match.group(1).replace(" ", "")

    # Extract pole count
    pole_match = POLE_PATTERN.search(text_lower)
    if pole_match:
        if pole_match.group(1):
            specs["pole"] = pole_match.group(1)
        elif pole_match.group(2):
            word_to_num = {"single": "1", "double": "2", "triple": "3", "four": "4"}
            specs["pole"] = word_to_num.get(pole_match.group(2).lower(), "1")

    # Extract sqmm
    sqmm_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:sqmm|sq\.?\s*mm)", text_lower)
    if sqmm_match:
        specs["sqmm"] = sqmm_match.group(1)

    # Extract way count (handles "1 way", "2-way", "1 w", "2w", etc.)
    # Note: we check context (like "switch", "socket", "plate", "box") to distinguish from "watts"
    way_match = re.search(r"\b(\d+)\s*(?:way|w)\b", text_lower)
    if way_match:
        prod_type = extract_product_type(text_lower)
        if prod_type in ["switch", "socket", "junction_box"] or "way" in text_lower or "plate" in text_lower or "gang box" in text_lower:
            specs["way"] = way_match.group(1)
        else:
            specs["watts"] = way_match.group(1)

    # Extract watts (if not already extracted as way)
    if "way" not in specs:
        watt_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:watts?|w)\b", text_lower)
        if watt_match:
            specs["watts"] = watt_match.group(1)

    # Extract voltage
    volt_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:volts?|v)\b", text_lower)
    if volt_match:
        specs["volts"] = volt_match.group(1)

    # Extract core count
    core_match = re.search(r"(\d+)\s*core", text_lower)
    if core_match:
        specs["core"] = core_match.group(1)

    # Extract mm size
    mm_match = re.search(r"(\d+)\s*mm\b", text_lower)
    if mm_match and "sqmm" not in specs:
        specs["mm"] = mm_match.group(1)

    return specs


def extract_product_type(text):
    """Identify the product type from text."""
    text_lower = text.lower()
    for ptype, keywords in PRODUCT_TYPE_KEYWORDS.items():
        for kw in keywords:
            pattern = rf"\b{re.escape(kw)}s?\b"
            if re.search(pattern, text_lower):
                return ptype
    return None


# ---------------------------------------------------------------------------
# Improved matching
# ---------------------------------------------------------------------------
def simple_name_match(product_name, enquiry_lower):
    """Check if a catalog product name matches an enquiry segment.

    Improved with brand-awareness and spec-awareness to prevent false matches.
    """
    name_lower = product_name.lower()

    # Exact substring match (highest confidence)
    if name_lower in enquiry_lower:
        return True

    # Extract brand from both sides
    catalog_brand = extract_brand(name_lower)
    enquiry_brand = extract_brand(enquiry_lower)

    # If both have brands and they differ, no match
    if catalog_brand and enquiry_brand:
        # Normalize brand aliases
        brand_aliases = {
            "sudhaker": "sudhakar", "havels": "havells",
            "l & t": "l&t", "general electric": "ge",
        }
        cb = brand_aliases.get(catalog_brand, catalog_brand)
        eb = brand_aliases.get(enquiry_brand, enquiry_brand)
        if cb != eb:
            return False

    # Extract and compare specs
    catalog_specs = extract_specs(name_lower)
    enquiry_specs = extract_specs(enquiry_lower)

    # If both have ampere ratings, they must match
    if "amps" in catalog_specs and "amps" in enquiry_specs:
        if catalog_specs["amps"] != enquiry_specs["amps"]:
            return False

    # If both have pole counts, they must match
    if "pole" in catalog_specs and "pole" in enquiry_specs:
        if catalog_specs["pole"] != enquiry_specs["pole"]:
            return False

    # If both have sqmm, they must match
    if "sqmm" in catalog_specs and "sqmm" in enquiry_specs:
        if catalog_specs["sqmm"] != enquiry_specs["sqmm"]:
            return False

    # If both have way counts, they must match
    if "way" in catalog_specs and "way" in enquiry_specs:
        if catalog_specs["way"] != enquiry_specs["way"]:
            return False

    # Split into key tokens (ignore single letters, common words, and any numbers/digits)
    # Numbers/digits are already strictly verified in the spec checks above.
    stop_words = {
        "the", "and", "for", "with", "make", "pvc", "nos", "pcs", "no", "nc",
        "off", "on", "in", "at", "by", "of", "to", "up", "or", "as", "if", "is",
        "it", "so", "from", "each", "per", "use", "type", "modular", "style",
        "series", "range", "model", "suitable", "approx", "colour", "color",
        "brand", "standard", "heavy", "duty", "light", "medium", "wire", "cable"
    }
    tokens = [
        token for token in re.split(r"\W+", name_lower)
        if token and len(token) > 1 and token not in stop_words and not re.search(r"\d", token)
    ]

    # Always exclude brand tokens from threshold and match calculation.
    # This prevents brand matches from satisfying the description matching threshold
    # (e.g. matching 'Legrand changeover switch' to a generic 'Legrand switch' request).
    if catalog_brand:
        brand_tokens = set(re.split(r"\W+", catalog_brand.lower()))
        tokens = [token for token in tokens if token not in brand_tokens]

    if not tokens:
        return False

    # Product type must match if both sides have one
    catalog_type = extract_product_type(name_lower)
    enquiry_type = extract_product_type(enquiry_lower)
    if catalog_type and enquiry_type and catalog_type != enquiry_type:
        return False

    # Smooth threshold matching:
    # - 1 token: requires 1 match
    # - 2 tokens: requires 2 matches
    # - 3+ tokens: requires at least 65% of tokens to match (minimum of 2 matches)
    enquiry_tokens = set(re.split(r"\W+", enquiry_lower))
    matched_tokens = 0
    for token in tokens:
        # Check for exact match or simple plural/singular match
        if token in enquiry_tokens or f"{token}s" in enquiry_tokens or (token.endswith('s') and token[:-1] in enquiry_tokens):
            matched_tokens += 1
            
    threshold = 1 if len(tokens) == 1 else max(2, int(len(tokens) * 0.65))
    return matched_tokens >= threshold


def parse_block_table_lines(lines):
    """Parse block-format tabular enquiries where data spans multiple lines.

    Handles format like:
        S.No / Material header
        Description
        Unit
        Quantity
    """
    parsed = []
    i = 0
    header_keywords = {"matera", "material", "description", "unit", "quantity",
                       "material description", "s.no", "s.no.", "s.no", "sr.no",
                       "sr. no", "sl.no", "sl. no", "item"}

    while i < len(lines):
        line = lines[i].strip()
        lowercase_line = line.lower()
        if not line or any(keyword in lowercase_line for keyword in header_keywords):
            i += 1
            continue

        # Pattern 1: Serial number followed by description, unit, quantity on next lines
        if re.match(r"^\d+$", line) and i + 3 < len(lines):
            description = lines[i + 1].strip()
            unit = lines[i + 2].strip()
            quantity = lines[i + 3].strip()
            if description and unit and re.match(r"^\d+$", quantity):
                parsed.append(f"Please supply {quantity} {unit} of {description}.")
                i += 4
                continue

        # Pattern 2: Product name on current line, unit on next, quantity after
        if i + 2 < len(lines) and re.match(r"^\d+$", lines[i + 2].strip()) and re.match(r"^[A-Za-z%]+$", lines[i + 1].strip()):
            product = lines[i].strip()
            unit = lines[i + 1].strip()
            quantity = lines[i + 2].strip()
            parsed.append(f"Please supply {quantity} {unit} of {product}.")
            i += 3
            continue

        # Pattern 3: Quantity on current line (look back for description and unit)
        if re.match(r"^\d+$", line) and i >= 2:
            quantity = line
            unit = lines[i - 1].strip()
            description = lines[i - 2].strip()
            product = lines[i - 3].strip() if i >= 3 else ""
            if product and unit:
                parsed.append(f"Please supply {quantity} {unit} of {product}. {description}")
                i += 1
                continue

        parsed.append(line)
        i += 1

    return parsed


def extract_text_for_unmatched(segment):
    cleaned = segment.strip()
    if not cleaned:
        return ""

    m = re.match(rf"please supply\s+(\d+)\s*(?:{UNITS_RE})\s+of\s+(.+)$", cleaned, re.IGNORECASE)
    if m:
        res = m.group(2).strip()
        if res.endswith('.'):
            res = res[:-1]
        return res

    cleaned = re.sub(r"please supply\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(rf"\b({UNITS_RE})\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bof\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()
    if cleaned.endswith('.'):
        cleaned = cleaned[:-1]
    return cleaned.strip()


def clean_email_headers_and_footers(text):
    """Remove email headers, footers, forwarding markers, signatures, and contact info from raw text."""
    if not text:
        return ""
        
    lines = text.split("\n")
    cleaned_lines = []
    
    # Common signature or header keywords to skip
    skip_keywords = {
        "forwarded message", "original message", "from:", "to:", "date:", "subject:", "cc:", "sent:",
        "corp off", "gst no", "msme/uam", "plot no", "hyderbasti", "secunderabad", "tel:", "mobile:",
        "dear sir", "dear madam", "yours faithfully", "yours sincerely", "best regards", "kind regards",
        "thanks & regards", "thanks and regards", "sent from my", "confidentiality notice", "disclaimer:",
        "http://", "https://", "www.", "to me,", "hours ago", "yesterday", "tomorrow", "wrote:"
    }
    
    # Simple regexes to detect contact lines
    phone_pattern = re.compile(r"\b\d{10}\b|\b\d{5}[-\s]\d{5}\b") # 10 digit phones
    email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    gst_pattern = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z0-9]{3}\b") # Indian GST format
    
    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()
        
        if not line_stripped:
            continue
            
        # Check explicit keywords
        if any(kw in line_lower for kw in skip_keywords):
            continue
            
        # Skip forwarding lines or lines of special symbols (like ====== or ------)
        if re.match(r"^[-=_*#\s]{3,}$", line_stripped):
            continue
            
        # Skip contact details
        if phone_pattern.search(line_stripped) or email_pattern.search(line_stripped) or gst_pattern.search(line_stripped):
            continue
            
        # Skip salutations or generic RFQ request lines if they are long/useless
        if line_lower.startswith("dear ") or line_lower.startswith("sub :") or line_lower.startswith("subject:"):
            continue
            
        cleaned_lines.append(line_stripped)
        
    return "\n".join(cleaned_lines)


def _is_valid_product_segment(text_lower):
    """Return True if the segment looks like a valid product request, False if it is a random sentence."""
    cleaned = text_lower.strip()
    
    # 1. If it was formatted as a merge block, it is definitely valid
    if "please supply" in cleaned:
        return True
        
    # 2. Check if it has a quantity and a unit
    has_qty = bool(re.search(r"\b\d+\b", cleaned))
    unit_re = re.compile(
        r"\b(nos|pcs|pieces|units|meters|mtrs?|pairs?|box|each|ea|coils?|rolls?|pkts?|sets?|kgs?|ltrs?|sqm|rmt)\b",
        re.IGNORECASE
    )
    has_unit = bool(unit_re.search(cleaned))
    
    if has_qty and has_unit:
        return True
        
    # 3. Check if it has a known product type keyword (e.g. MCB, wire, relay, switch)
    has_product_type = extract_product_type(cleaned) is not None
    
    # 4. Check if it has a known brand keyword
    has_brand = extract_brand(cleaned) is not None
    
    if has_product_type or has_brand:
        return True
        
    # 5. Check if it looks like a model number or specific electrical code (has digits + letters, e.g. ST-50-24, ATV320, DVP14)
    has_code = bool(re.search(r"\b[a-z]+\d+\w*\b|\b\d+[a-z]+\w*\b", cleaned))
    if has_code and len(cleaned) < 50:
        return True
        
    return False


def normalize_enquiry_input(enquiry):
    """Normalize raw enquiry text into a list of segments, each describing one product.

    Improved to handle:
    - Block tabular format (Material/Description/Unit/Quantity on separate lines)
    - Bullet/numbered lists
    - Pipe/tab delimited tables
    - Multi-line descriptions with Make: on the next line
    """
    if not enquiry:
        return []

    cleaned_text = clean_email_headers_and_footers(str(enquiry))
    text = cleaned_text.strip().replace("\r\n", "\n")
    if not text:
        return []

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return []

    # Detect block tabular format (Material/Description/Unit/Quantity headers)
    has_table_headers = any(re.search(r"\b(matera|material|description|unit|quantity)\b", line, re.IGNORECASE) for line in lines[:6])

    raw_segments = []
    if has_table_headers:
        # Filter out header lines before processing
        content_lines = [line for line in lines if not re.search(r"\b(matera|material|description|unit|quantity)\b", line, re.IGNORECASE)]

        # Try the improved multi-line block merger first (handles Make: patterns)
        merged = _try_merge_multiline_blocks(content_lines)
        if merged:
            raw_segments = merged
        else:
            # Fall back to the old block table parser
            raw_segments = parse_block_table_lines(content_lines)
    else:
        # --- Detect repeating block pattern even without headers ---
        merged = _try_merge_multiline_blocks(lines)
        if merged:
            raw_segments = merged
        else:
            normalized = []
            for line in lines:
                cleaned = re.sub(r"\s+", " ", line).strip()
                if not cleaned:
                    continue

                if "|" in cleaned or "\t" in cleaned:
                    converted = convert_table_like_line(cleaned)
                    normalized.extend(converted)
                    continue

                parts = [part.strip() for part in re.split(r"\s{2,}\s*", cleaned) if part.strip()]
                if len(parts) >= 2 and any(re.search(rf"(\d+)\s*(?:{UNITS_RE})", part, re.I) for part in parts):
                    converted = convert_table_like_line(cleaned)
                    normalized.extend(converted)
                    continue

                normalized.append(cleaned)
            raw_segments = normalized

    # Filter segments to remove random paragraphs, timestamps, notes, and instructions
    filtered_segments = []
    for seg in raw_segments:
        seg_lower = seg.lower().strip()
        if not seg_lower or len(seg_lower) < 3:
            continue
        if _is_non_product_text(seg_lower):
            continue
        if not _is_valid_product_segment(seg_lower):
            continue
        filtered_segments.append(seg)

    return filtered_segments


def _try_merge_multiline_blocks(lines):
    """Try to detect multi-line block patterns in enquiries.

    Handles formats like:
        Contactor                              <- product type/short name
        CONTACTOR MO C15 WITH MO-SA1L...       <- full description
        NOS                                    <- unit
        2                                      <- quantity

    Or with Make: lines:
        Over Load Relay 3UA 50 6.3-10Amps      <- product with specs
        Make: Siemens                          <- brand
        NOS                                    <- unit
        4                                      <- quantity

    Or short name + Make: + unit + qty:
        MCB 32A 3 Pole                         <- product with specs
        Make: LEGRAND                          <- brand
        NOS                                    <- unit
        6                                      <- quantity
    """
    unit_re = re.compile(r"^(NOS|PCS|PIECES|UNITS|METERS|M|PKTS?|SETS?|ROLLS?|COILS?|BUNDLES?|KGS?|LTRS?|PAIRS?|BOX|EACH|LOT|MTRS?|FEETS?|SQM|RMT|KM|NO|EA)(?:'S)?$", re.IGNORECASE)
    make_re = re.compile(r"^Make\s*[:\-]?\s*(.+)$", re.IGNORECASE)
    qty_re = re.compile(r"^\d+$")

    # First pass: tag each line
    tagged = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            tagged.append(("empty", stripped, ""))
        elif unit_re.match(stripped):
            tagged.append(("unit", stripped, ""))
        elif qty_re.match(stripped):
            tagged.append(("qty", stripped, ""))
        else:
            make_match = make_re.match(stripped)
            if make_match:
                tagged.append(("make", stripped, make_match.group(1).strip()))
            elif _is_non_product_text(stripped.lower()):
                tagged.append(("empty", stripped, ""))
            else:
                tagged.append(("text", stripped, ""))

    # Second pass: walk forward collecting product blocks.
    # A product block is:  1+ text lines, optional make line, unit line, qty line
    blocks = []
    i = 0
    while i < len(tagged):
        tag, val, extra = tagged[i]

        if tag == "empty":
            i += 1
            continue

        # Collect consecutive text lines (product descriptions)
        text_lines = []
        while i < len(tagged) and tagged[i][0] == "text":
            text_lines.append(tagged[i][1])
            i += 1

        # Optionally collect a Make: line right after text
        make_brand = None
        if i < len(tagged) and tagged[i][0] == "make":
            make_brand = tagged[i][2]  # extracted brand name
            i += 1

        # Look for unit and qty in any order (only if we have a description)
        unit_val = None
        qty_val = None
        
        if text_lines:
            for _ in range(2):
                if i < len(tagged):
                    next_tag = tagged[i][0]
                    if next_tag == "unit" and not unit_val:
                        unit_val = tagged[i][1]
                        i += 1
                    elif next_tag == "qty" and not qty_val:
                        qty_val = tagged[i][1]
                        i += 1
                    else:
                        break
                else:
                    break

        if text_lines and qty_val:
            # Build a merged description from all text lines + brand
            description = " ".join(text_lines)
            if make_brand:
                description += f" Make: {make_brand}"
            unit_str = unit_val or "NOS"
            blocks.append(f"Please supply {qty_val} {unit_str} of {description}.")
        elif text_lines:
            # No qty found — pass through individual lines
            for tl in text_lines:
                blocks.append(tl)
            if make_brand:
                blocks.append(f"Make: {make_brand}")
            if unit_val:
                blocks.append(unit_val)
            if qty_val:
                blocks.append(qty_val)
        else:
            # Skip unrecognised tag (shouldn't happen often)
            i += 1

    # Only use merged blocks if we found at least 1 product block with quantities
    qty_blocks = [b for b in blocks if b.startswith("Please supply")]
    if len(qty_blocks) >= 1:
        return blocks

    return None


def convert_table_like_line(line):
    cleaned = re.sub(r"\s+", " ", line).strip()
    if not cleaned:
        return []

    parts = [part.strip() for part in re.split(r"\s*\|\s*|\s*\t\s*|\s{2,}", cleaned) if part.strip()]
    if len(parts) >= 2:
        qty_index = None
        qty_match = None
        unit_index = None
        for idx, part in enumerate(parts):
            match = re.search(rf"(\d+)\s*({UNITS_RE})", part, re.I)
            if match:
                qty_index = idx
                qty_match = match
                break

        if qty_match and qty_index is not None:
            quantity = int(qty_match.group(1))
            unit = qty_match.group(2).lower()
            product_parts = [part for idx, part in enumerate(parts) if idx != qty_index]
            product_text = " ".join(product_parts).strip(" ,;:-")
            if product_text:
                return [f"Please supply {quantity} {unit} of {product_text}."]

        for idx, part in enumerate(parts):
            if re.fullmatch(r"\d+", part.strip()):
                qty_index = idx
                break

        if qty_index is not None:
            for candidate_idx in [qty_index - 1, qty_index + 1]:
                if 0 <= candidate_idx < len(parts):
                    unit_match = re.fullmatch(rf"({UNITS_RE})", parts[candidate_idx].strip(), re.I)
                    if unit_match:
                        unit_index = candidate_idx
                        break

            if unit_index is not None:
                quantity = int(parts[qty_index].strip())
                unit = parts[unit_index].strip().lower()
                product_parts = [
                    parts[idx]
                    for idx in range(len(parts))
                    if idx not in {qty_index, unit_index}
                ]
                product_text = " ".join(product_parts).strip(" ,;:-")
                if product_text:
                    return [f"Please supply {quantity} {unit} of {product_text}."]

    quantity_match = re.search(rf"(\d+)\s*({UNITS_RE})\b(?:\s*(.+))?", cleaned, re.I)
    if quantity_match:
        quantity = int(quantity_match.group(1))
        unit = quantity_match.group(2).lower()
        remainder = (quantity_match.group(3) or "").strip(" ,;:-")
        if remainder:
            return [f"Please supply {quantity} {unit} of {remainder}."]

    return [cleaned]


def _is_non_product_text(text_lower):
    """Return True if the text is generic enquiry language, not a product request."""
    cleaned = text_lower.strip()
    # Reject pure quantities/serial numbers (digits/decimals only)
    if re.match(r"^\d+(?:\.\d+)?$", cleaned):
        return True
        
    # Reject pure unit words (like NOS, PCS, MTR'S)
    unit_re = re.compile(r"^(NOS|PCS|PIECES|UNITS|METERS|M|PKTS?|SETS?|ROLLS?|COILS?|BUNDLES?|KGS?|LTRS?|PAIRS?|BOX|EACH|LOT|MTRS?|FEETS?|SQM|RMT|KM|NO|EA)(?:'S)?$", re.IGNORECASE)
    if unit_re.match(cleaned):
        return True

    # Check for contact details: phone, email, GST, company details
    phone_pattern = re.compile(r"\b\d{10}\b|\b\d{5}[-\s]\d{5}\b")
    email_pattern = re.compile(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b")
    gst_pattern = re.compile(r"\bgstin\b|\bgst\s*no\b|\b\d{2}[a-z]{5}\d{4}[a-z]{1}[a-z0-9]{3}\b")
    address_keywords = {"plot no", "survey no", "road", "colony", "industrial area", "secunderabad", "hyderabad", "telangana", "corp off", "regd off", "fax", "tele ph", "email id"}
    date_keywords = {"jan ", "feb ", "mar ", "apr ", "may ", "jun ", "jul ", "aug ", "sep ", "oct ", "nov ", "dec ", "hours ago", "to me,", "wrote:"}
    
    if phone_pattern.search(cleaned) or email_pattern.search(cleaned) or gst_pattern.search(cleaned):
        return True
        
    if any(re.search(rf"\b{re.escape(kw)}\b", cleaned) for kw in address_keywords) or any(kw in cleaned for kw in date_keywords):
        return True

    # Common filler/salutation patterns
    filler_patterns = [
        r"^we (?:are |need |require |want |would )",
        r"^(?:please |kindly )(?:quote|send|provide|share|give|arrange|confirm)",
        r"^(?:dear |hi |hello |respected |to whom)",
        r"^(?:thank|regards|sincerely|best wishes|yours)",
        r"^(?:looking for|we need|we require|we want)\s*:?\s*$",
        r"^(?:subject|ref|reference|enquiry|quotation|quote)\s*[:\-]",
        r"delivery\s+(?:within|by|before|at|in)",
        r"(?:current|latest|best)\s+pric",
        r"(?:urgent|asap|immediately|earliest)\b",
        r"^(?:note|please note|n\.b)\s*[:\-]",
        r"^sr\.?\s*no\b|^s\.?no\b|^sl\.?\s*no\b",
        r"^s\.no\b",
        r"^description\b|^qty\b|^uom\b|^unit\b",
        r"============ forwarded message ============"
    ]
    for pattern in filler_patterns:
        if re.search(pattern, cleaned):
            return True

    # Skip lines that have no product-like content (no digits, no brand, no product keywords)
    has_number = bool(re.search(r"\d", cleaned))
    has_brand = extract_brand(cleaned) is not None
    has_product_type = extract_product_type(cleaned) is not None
    has_supply = "please supply" in cleaned

    if not has_number and not has_brand and not has_product_type and not has_supply:
        # Likely generic text — but only skip if it's short-ish and has no qty/unit marker
        if len(cleaned) < 100 and not re.search(r"\b(pcs|nos|meters|units|qty)\b", cleaned, re.I):
            return True

    return False


def parse_enquiry_with_fallback(enquiry, catalog):
    """Parse an enquiry and match products against the catalog.

    Improved with:
    - Brand-aware matching (Schneider enquiry won't match L&T products)
    - Spec-aware matching (16A won't match 32A, 3 Pole won't match Single Pole)
    - Multi-brand results: when no brand specified, returns ALL brand options
    - Multi-line block format support
    """
    segments = normalize_enquiry_input(enquiry)
    if not segments:
        return []

    products = []
    seen_requirements = set()

    for segment in segments:
        segment_lower = segment.lower()

        # Skip segments that are too short or look like headers
        if len(segment.strip()) < 3:
            continue
        if re.match(r"^(matera|material|description|unit|quantity|s\.?no|sr\.?\s*no)$", segment.strip(), re.IGNORECASE):
            continue

        # Skip non-product text (greetings, filler, sign-offs, generic enquiry language)
        if _is_non_product_text(segment_lower):
            continue

        # Check if enquiry segment specifies a brand
        enquiry_brand = extract_brand(segment_lower)
        enquiry_type = extract_product_type(segment_lower)
        enquiry_specs = extract_specs(segment_lower)
        qty = find_quantity(segment)

        # Find all matching products
        matched_products = [
            product for product in catalog
            if simple_name_match(product["product_name"], segment_lower)
        ]

        if matched_products:
            if enquiry_brand:
                # Brand specified → pick the best match (single result)
                best_match = _pick_best_match(matched_products, segment_lower)
                products.append({
                    "product_name": best_match["product_name"],
                    "quantity": qty,
                    "requirement": segment.strip(),
                    "all_matches": [best_match],
                })
            else:
                # No brand → return the best match PER brand
                brand_best = _pick_best_per_brand(matched_products, segment_lower)
                if brand_best:
                    # Use the top-scoring match as the primary product name
                    top = brand_best[0]
                    products.append({
                        "product_name": top["product_name"],
                        "quantity": qty,
                        "requirement": segment.strip(),
                        "all_matches": brand_best,
                    })
            continue

        # Fuzzy fallback for unmatched text
        cleaned_text = extract_text_for_unmatched(segment)
        if not cleaned_text:
            continue

        if enquiry_brand:
            catalog_match = find_catalog_match(cleaned_text, catalog)
            all_matches = [catalog_match] if catalog_match else []
        else:
            all_matches = find_all_catalog_matches(cleaned_text, catalog)

        if all_matches:
            products.append({
                "product_name": all_matches[0]["product_name"],
                "quantity": qty,
                "requirement": segment.strip(),
                "all_matches": all_matches,
            })
        else:
            products.append({
                "product_name": cleaned_text,
                "quantity": qty,
                "requirement": segment.strip(),
                "all_matches": [],
            })

    if products:
        return products

    # Last-resort: match entire enquiry as one block
    enquiry_lower = str(enquiry).lower()
    all_matches = []
    for product in catalog:
        if simple_name_match(product["product_name"], enquiry_lower):
            all_matches.append(product)

    if all_matches:
        enquiry_brand = extract_brand(enquiry_lower)
        if enquiry_brand:
            best = _pick_best_match(all_matches, enquiry_lower)
            products.append({
                "product_name": best["product_name"],
                "quantity": find_quantity(enquiry),
                "requirement": enquiry.strip(),
                "all_matches": [best],
            })
        else:
            brand_best = _pick_best_per_brand(all_matches, enquiry_lower)
            products.append({
                "product_name": brand_best[0]["product_name"] if brand_best else enquiry.strip(),
                "quantity": find_quantity(enquiry),
                "requirement": enquiry.strip(),
                "all_matches": brand_best,
            })

    return products


def _score_product_match(product, segment_lower):
    """Compute matching score for a candidate product against an enquiry segment."""
    segment_brand = extract_brand(segment_lower)
    segment_specs = extract_specs(segment_lower)
    segment_type = extract_product_type(segment_lower)

    name_lower = product["product_name"].lower()
    score = 0.0

    # Exact substring match bonus
    if name_lower in segment_lower:
        score += 5.0

    # Brand match
    product_brand = extract_brand(name_lower)
    if product_brand and segment_brand:
        brand_aliases = {
            "sudhaker": "sudhakar", "havels": "havells",
            "l & t": "l&t", "general electric": "ge",
        }
        pb = brand_aliases.get(product_brand, product_brand)
        sb = brand_aliases.get(segment_brand, segment_brand)
        if pb == sb:
            score += 10.0
        else:
            score -= 20.0  # Wrong brand is a strong negative

    # Spec matches
    product_specs = extract_specs(name_lower)
    for spec_key in ["amps", "pole", "sqmm", "watts", "core", "mm", "way"]:
        if spec_key in product_specs and spec_key in segment_specs:
            if product_specs[spec_key] == segment_specs[spec_key]:
                score += 5.0  # Matching spec is very valuable
            else:
                score -= 15.0  # Wrong spec is a strong negative
        elif spec_key in product_specs and spec_key not in segment_specs:
            # Product has a spec the enquiry doesn't mention — mild penalty
            # e.g. enquiry says "4 sqmm Wire" but product is "2 Core 4 sqmm Cable"
            score -= 2.0

    # Wire vs Cable subtype awareness
    enquiry_is_wire = bool(re.search(r"\bwir(?:e|ing)\b", segment_lower))
    enquiry_is_cable = bool(re.search(r"\bcable\b", segment_lower))
    product_is_wire = bool(re.search(r"\bwir(?:e|ing)\b", name_lower))
    product_is_cable = bool(re.search(r"\bcable\b", name_lower))
    if enquiry_is_wire and product_is_cable and not product_is_wire:
        score -= 5.0  # Enquiry says wire, product says cable
    if enquiry_is_cable and product_is_wire and not product_is_cable:
        score -= 5.0  # Enquiry says cable, product says wire
    if enquiry_is_wire and product_is_wire:
        score += 2.0  # Both say wire
    if enquiry_is_cable and product_is_cable:
        score += 2.0  # Both say cable

    # Product type match
    product_type = extract_product_type(name_lower)
    if product_type and segment_type:
        if product_type == segment_type:
            score += 3.0
        else:
            score -= 10.0

    # Name length bonus (more specific names are better matches)
    score += len(name_lower) * 0.05

    # Penalize unmatched specialized tokens in the product name
    # (e.g. if catalog product has 'auxiliary', 'changeover', 'wireless' but enquiry does not)
    stop_words = {"the", "and", "for", "with", "make", "pvc", "nos", "pcs", "modular"}
    product_tokens = [t for t in re.split(r"\W+", name_lower) if t and len(t) > 1 and t not in stop_words]
    p_brand = extract_brand(name_lower)
    brand_tokens = set(re.split(r"\W+", p_brand.lower())) if p_brand else set()
    
    unmatched_special_tokens = 0
    for token in product_tokens:
        if token not in brand_tokens and token not in ["switch", "socket", "mcb", "mccb", "rccb", "rcbo", "relay", "contactor"]:
            # Ignore numbers/specs that are checked elsewhere
            if not re.search(r"\d", token):
                if token not in segment_lower:
                    unmatched_special_tokens += 1
    score -= unmatched_special_tokens * 2.0

    return score


def _pick_best_match(matched_products, segment_lower):
    """Pick the best matching product from a list of candidates."""
    best = None
    best_score = -9999.0

    for product in matched_products:
        score = _score_product_match(product, segment_lower)
        if score > best_score:
            best_score = score
            best = product

    return best or matched_products[0]


def _pick_best_per_brand(matched_products, segment_lower):
    """Group matched products by brand and pick the best match for each brand.
    Returns a list of best products per brand, sorted by score descending.
    """
    brand_groups = {}
    for product in matched_products:
        brand = extract_brand(product["product_name"].lower()) or "generic"
        brand_aliases = {
            "sudhaker": "sudhakar", "havels": "havells",
            "l & t": "l&t", "general electric": "ge",
        }
        brand = brand_aliases.get(brand, brand)
        if brand not in brand_groups:
            brand_groups[brand] = []
        brand_groups[brand].append(product)

    best_per_brand = []
    for brand, products in brand_groups.items():
        best = _pick_best_match(products, segment_lower)
        score = _score_product_match(best, segment_lower)
        # Avoid including low-scoring/irrelevant brand suggestions
        if score >= 0.0 or len(best_per_brand) == 0:
            best_per_brand.append((best, score))

    # Sort by score descending
    best_per_brand.sort(key=lambda x: x[1], reverse=True)
    return [x[0] for x in best_per_brand]


def extract_requirement(enquiry, product_name):
    prefixed = re.search(rf"{re.escape(product_name)}[,:]?\s*([^\n\r]+)", enquiry, re.IGNORECASE)
    if prefixed:
        return prefixed.group(1).strip()
    return enquiry.strip()


def normalize_product_name(name):
    if not isinstance(name, str):
        return ""
    normalized = name.lower()
    normalized = normalized.replace("mm", "mm")
    normalized = normalized.replace("-", " ")
    normalized = normalized.replace("/", " ")
    normalized = normalized.replace("  ", " ")
    normalized = normalized.strip()
    return normalized


def tokenize_name(name):
    normalized = normalize_product_name(name)
    tokens = [token for token in re.split(r"\W+", normalized) if token]
    numeric = [token for token in tokens if re.search(r"\d", token)]
    text = [token for token in tokens if token not in numeric]
    return tokens, text, numeric


def find_catalog_match(product_name, catalog):
    """Find the best matching product in the catalog using fuzzy matching.

    Improved with:
    - Brand-aware scoring
    - Spec-aware scoring (amps, pole, sqmm must match)
    - Higher threshold (0.65 instead of 0.55)
    - Product type awareness
    """
    product_name_lower = normalize_product_name(product_name)
    for product in catalog:
        if product_name_lower == normalize_product_name(product["product_name"]):
            return product

    query_tokens, query_text, query_numeric = tokenize_name(product_name_lower)
    if not query_tokens:
        return None

    # Extract brand and specs from query
    query_brand = extract_brand(product_name_lower)
    query_specs = extract_specs(product_name_lower)
    query_type = extract_product_type(product_name_lower)

    best_candidate = None
    best_score = 0.0

    for product in catalog:
        candidate_name = normalize_product_name(product["product_name"])
        candidate_tokens, candidate_text, candidate_numeric = tokenize_name(candidate_name)

        if query_numeric and candidate_numeric and not set(query_numeric).intersection(candidate_numeric):
            continue

        common_tokens = set(query_tokens).intersection(candidate_tokens)
        common_text = set(query_text).intersection(candidate_text)

        if not common_tokens:
            continue

        # --- Brand check ---
        candidate_brand = extract_brand(candidate_name)
        if query_brand and candidate_brand:
            brand_aliases = {
                "sudhaker": "sudhakar", "havels": "havells",
                "l & t": "l&t", "general electric": "ge",
            }
            qb = brand_aliases.get(query_brand, query_brand)
            cb = brand_aliases.get(candidate_brand, candidate_brand)
            if qb != cb:
                continue  # Skip wrong brand entirely

        # --- Spec check ---
        candidate_specs = extract_specs(candidate_name)
        spec_mismatch = False
        for spec_key in ["amps", "pole", "sqmm"]:
            if spec_key in query_specs and spec_key in candidate_specs:
                if query_specs[spec_key] != candidate_specs[spec_key]:
                    spec_mismatch = True
                    break
        if spec_mismatch:
            continue

        # --- Product type check ---
        candidate_type = extract_product_type(candidate_name)
        if query_type and candidate_type and query_type != candidate_type:
            continue

        text_score = len(common_text) / max(1, len(query_text))
        token_score = len(common_tokens) / max(1, len(query_tokens))
        fuzzy_score = difflib.SequenceMatcher(None, product_name_lower, candidate_name).ratio()

        # Brand match bonus
        brand_bonus = 0.0
        if query_brand and candidate_brand:
            brand_aliases = {"sudhaker": "sudhakar", "havels": "havells", "l & t": "l&t", "general electric": "ge"}
            if brand_aliases.get(query_brand, query_brand) == brand_aliases.get(candidate_brand, candidate_brand):
                brand_bonus = 0.15

        # Spec match bonus
        spec_bonus = 0.0
        matched_specs = 0
        for spec_key in ["amps", "pole", "sqmm", "watts"]:
            if spec_key in query_specs and spec_key in candidate_specs:
                if query_specs[spec_key] == candidate_specs[spec_key]:
                    matched_specs += 1
        spec_bonus = matched_specs * 0.1

        score = (2.0 * text_score + token_score + fuzzy_score) / 4.0 + brand_bonus + spec_bonus

        if score > best_score:
            best_score = score
            best_candidate = product

    # Raised threshold from 0.55 to 0.65
    if best_candidate and best_score >= 0.65:
        return best_candidate

    return None


def find_all_catalog_matches(product_name, catalog):
    """Find all matching products (best per brand) above a threshold using fuzzy matching."""
    product_name_lower = normalize_product_name(product_name)
    query_tokens, query_text, query_numeric = tokenize_name(product_name_lower)
    if not query_tokens:
        return []

    query_brand = extract_brand(product_name_lower)
    query_specs = extract_specs(product_name_lower)
    query_type = extract_product_type(product_name_lower)

    candidates_by_brand = {}

    for product in catalog:
        candidate_name = normalize_product_name(product["product_name"])
        candidate_tokens, candidate_text, candidate_numeric = tokenize_name(candidate_name)

        if query_numeric and candidate_numeric and not set(query_numeric).intersection(candidate_numeric):
            continue

        common_tokens = set(query_tokens).intersection(candidate_tokens)
        common_text = set(query_text).intersection(candidate_text)

        if not common_tokens:
            continue

        # --- Brand check ---
        candidate_brand = extract_brand(candidate_name)
        if query_brand and candidate_brand:
            brand_aliases = {
                "sudhaker": "sudhakar", "havels": "havells",
                "l & t": "l&t", "general electric": "ge",
            }
            qb = brand_aliases.get(query_brand, query_brand)
            cb = brand_aliases.get(candidate_brand, candidate_brand)
            if qb != cb:
                continue  # Skip wrong brand entirely

        # --- Spec check ---
        candidate_specs = extract_specs(candidate_name)
        spec_mismatch = False
        for spec_key in ["amps", "pole", "sqmm"]:
            if spec_key in query_specs and spec_key in candidate_specs:
                if query_specs[spec_key] != candidate_specs[spec_key]:
                    spec_mismatch = True
                    break
        if spec_mismatch:
            continue

        # --- Product type check ---
        candidate_type = extract_product_type(candidate_name)
        if query_type and candidate_type and query_type != candidate_type:
            continue

        text_score = len(common_text) / max(1, len(query_text))
        token_score = len(common_tokens) / max(1, len(query_tokens))
        fuzzy_score = difflib.SequenceMatcher(None, product_name_lower, candidate_name).ratio()

        brand_bonus = 0.0
        if query_brand and candidate_brand:
            brand_aliases = {"sudhaker": "sudhakar", "havels": "havells", "l & t": "l&t", "general electric": "ge"}
            if brand_aliases.get(query_brand, query_brand) == brand_aliases.get(candidate_brand, candidate_brand):
                brand_bonus = 0.15

        spec_bonus = 0.0
        matched_specs = 0
        for spec_key in ["amps", "pole", "sqmm", "watts"]:
            if spec_key in query_specs and spec_key in candidate_specs:
                if query_specs[spec_key] == candidate_specs[spec_key]:
                    matched_specs += 1
        spec_bonus = matched_specs * 0.1

        score = (2.0 * text_score + token_score + fuzzy_score) / 4.0 + brand_bonus + spec_bonus

        if score >= 0.65:
            # Group by brand
            brand = candidate_brand or "generic"
            brand_aliases = {"sudhaker": "sudhakar", "havels": "havells", "l & t": "l&t", "general electric": "ge"}
            brand = brand_aliases.get(brand, brand)
            
            if brand not in candidates_by_brand or score > candidates_by_brand[brand][1]:
                candidates_by_brand[brand] = (product, score)

    # Sort by score descending
    sorted_matches = sorted(candidates_by_brand.values(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in sorted_matches]


def build_quote_rows(parsed_items, catalog):
    rows = []
    matched_products = set()
    for item in parsed_items:
        product_description = item.get("requirement", "").strip()
        qty = int(item.get("quantity", 1) or 1)
        
        matches = item.get("all_matches", [])
        if not matches:
            # Fallback if parse didn't pre-populate all_matches
            matched = find_catalog_match(item.get("product_name", ""), catalog)
            matches = [matched] if matched else []

        if matches:
            best_match = matches[0]
            note = best_match.get("note") or "matched"
            if len(matches) > 1:
                other_brands = []
                for m in matches[1:]:
                    brand = extract_brand(m["product_name"].lower()) or "Generic"
                    other_brands.append(brand.upper())
                note = f"Best match. Alternatives: {', '.join(other_brands)}"
                
            row = {
                "product_id": best_match["product_id"],
                "product_name": best_match["product_name"],
                "requirement": product_description,
                "requested_quantity": qty,
                "unit": best_match["unit"],
                "unit_price": best_match["latest_price"],
                "discount": "0%",
                "total_price": round(qty * best_match["latest_price"], 2),
                "note": note,
            }
            rows.append(row)
            matched_products.add(best_match["product_name"])
        else:
            row = {
                "product_id": "",
                "product_name": item.get("product_name", "").strip(),
                "requirement": product_description,
                "requested_quantity": qty,
                "unit": "",
                "unit_price": 0.0,
                "discount": "0%",
                "total_price": 0.0,
                "note": "product not found in catalog",
            }
            rows.append(row)

    if not rows and parsed_items:
        qty = int(parsed_items[0].get("quantity", 1) or 1)
        rows.append(
            {
                "product_id": "",
                "product_name": parsed_items[0].get("product_name", "").strip(),
                "requirement": parsed_items[0].get("requirement", "").strip(),
                "requested_quantity": qty,
                "unit": "",
                "unit_price": 0.0,
                "discount": "0%",
                "total_price": 0.0,
                "note": "product not found in catalog",
            }
        )

    return rows


def write_quote_csv(output_path, quote_rows, enquiry_text):
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=QUOTE_HEADERS)
        writer.writeheader()
        for row in quote_rows:
            writer.writerow(row)

    print(f"Quote saved to: {output_path}")
    print(f"Quote generated from enquiry: {enquiry_text[:200]!r}")


def parse_enquiry(enquiry, catalog):
    if os.environ.get("GEMINI_API_KEY"):
        try:
            parsed = call_gemini_api(enquiry)
            if isinstance(parsed, list) and parsed:
                return parsed
            print("Gemini returned no structured items; falling back to local extraction.")
        except Exception as exc:
            print(f"Gemini extraction failed: {exc}")
            print("Falling back to local extraction.")

    return parse_enquiry_with_fallback(enquiry, catalog)


def main():
    parser = argparse.ArgumentParser(description="Automate quotation creation from an enquiry and product catalog.")
    parser.add_argument("--catalog", required=True, help="Path to product catalog CSV or JSON file.")
    parser.add_argument("--enquiry", help="Enquiry text.")
    parser.add_argument("--enquiry-file", help="Path to a text file containing the enquiry.")
    parser.add_argument("--output", default="quotation.csv", help="Output quote CSV path.")
    args = parser.parse_args()

    if not args.enquiry and not args.enquiry_file:
        parser.error("Provide either --enquiry or --enquiry-file.")

    if args.enquiry_file:
        with open(args.enquiry_file, encoding="utf-8") as fh:
            enquiry_text = fh.read().strip()
    else:
        enquiry_text = args.enquiry.strip()

    catalog = load_catalog(args.catalog)
    if not catalog:
        raise RuntimeError("Catalog is empty or could not be loaded.")

    parsed_items = parse_enquiry(enquiry_text, catalog)
    if not parsed_items:
        print("No products detected in enquiry. Please verify the enquiry text or catalog.")
        sys.exit(1)

    quote_rows = build_quote_rows(parsed_items, catalog)
    write_quote_csv(args.output, quote_rows, enquiry_text)


if __name__ == "__main__":
    main()
