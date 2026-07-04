#!/bin/bash

# Bash script to run the web application (for Linux/macOS)

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Please install Python 3.9 or later."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the Flask app
echo "Starting web application..."
echo "Open your browser and go to http://localhost:5000"
python3 app.py
