@echo off
echo ========================================
echo       PDF Merger & Compressor
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking dependencies...
python -c "import PyPDF2, reportlab" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Ask user which interface to use
echo.
echo Choose interface:
echo 1) Graphical Interface (GUI)
echo 2) Command Line Interface
echo.
set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" (
    echo Starting GUI...
    python pdf_merger_gui.py
) else if "%choice%"=="2" (
    echo.
    echo Usage examples:
    echo   For current directory PDFs: python pdf_merger.py *.pdf
    echo   For specific files: python pdf_merger.py file1.pdf file2.pdf
    echo.
    echo Opening command prompt...
    cmd /k
) else (
    echo Invalid choice. Starting GUI...
    python pdf_merger_gui.py
)

pause