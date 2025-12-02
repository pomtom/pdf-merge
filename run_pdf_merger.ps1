# PDF Merger & Compressor - PowerShell Launcher
# Author: GitHub Copilot
# Date: December 2, 2025

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "       PDF Merger & Compressor        " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a command exists
function Test-Command {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
if (-not (Test-Command "python")) {
    Write-Host "❌ ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python from https://python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Get Python version
$pythonVersion = python --version 2>&1
Write-Host "✅ Found: $pythonVersion" -ForegroundColor Green

# Check if required packages are installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import PyPDF2, reportlab" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Dependencies not found"
    }
    Write-Host "✅ All dependencies are installed" -ForegroundColor Green
}
catch {
    Write-Host "⚠️  Installing required packages..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ ERROR: Failed to install dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
}

# Test the installation
Write-Host "Testing installation..." -ForegroundColor Yellow
python test_installation.py

Write-Host ""
Write-Host "Choose how to run PDF Merger:" -ForegroundColor Cyan
Write-Host "1) Graphical Interface (GUI) - Recommended for beginners" -ForegroundColor White
Write-Host "2) Command Line Interface (CLI) - For advanced users" -ForegroundColor White
Write-Host "3) Test with sample files" -ForegroundColor White
Write-Host "4) View documentation" -ForegroundColor White
Write-Host ""

do {
    $choice = Read-Host "Enter your choice (1-4)"
    
    switch ($choice) {
        "1" {
            Write-Host "Starting GUI..." -ForegroundColor Green
            python pdf_merger_gui.py
            break
        }
        "2" {
            Write-Host ""
            Write-Host "Command Line Interface Help:" -ForegroundColor Cyan
            Write-Host "Basic usage:" -ForegroundColor White
            Write-Host "  python pdf_merger.py file1.pdf file2.pdf file3.pdf" -ForegroundColor Gray
            Write-Host "  python pdf_merger.py *.pdf" -ForegroundColor Gray
            Write-Host ""
            Write-Host "Advanced options:" -ForegroundColor White
            Write-Host "  python pdf_merger.py *.pdf --output 'my_report'" -ForegroundColor Gray
            Write-Host "  python pdf_merger.py *.pdf --email-limit 20" -ForegroundColor Gray
            Write-Host ""
            Write-Host "Opening PowerShell for command line usage..." -ForegroundColor Green
            break
        }
        "3" {
            Write-Host "Running test with sample files..." -ForegroundColor Green
            python test_installation.py
            Read-Host "Press Enter to continue"
        }
        "4" {
            Write-Host "Opening documentation..." -ForegroundColor Green
            if (Test-Path "README.md") {
                Start-Process "README.md"
            } else {
                Write-Host "README.md not found in current directory" -ForegroundColor Red
            }
            Read-Host "Press Enter to continue"
        }
        default {
            Write-Host "Invalid choice. Please enter 1, 2, 3, or 4." -ForegroundColor Red
        }
    }
} while ($choice -notin @("1", "2"))

Write-Host ""
Write-Host "Thank you for using PDF Merger & Compressor!" -ForegroundColor Cyan