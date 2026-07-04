# PowerShell script to run the web application

# Check if Python is available
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "Python not found. Please install Python 3.9 or later."
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
& ".\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "Installing dependencies..."
pip install -r requirements.txt

# Run the Flask app
Write-Host "Starting web application..."
Write-Host "Open your browser and go to http://localhost:5000"
python app.py
