#!/usr/bin/env python3
"""
PDF Merger and Compressor
A Python application to merge multiple PDF files and compress them for email sending.

Author: GitHub Copilot
Date: December 2, 2025
"""

import os
import sys
import logging
import argparse
import zipfile
from pathlib import Path
from typing import List, Optional
from datetime import datetime

try:
    import PyPDF2
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except ImportError as e:
    print(f"Required package not installed: {e}")
    print("Please install required packages using:")
    print("pip install PyPDF2 reportlab")
    sys.exit(1)


class PDFMerger:
    """
    A class to handle PDF merging and compression operations.
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the PDF Merger.
        
        Args:
            output_dir (str): Directory to save output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self._setup_logging()
        
    def _setup_logging(self):
        """Set up logging configuration."""
        log_file = self.output_dir / f"pdf_merger_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def validate_pdf_files(self, pdf_paths: List[str]) -> List[str]:
        """
        Validate that all provided files are valid PDFs.
        
        Args:
            pdf_paths (List[str]): List of PDF file paths
            
        Returns:
            List[str]: List of valid PDF file paths
            
        Raises:
            ValueError: If no valid PDF files are found
        """
        valid_files = []
        
        for pdf_path in pdf_paths:
            path = Path(pdf_path)
            
            if not path.exists():
                self.logger.warning(f"File not found: {pdf_path}")
                continue
                
            if not path.suffix.lower() == '.pdf':
                self.logger.warning(f"Not a PDF file: {pdf_path}")
                continue
                
            try:
                # Test if file can be opened as PDF
                with open(path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    if len(reader.pages) == 0:
                        self.logger.warning(f"Empty PDF file: {pdf_path}")
                        continue
                        
                valid_files.append(str(path.absolute()))
                self.logger.info(f"Valid PDF file: {pdf_path} ({len(reader.pages)} pages)")
                
            except Exception as e:
                self.logger.warning(f"Invalid PDF file {pdf_path}: {e}")
                continue
                
        if not valid_files:
            raise ValueError("No valid PDF files found")
            
        return valid_files
        
    def merge_pdfs(self, pdf_paths: List[str], output_filename: Optional[str] = None) -> str:
        """
        Merge multiple PDF files into a single PDF.
        
        Args:
            pdf_paths (List[str]): List of PDF file paths to merge
            output_filename (Optional[str]): Name for the output file
            
        Returns:
            str: Path to the merged PDF file
            
        Raises:
            ValueError: If no valid PDF files are provided
            Exception: If merging fails
        """
        # Validate input files
        valid_files = self.validate_pdf_files(pdf_paths)
        
        # Generate output filename if not provided
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"merged_pdf_{timestamp}.pdf"
            
        output_path = self.output_dir / output_filename
        
        try:
            # Create PDF merger object
            merger = PyPDF2.PdfMerger()
            
            total_pages = 0
            
            # Add each PDF to the merger
            for pdf_path in valid_files:
                self.logger.info(f"Adding PDF: {pdf_path}")
                
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    page_count = len(reader.pages)
                    total_pages += page_count
                    
                    merger.append(file)
                    self.logger.info(f"Added {page_count} pages from {pdf_path}")
            
            # Write merged PDF
            with open(output_path, 'wb') as output_file:
                merger.write(output_file)
                
            merger.close()
            
            # Get file size
            file_size = output_path.stat().st_size / (1024 * 1024)  # Size in MB
            
            self.logger.info(f"Successfully merged {len(valid_files)} PDFs")
            self.logger.info(f"Total pages: {total_pages}")
            self.logger.info(f"Output file: {output_path}")
            self.logger.info(f"File size: {file_size:.2f} MB")
            
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Failed to merge PDFs: {e}")
            raise
            
    def compress_for_email(self, file_path: str, max_size_mb: float = 25.0) -> str:
        """
        Compress the merged PDF file for email sending.
        
        Args:
            file_path (str): Path to the PDF file to compress
            max_size_mb (float): Maximum size in MB (default: 25MB for email)
            
        Returns:
            str: Path to the compressed file (ZIP format)
        """
        file_path = Path(file_path)
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        
        # Generate zip filename
        zip_filename = file_path.stem + "_compressed.zip"
        zip_path = self.output_dir / zip_filename
        
        try:
            # Create ZIP file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
                zipf.write(file_path, file_path.name)
                
            # Get compressed size
            compressed_size_mb = zip_path.stat().st_size / (1024 * 1024)
            compression_ratio = (1 - compressed_size_mb / file_size_mb) * 100
            
            self.logger.info(f"Original size: {file_size_mb:.2f} MB")
            self.logger.info(f"Compressed size: {compressed_size_mb:.2f} MB")
            self.logger.info(f"Compression ratio: {compression_ratio:.1f}%")
            
            if compressed_size_mb > max_size_mb:
                self.logger.warning(f"Compressed file ({compressed_size_mb:.2f} MB) exceeds email limit ({max_size_mb} MB)")
                self.logger.warning("Consider using a file sharing service for large files")
            else:
                self.logger.info("File is ready for email attachment")
                
            return str(zip_path)
            
        except Exception as e:
            self.logger.error(f"Failed to compress file: {e}")
            raise
            
    def process_pdfs(self, pdf_paths: List[str], output_name: Optional[str] = None, 
                    email_size_limit: float = 25.0) -> tuple[str, str]:
        """
        Complete workflow: merge PDFs and compress for email.
        
        Args:
            pdf_paths (List[str]): List of PDF file paths to merge
            output_name (Optional[str]): Name for the output file
            email_size_limit (float): Maximum size in MB for email
            
        Returns:
            tuple[str, str]: Paths to merged PDF and compressed ZIP file
        """
        self.logger.info("Starting PDF processing workflow")
        
        # Merge PDFs
        merged_pdf = self.merge_pdfs(pdf_paths, output_name)
        
        # Compress for email
        compressed_file = self.compress_for_email(merged_pdf, email_size_limit)
        
        self.logger.info("PDF processing completed successfully")
        return merged_pdf, compressed_file


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Merge multiple PDF files and compress them for email sending",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python pdf_merger.py file1.pdf file2.pdf file3.pdf
    python pdf_merger.py *.pdf --output "monthly_reports.pdf"
    python pdf_merger.py folder/*.pdf --email-limit 20
        """
    )
    
    parser.add_argument(
        'pdf_files', 
        nargs='+', 
        help='PDF files to merge (supports wildcards)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output filename for merged PDF (without extension)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Directory to save output files (default: output)'
    )
    
    parser.add_argument(
        '--email-limit',
        type=float,
        default=25.0,
        help='Maximum file size in MB for email (default: 25.0)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='PDF Merger 1.0.0'
    )
    
    args = parser.parse_args()
    
    try:
        # Create PDF merger instance
        merger = PDFMerger(args.output_dir)
        
        # Process PDFs
        merged_pdf, compressed_file = merger.process_pdfs(
            args.pdf_files,
            args.output,
            args.email_limit
        )
        
        print("\n" + "="*60)
        print("PDF PROCESSING COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Merged PDF: {merged_pdf}")
        print(f"Compressed file: {compressed_file}")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
        
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()