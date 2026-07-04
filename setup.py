#!/usr/bin/env python3
"""
Quick setup script for the quotation automation system.
Run this once to set up your environment.
"""
import os
import sys
import subprocess
import platform

def run_command(cmd, description):
    """Run a command and report status."""
    print(f"\n📦 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {description} completed")
            return True
        else:
            print(f"✗ {description} failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("🚀 Quotation Automation System - Setup")
    print("=" * 60)
    
    # Detect OS
    is_windows = platform.system() == "Windows"
    
    # Check Python
    if not run_command("python --version", "Checking Python installation"):
        print("\n❌ Python not found. Please install Python 3.9+")
        sys.exit(1)
    
    # Create directories
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("catalogs", exist_ok=True)
    print("✓ Created uploads and catalogs directories")
    
    # Create virtual environment
    venv_cmd = "python -m venv venv"
    if not run_command(venv_cmd, "Creating virtual environment"):
        sys.exit(1)
    
    # Install requirements
    if is_windows:
        pip_cmd = ".\\venv\\Scripts\\pip install -r requirements.txt"
    else:
        pip_cmd = "source venv/bin/activate && pip install -r requirements.txt"
    
    if not run_command(pip_cmd, "Installing dependencies"):
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\n📝 Next steps:")
    print("\n1. Run the web application:")
    
    if is_windows:
        print("   .\\run_web.ps1")
    else:
        print("   ./run_web.sh")
    
    print("\n2. Open your browser to: http://localhost:5000")
    print("\n3. Upload your product catalog (CSV or JSON)")
    print("\n4. Start creating quotations!")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
