#!/usr/bin/env python3
"""
Test script for PDF Merger application.
This script verifies that all dependencies are installed correctly.

Author: GitHub Copilot
Date: December 2, 2025
"""

import sys
import subprocess
from pathlib import Path


def test_python_version():
    """Test if Python version is compatible."""
    print("Testing Python version...")
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"❌ Python {version.major}.{version.minor} is not supported. Please use Python 3.7+")
        return False
    else:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True


def test_dependencies():
    """Test if all required packages are installed."""
    print("\nTesting dependencies...")
    
    required_packages = {
        'PyPDF2': 'PDF manipulation',
        'reportlab': 'PDF creation',
        'tkinter': 'GUI interface (built-in)'
    }
    
    all_good = True
    
    for package, description in required_packages.items():
        try:
            if package == 'tkinter':
                import tkinter
            else:
                __import__(package)
            print(f"✅ {package} - {description}")
        except ImportError:
            print(f"❌ {package} - {description} (NOT INSTALLED)")
            all_good = False
    
    return all_good


def test_file_structure():
    """Test if all required files are present."""
    print("\nTesting file structure...")
    
    required_files = {
        'pdf_merger.py': 'Main CLI application',
        'pdf_merger_gui.py': 'GUI application',
        'requirements.txt': 'Dependencies list',
        'README.md': 'Documentation'
    }
    
    all_good = True
    
    for filename, description in required_files.items():
        file_path = Path(filename)
        if file_path.exists():
            print(f"✅ {filename} - {description}")
        else:
            print(f"❌ {filename} - {description} (MISSING)")
            all_good = False
    
    return all_good


def create_sample_pdf():
    """Create a sample PDF for testing."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create output directory if it doesn't exist
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Create sample PDFs
        for i in range(2):
            filename = output_dir / f"sample_{i+1}.pdf"
            c = canvas.Canvas(str(filename), pagesize=letter)
            c.drawString(100, 750, f"Sample PDF {i+1}")
            c.drawString(100, 720, "This is a test PDF created by the PDF Merger test script.")
            c.drawString(100, 690, "You can use this file to test the PDF merger functionality.")
            c.save()
            
        print(f"✅ Sample PDFs created in '{output_dir}' directory")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample PDFs: {e}")
        return False


def run_functionality_test():
    """Test the actual PDF merger functionality."""
    print("\nTesting PDF merger functionality...")
    
    try:
        # Import our PDF merger
        from pdf_merger import PDFMerger
        
        # Create sample PDFs first
        if not create_sample_pdf():
            return False
        
        # Test PDF merger
        merger = PDFMerger("test_output")
        
        sample_files = ["output/sample_1.pdf", "output/sample_2.pdf"]
        
        # Check if sample files exist
        for file in sample_files:
            if not Path(file).exists():
                print(f"❌ Sample file {file} not found")
                return False
        
        # Test merging
        merged_pdf, compressed_file = merger.process_pdfs(sample_files, "test_merge")
        
        # Check if output files were created
        if Path(merged_pdf).exists() and Path(compressed_file).exists():
            print("✅ PDF merging and compression successful")
            
            # Clean up test files
            Path(merged_pdf).unlink(missing_ok=True)
            Path(compressed_file).unlink(missing_ok=True)
            
            return True
        else:
            print("❌ Output files were not created")
            return False
            
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("PDF Merger Installation Test")
    print("=" * 50)
    
    tests = [
        ("Python Version", test_python_version),
        ("Dependencies", test_dependencies),
        ("File Structure", test_file_structure),
        ("Functionality", run_functionality_test)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        if not test_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED! PDF Merger is ready to use.")
        print("\nQuick start:")
        print("  CLI: python pdf_merger.py *.pdf")
        print("  GUI: python pdf_merger_gui.py")
    else:
        print("❌ SOME TESTS FAILED! Please fix the issues above.")
        print("\nTo install missing dependencies:")
        print("  pip install -r requirements.txt")
    
    print("=" * 50)


if __name__ == "__main__":
    main()