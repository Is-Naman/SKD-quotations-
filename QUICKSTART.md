# Quick Start Guide

## 🎯 One-Time Setup

### Option 1: Automatic Setup (Recommended)
```powershell
python setup.py
```

### Option 2: Manual Setup
```powershell
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
venv\Scripts\activate

# 3. Install Flask
pip install -r requirements.txt

# 4. Run the app
python app.py
```

## 🚀 Running the Application

### Windows PowerShell
```powershell
.\run_web.ps1
```

### Command Prompt
```cmd
venv\Scripts\activate
python app.py
```

### Linux/macOS
```bash
source venv/bin/activate
python app.py
```

## 💻 Access the Web App

Open your browser and go to:
```
http://localhost:5000
```

## 📋 First Use Checklist

- [ ] Created virtual environment
- [ ] Installed dependencies
- [ ] Started Flask web server
- [ ] Opened http://localhost:5000 in browser
- [ ] Uploaded your product catalog
- [ ] Created your first quotation

## 📁 Prepare Your Catalog

Convert your price lists to CSV format:

### Simple CSV Format
```csv
product_id,product_name,latest_price,unit,description
P001,Schneider 16A Socket,320,pcs,Wall socket
P002,Polycab 4 sqmm Wire,34.20,m,Copper wire
```

### Using Excel
1. Open your price list in Excel
2. Add headers: product_id, product_name, latest_price, unit, description
3. Save as CSV (Comma Separated Values)

## ⚡ Usage Steps

1. **Upload Catalog** - Add your latest price list
2. **Enter Enquiry** - Describe what the customer needs
3. **Generate Quote** - System automatically detects products
4. **Review & Edit** - Adjust quantities and discounts
5. **Export** - Download as CSV

## 🔧 Troubleshooting

### "Port 5000 already in use"
Change the port in `app.py`:
```python
app.run(debug=True, host="0.0.0.0", port=5001)  # Change 5000 to 5001
```

### "Module not found"
Make sure virtual environment is activated:
```powershell
venv\Scripts\activate
```

### "Catalog not uploading"
Check:
- File format is CSV or JSON
- File encoding is UTF-8
- Headers match: product_id, product_name, latest_price, unit, description

## 💡 Tips

- Save enquiry details for future reference
- Keep catalog updated with latest prices
- Test with sample enquiries first
- Export quotations regularly

## 🎓 Example Commands

### Command Line Usage (Without Web UI)
```bash
python quotation_automation.py \
  --catalog product_catalog_sample.csv \
  --enquiry "Need 20 pcs Schneider 16A Socket" \
  --output quotation.csv
```

### Using Enquiry File
```bash
python quotation_automation.py \
  --catalog product_catalog_sample.csv \
  --enquiry-file sample_enquiry.txt \
  --output quotation.csv
```

## 📞 Need Help?

Check the main README.md for:
- API endpoints
- Catalog format details
- AI integration setup
- Production deployment notes

Good luck! 🎉
