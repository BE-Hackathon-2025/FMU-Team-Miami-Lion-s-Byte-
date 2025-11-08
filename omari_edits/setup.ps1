# PowerShell Setup Script for Healthcare App with Web Scraping

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Healthcare App Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking for Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# Check if Chrome is installed (required for Selenium)
Write-Host ""
Write-Host "Checking for Google Chrome..." -ForegroundColor Yellow
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$chromePathX86 = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

if ((Test-Path $chromePath) -or (Test-Path $chromePathX86)) {
    Write-Host "Google Chrome is installed" -ForegroundColor Green
} else {
    Write-Host "WARNING: Google Chrome not found!" -ForegroundColor Yellow
    Write-Host "Web scraping features require Chrome. Please install from https://www.google.com/chrome/" -ForegroundColor Yellow
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists, skipping..." -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Host "Virtual environment created successfully" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install requirements
Write-Host ""
Write-Host "Installing required packages..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Yellow
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Setup completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "To start the application:" -ForegroundColor Cyan
    Write-Host "1. Activate the virtual environment: .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "2. Run the app: python main.py" -ForegroundColor White
    Write-Host "3. Open your browser to: http://localhost:5000" -ForegroundColor White
    Write-Host ""
    Write-Host "Note: Web scraping will work best with a stable internet connection" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Setup encountered errors!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Please check the error messages above" -ForegroundColor Yellow
}
