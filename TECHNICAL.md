# Technical Documentation

## Architecture Overview

The Quotation Automation System is a three-tier application:

```
┌─────────────────────────────────────────────────────┐
│         Web Browser (Frontend)                      │
│  HTML/CSS/JavaScript - Interactive UI               │
└────────────────┬────────────────────────────────────┘
                 │ HTTP/REST API
┌────────────────▼────────────────────────────────────┐
│         Flask Server (app.py)                       │
│  API Endpoints - Request Handling                   │
└────────────────┬────────────────────────────────────┘
                 │ Python Functions
┌────────────────▼────────────────────────────────────┐
│    Quotation Engine (quotation_automation.py)       │
│  Product Matching - Quotation Generation            │
└─────────────────────────────────────────────────────┘
```

## Core Modules

### 1. quotation_automation.py
**Purpose**: Core automation logic

**Key Functions**:
- `load_catalog()` - Load CSV/JSON catalog
- `parse_enquiry()` - Extract products from text (with Gemini fallback)
- `build_quote_rows()` - Match products and create quotation
- `find_catalog_match()` - Fuzzy product matching

**Data Flow**:
```
Enquiry Text → Parse Items → Find Catalog Matches → Build Rows → CSV Output
```

### 2. app.py
**Purpose**: Flask web server and API

**Key Endpoints**:
- `GET /` - Main web interface
- `GET /api/catalogs` - List available catalogs
- `POST /api/upload-catalog` - Upload new catalog
- `POST /api/generate-quotation` - Generate quotation
- `POST /api/export-quotation` - Export as CSV

**Request/Response Example**:
```python
# Generate Quotation Request
POST /api/generate-quotation
{
    "enquiry": "Need 20 pcs Schneider sockets",
    "catalog": "product_list.csv"
}

# Response
{
    "message": "Quotation generated successfully",
    "quotation": [
        {
            "product_name": "Schneider 16A Socket",
            "requested_quantity": 20,
            "unit_price": 320.00,
            "total_price": 6400.00,
            "discount": "0%"
        }
    ]
}
```

### 3. templates/index.html
**Purpose**: Interactive web interface

**Features**:
- Catalog upload with drag-and-drop
- Real-time quotation generation
- Inline quantity and discount editing
- CSV export functionality
- Responsive design for mobile

**JavaScript Functions**:
- `loadCatalogs()` - Fetch available catalogs
- `generateQuotation()` - API call to generate quote
- `updateSummary()` - Recalculate totals on edit
- `exportQuotation()` - Download CSV

## Data Formats

### Catalog Format (CSV)
```csv
product_id,product_name,latest_price,unit,description
P001,Schneider 16A Socket,320.00,pcs,Wall mounted socket
P002,Polycab 4 sqmm Wire,34.20,m,Insulated copper wire
```

### Quotation Format (CSV Output)
```csv
product_id,product_name,requirement,requested_quantity,unit,unit_price,discount,total_price,note
P001,Schneider 16A Socket,Office wiring,20,pcs,320.00,10%,5760.00,
```

## Product Matching Algorithm

1. **Exact Match**: Direct string comparison (case-insensitive)
2. **Simple Substring**: Check if product name contains enquiry keywords
3. **Token Matching**: Match multiple keywords
4. **Fuzzy Matching**: Difflib sequence matching (>50% similarity)
5. **Gemini API** (Optional): AI-powered extraction when enabled

**Match Score Logic**:
```python
if product_name.lower() == enquiry.lower():
    return product  # Exact match
elif product_name.lower() in enquiry.lower():
    return product  # Substring match
else:
    score = calculate_similarity(product_name, enquiry)
    if score > 0.5:  # Fuzzy match threshold
        return product
```

## Quantity Extraction

Regex patterns for quantity detection:
```
\d+ pcs     → matches "20 pcs"
\d+ pieces  → matches "50 pieces"
\d+ qty     → matches "100 qty"
\d+ meters  → matches "100 meters"
\d+ m       → matches "50 m"
```

Default quantity if not found: **1**

## Discount Calculation

User-edited discount field stores percentage:
```python
final_price = unit_price * quantity * (1 - discount_percent / 100)
```

Example:
```
Unit Price: ₹100
Quantity: 10
Discount: 10%
Final Price: 100 × 10 × (1 - 10/100) = ₹900
```

## File Directory Structure

```
LP of SKD/
├── app.py                      # Flask server
├── quotation_automation.py      # Core engine
├── config.py                   # Configuration
├── utils.py                    # Utilities
├── setup.py                    # Setup script
├── requirements.txt            # Dependencies
├── .gitignore                  # Git ignore
│
├── templates/
│   └── index.html              # Web frontend
│
├── product_catalog_sample.csv   # Sample catalog
├── sample_enquiry.txt          # Sample enquiry
│
├── run_web.ps1                 # PowerShell startup
├── run_web.bat                 # Batch startup
├── run_web.sh                  # Bash startup
│
├── README.md                   # Main documentation
├── QUICKSTART.md               # Quick start guide
├── TECHNICAL.md                # This file
│
├── uploads/                    # Uploaded files (created)
├── catalogs/                   # Stored catalogs (created)
├── venv/                       # Virtual environment (created)
```

## Configuration

### Environment Variables

```bash
# Optional Gemini API Integration
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-pro
GEMINI_API_URL=https://api.openai.com/v1/responses

# Flask Settings
FLASK_ENV=development  # or production
FLASK_DEBUG=1
```

### config.py Settings

```python
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Max upload size
UPLOAD_FOLDER = "uploads"               # Temporary files
CATALOG_FOLDER = "catalogs"             # Persistent catalogs
SESSION_LIFETIME = 7 days               # Session duration
```

## Deployment Guide

### Local Development
```bash
python app.py  # Runs on http://localhost:5000
```

### Production Deployment (Gunicorn + Nginx)

**Install Gunicorn**:
```bash
pip install gunicorn
```

**Run with Gunicorn**:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**Nginx Configuration**:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## API Reference

### Upload Catalog
```
POST /api/upload-catalog
Content-Type: multipart/form-data

body:
  file: <CSV or JSON file>

Response:
  200 OK: { filename, product_count }
  400 Bad Request: { error }
```

### Generate Quotation
```
POST /api/generate-quotation
Content-Type: application/json

body:
{
  "enquiry": "Need 20 pcs sockets",
  "catalog": "catalog.csv"
}

Response:
  200 OK: { quotation: [...] }
  400 Bad Request: { error }
```

### Export Quotation
```
POST /api/export-quotation
Content-Type: application/json

body:
{
  "quotation": [...],
  "customer_name": "ABC Company"
}

Response:
  200 OK: CSV file (application/csv)
  400 Bad Request: { error }
```

### List Catalogs
```
GET /api/catalogs

Response:
  200 OK: { catalogs: [{name, path}, ...] }
```

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Port 5000 in use | Another app using port | Change port in app.py |
| Catalog not found | File deleted or moved | Re-upload catalog |
| No products matched | Poor enquiry wording | Be more specific |
| CSV parse error | Invalid encoding | Save as UTF-8 |
| Module not found | Dependencies missing | Run `pip install -r requirements.txt` |

## Performance Optimization

### Catalog Loading
- Catalogs cached in memory after loading
- Lazy loading from disk on first access

### Fuzzy Matching
- Capped at top 5 matches to reduce computation
- Sequence matcher similarity threshold: 0.45

### Frontend
- Real-time calculation on client-side
- No server round-trip for discount updates
- Minimal API calls

## Security Considerations

### Input Validation
- File extension whitelist (CSV, JSON only)
- File size limit: 16MB
- Path traversal prevention via `secure_filename()`

### Data Protection
- Uploaded files in separate `uploads/` directory
- No sensitive data stored in session
- CORS not enabled (same-origin only)

### Production Recommendations
- Use HTTPS/TLS
- Enable CSRF protection
- Implement rate limiting
- Add authentication
- Use environment variables for secrets

## Troubleshooting

### Module Import Error
```
ModuleNotFoundError: No module named 'flask'
```
Solution: Activate venv and reinstall
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

### Product Not Matching
- Check exact product names in catalog
- Try using keywords instead of full names
- Enable Gemini API for better AI matching
- Check for typos and spelling

### Quotation Not Exporting
- Check browser downloads folder
- Clear browser cache
- Try different browser
- Check browser console for errors (F12)

## Contributing & Extending

### Add New Product Matching Logic
Edit `find_catalog_match()` in `quotation_automation.py`

### Add Database Support
Modify `load_catalog()` to query database instead of CSV

### Add Email Notifications
Extend `export_quotation()` endpoint in `app.py`

### Add Authentication
Implement Flask-Login or OAuth2

### Add Quotation History
Add SQLite database for storing past quotations

## Support Resources

- Python docs: https://docs.python.org/3/
- Flask docs: https://flask.palletsprojects.com/
- Gemini API: https://ai.google.dev/
- CSV module: https://docs.python.org/3/library/csv.html

## Version History

v1.0 (2026-06-26)
- Initial release
- Web interface
- CSV/JSON catalog support
- Gemini API integration (optional)
- Export functionality
