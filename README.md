# PDF Merger & Compressor

A Python application that merges multiple PDF files into a single document and compresses it for email sending. This tool is completely free to use and follows Python best practices.

## Features

✅ **Merge Multiple PDFs**: Combine any number of PDF files into a single document  
✅ **Email-Ready Compression**: Automatically compress merged PDFs for email attachment  
✅ **Command Line Interface**: Full CLI support with extensive options  
✅ **Graphical User Interface**: Easy-to-use GUI for non-technical users  
✅ **Smart Validation**: Validates PDF files before processing  
✅ **Detailed Logging**: Comprehensive logging for troubleshooting  
✅ **Cross-Platform**: Works on Windows, macOS, and Linux  
✅ **Free & Open Source**: No licensing fees or restrictions  

## Requirements

- Python 3.7 or higher
- Required packages (see installation)

## Installation

1. **Clone or download this repository**:
   ```bash
   git clone <repository-url>
   cd pdf-merge
   ```

2. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

   Or install packages individually:
   ```bash
   pip install PyPDF2 reportlab tqdm
   ```

## Usage

### Command Line Interface (CLI)

#### Basic Usage
```bash
# Merge multiple PDF files
python pdf_merger.py file1.pdf file2.pdf file3.pdf

# Use wildcards to select all PDFs in current directory
python pdf_merger.py *.pdf

# Merge PDFs from a specific folder
python pdf_merger.py folder/*.pdf
```

#### Advanced Options
```bash
# Specify custom output filename
python pdf_merger.py *.pdf --output "monthly_reports"

# Set custom output directory
python pdf_merger.py *.pdf --output-dir "my_output"

# Set email size limit (default: 25MB)
python pdf_merger.py *.pdf --email-limit 20

# Combine all options
python pdf_merger.py folder/*.pdf --output "Q4_reports" --output-dir "reports" --email-limit 30
```

#### Command Line Help
```bash
python pdf_merger.py --help
```

### Graphical User Interface (GUI)

For users who prefer a graphical interface:

```bash
python pdf_merger_gui.py
```

#### GUI Features:
- **Drag & Drop Support**: Add files by selecting them through file browser
- **Folder Import**: Add all PDFs from a selected folder
- **Live Log Output**: See processing progress in real-time
- **Settings Panel**: Configure output directory, filename, and email size limit
- **File Management**: Add, remove, or clear PDF files from the list

## Output

The application generates two files:

1. **Merged PDF**: A single PDF containing all input files
   - Example: `merged_pdf_20251202_143055.pdf`

2. **Compressed ZIP**: Email-ready compressed version
   - Example: `merged_pdf_20251202_143055_compressed.zip`

## Configuration

### Email Size Limits

Common email provider limits:
- **Gmail**: 25MB
- **Outlook/Hotmail**: 20MB
- **Yahoo**: 25MB
- **Corporate email**: Often 10-20MB

Adjust the `--email-limit` parameter accordingly.

### Output Directory Structure

```
output/
├── merged_pdf_20251202_143055.pdf
├── merged_pdf_20251202_143055_compressed.zip
└── pdf_merger_20251202_143055.log
```

## Examples

### Example 1: Basic Merge
```bash
python pdf_merger.py report1.pdf report2.pdf report3.pdf
```
**Output**: 
- `output/merged_pdf_[timestamp].pdf`
- `output/merged_pdf_[timestamp]_compressed.zip`

### Example 2: Custom Output
```bash
python pdf_merger.py *.pdf --output "quarterly_report" --output-dir "reports"
```
**Output**: 
- `reports/quarterly_report.pdf`
- `reports/quarterly_report_compressed.zip`

### Example 3: Large File Handling
```bash
python pdf_merger.py large_files/*.pdf --email-limit 15
```
**Result**: Warns if compressed file exceeds 15MB limit

## Troubleshooting

### Common Issues

1. **"Module not found" Error**:
   ```bash
   pip install PyPDF2 reportlab
   ```

2. **"Permission denied" Error**:
   - Ensure output directory is writable
   - Close any open PDF files before processing

3. **"Invalid PDF" Warnings**:
   - Check that files are valid PDFs
   - Some files may be corrupted or password-protected

4. **Large file sizes**:
   - Consider reducing PDF quality before merging
   - Use cloud storage services for files > 25MB

### Logging

Check the log file in the output directory for detailed information:
```
output/pdf_merger_[timestamp].log
```

### Performance Tips

- **Close other applications** when processing large files
- **Use SSD storage** for better performance
- **Process files in smaller batches** if memory is limited

## Technical Details

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| PyPDF2 | 3.0.1 | PDF manipulation and merging |
| reportlab | 4.0.4 | PDF creation and manipulation |
| tqdm | 4.66.1 | Progress bars (optional) |

### File Formats Supported

- **Input**: PDF files only
- **Output**: 
  - PDF (merged document)
  - ZIP (compressed for email)

### Compression Algorithm

- Uses ZIP compression with maximum compression level (9)
- Typical compression ratio: 10-30% size reduction
- Maintains PDF quality while reducing file size

## Development

### Code Structure

```
pdf-merge/
├── pdf_merger.py          # Main CLI application
├── pdf_merger_gui.py      # GUI application
├── requirements.txt       # Dependencies
└── README.md             # Documentation
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Style

- Follows PEP 8 Python style guide
- Type hints for better code documentation
- Comprehensive error handling and logging
- Modular design for easy maintenance

## License

This project is free and open source. You can use, modify, and distribute it freely.

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review log files for error details
3. Create an issue on the repository
4. Provide sample files if possible (remove sensitive content)

## Version History

- **v1.0.0** (December 2025)
  - Initial release
  - CLI and GUI interfaces
  - PDF merging and compression
  - Cross-platform support
  - Comprehensive logging

---

**Made with ❤️ by GitHub Copilot**