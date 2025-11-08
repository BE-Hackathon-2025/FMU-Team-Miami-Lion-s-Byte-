# Web Scraping Setup Guide

## Overview
This application now includes web scraping functionality to automatically fetch real healthcare and insurance provider data based on location.

## Prerequisites

### 1. Google Chrome
Web scraping uses Selenium with Chrome WebDriver. Install Chrome from:
- https://www.google.com/chrome/

### 2. Python Packages
All required packages are in `requirements.txt`. Key packages for web scraping:
- `selenium==4.15.2` - Browser automation
- `beautifulsoup4==4.12.2` - HTML parsing
- `webdriver-manager==4.0.1` - Automatic ChromeDriver management
- `fake-useragent==1.4.0` - User agent rotation

## Installation

### Option 1: PowerShell Script (Recommended)
```powershell
# Run in PowerShell
.\setup.ps1
```

### Option 2: Batch File
```batch
# Run in Command Prompt
setup.bat
```

### Option 3: Manual Installation
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt
```

## Running the Application

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the Flask app
python main.py
```

Then open your browser to: http://localhost:5000

## Web Scraping Features

### Healthcare Providers
The app scrapes healthcare provider data from Google Maps including:
- Provider names
- Addresses
- Phone numbers
- Websites
- Ratings
- Approximate distances

**Endpoint:** `/get-provider-graph?location=Miami`

### Insurance Providers
The app scrapes insurance provider data from web searches including:
- Provider names
- Contact information
- Websites
- Descriptions

**Endpoint:** `/insurance_providers?location=Miami`

## Caching System

To avoid excessive scraping, the app includes a caching system:
- **Cache Duration:** 2 hours
- **Automatic Updates:** Cache refreshes when expired or new location requested
- **Fallback Data:** If scraping fails, the app uses local database providers

## Important Notes

### Rate Limiting
- The app limits results to 10-15 providers per location
- Includes delays between requests to avoid being blocked
- Uses headless Chrome for better performance

### Chrome in Headless Mode
The app runs Chrome in headless mode (no visible browser window) for:
- Better performance
- Background operation
- Server compatibility

### Internet Connection
Web scraping requires a stable internet connection. If offline:
- App falls back to local database providers
- Existing cached data remains available

## Troubleshooting

### "ChromeDriver not found"
The app automatically downloads ChromeDriver. If this fails:
```powershell
pip install --upgrade webdriver-manager
```

### "Module not found" errors
Reinstall dependencies:
```powershell
pip install -r requirements.txt --force-reinstall
```

### Scraping returns no results
Check:
1. Internet connection is active
2. Chrome is installed
3. No firewall blocking Python/Chrome
4. Check logs in terminal for specific errors

### Slow performance
Web scraping takes time (5-10 seconds per location). This is normal because:
- Pages need to load
- Multiple providers are extracted
- Data is cleaned and formatted

## API Endpoints

### Get Healthcare Providers
```
GET /get-provider-graph?location=Miami
```

### Get Insurance Providers
```
GET /insurance_providers?location=Miami
```

### Get Provider Dropdowns
```
GET /providers?type=all&location=Miami
```

## Logging

The app logs scraping activities. Check terminal output for:
- Scraping progress
- Number of providers found
- Any errors encountered

## Privacy & Legal

This web scraping implementation:
- Respects robots.txt when possible
- Uses reasonable delays between requests
- Only scrapes publicly available information
- Includes proper error handling
- Falls back to local data when needed

**Note:** Always ensure compliance with the terms of service of scraped websites.

## Support

For issues or questions:
1. Check terminal logs for error messages
2. Verify all prerequisites are installed
3. Try clearing cache by restarting the app
4. Check internet connectivity

## Future Enhancements

Potential improvements:
- Real-time geocoding for accurate distances
- Additional data sources
- User reviews from multiple platforms
- Price comparison data
- Insurance coverage verification
- Advanced filtering options
