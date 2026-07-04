# Quotation Automation - Complete System

A comprehensive system to automate quotation generation from product enquiries using AI and a product catalog database.

## 📋 Components

### 1. **Backend Scripts**
- `quotation_automation.py` - Core automation engine with product matching and quotation generation
- `app.py` - Flask web server for the UI

### 2. **Web Interface**
- `templates/index.html` - Interactive frontend for quotation creation
- Responsive design with real-time calculations

### 3. **Configuration**
- `config.py` - Application settings
- `requirements.txt` - Python dependencies

### 4. **Utilities**
- `run_web.ps1` - Windows startup script
- `run_web.sh` - Linux/macOS startup script

## 🚀 Quick Start

### Windows (PowerShell)
```powershell
.\run_web.ps1
```

### Linux/macOS
```bash
chmod +x run_web.sh
./run_web.sh
```

### Manual Setup
```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Then open your browser to: **http://localhost:5000**

## 📊 How It Works

### Step 1: Setup Catalog
- Upload a CSV or JSON file with your product list
- Format: `product_id`, `product_name`, `latest_price`, `unit`, `description`

### Step 2: Enter Enquiry
- Provide customer name (optional)
- Describe the product enquiry in natural language
- Example: "We need 20 pcs of Schneider 16A Socket Outlet and 50 meters of Polycab 4 sqmm wire"

### Step 3: Generate Quotation
- The system automatically:
  - Detects mentioned products
  - Extracts quantities
  - Matches against your catalog
  - Retrieves latest prices

### Step 4: Review & Edit
- Review all quotation items
- Adjust quantities and discounts as needed
- View running totals

### Step 5: Export
- Download quotation as CSV
- File includes all pricing and discount information
- Ready for customer delivery

## 🧠 AI Integration (Optional)

Set environment variables to enable Gemini API for better product detection:

```bash
set GEMINI_API_KEY=your_api_key
set GEMINI_MODEL=gemini-pro
set GEMINI_API_URL=https://api.openai.com/v1/responses
```

Without these, the system uses local fuzzy matching (still works well).

## 📁 Catalog Format

### CSV Example
```csv
product_id,product_name,latest_price,unit,description
P001,Schneider 16A Socket,320.00,pcs,Standard wall socket outlet
P002,Polycab 4 sqmm Wire,34.20,m,Single core insulated copper wire
```

### JSON Example
```json
[
  {
    "product_id": "P001",
    "product_name": "Schneider 16A Socket",
    "latest_price": 320.00,
    "unit": "pcs",
    "description": "Standard wall socket outlet"
  }
]
```

## 📤 Export Format

Generated quotations include:
- Product ID & Name
- Customer Requirements
- Quantity
- Unit & Unit Price
- **Discount %** (editable placeholder)
- Total Price
- Notes

## ⚙️ API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Main web interface |
| `/api/catalogs` | GET | List available catalogs |
| `/api/upload-catalog` | POST | Upload new catalog |
| `/api/generate-quotation` | POST | Generate quotation from enquiry |
| `/api/export-quotation` | POST | Export quotation to CSV |
| `/api/update-row` | POST | Update quotation row |

## 🛠️ Troubleshooting

### Port Already in Use
```bash
# Change port in app.py (default: 5000)
# Or kill the process using port 5000
```

### Catalog Not Loading
- Verify CSV/JSON format is correct
- Check file encoding is UTF-8
- Ensure all required columns are present

### Product Not Matching
- Try being more specific in the enquiry
- Check product names match your catalog
- Enable Gemini API for better AI matching

## 📝 Sample Enquiries

✓ "Need 50 meters of 2.5 sqmm copper wire for office wiring"
✓ "Supply 100 pcs 6A modular switches"
✓ "20 pcs Anchor Roma MCB 10A and 30 meters of cable"

## 🔐 Security Notes

- Change `SECRET_KEY` in `config.py` for production
- Set `SESSION_COOKIE_SECURE = True` for HTTPS
- Upload folder stores temporary files only
- Catalogs folder for your price lists

## 📞 Support

For issues or feature requests, check:
1. Ensure catalog format is correct
2. Verify product names in enquiry match catalog
3. Check browser console for errors (F12)
4. Review Python terminal for backend errors

## 🎯 Next Steps

- Integrate with your existing ERP/CRM
- Add email quotation delivery
- Implement user authentication
- Add quotation history tracking
- Support multiple currencies/GST calculations
