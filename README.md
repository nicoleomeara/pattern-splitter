# Pattern Splitter

This tool splits PDF files containing multiple weaving patterns into individual pattern files. It uses the table of contents to identify patterns and their page numbers, then creates separate PDF files for each pattern.

**✨ NEW:** Version 2.0 now preserves all images, colors, and formatting in the split files!

**🔧 FIXED:** No more hanging or freezing! Updated with timeout protection and non-blocking operations.

## Requirements

- Python 3.6+
- pymupdf library (for full PDF content preservation)
- requests library (for Google Drive support)
- PyPDF2 library (legacy support)

## Installation

1. Clone this repository or download the files
2. Create and activate a virtual environment:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment (Mac/Linux)
source .venv/bin/activate

# Activate virtual environment (Windows)
.venv\Scripts\activate
```

3. Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Usage

### 🖱️ Easy Methods (Recommended)

**Option 1: GUI Application (Easiest and Most Reliable!)**
```bash
# First, activate your virtual environment
source .venv/bin/activate  # Mac/Linux
# OR
.venv\Scripts\activate     # Windows

# Then run the GUI
python pdf_splitter_gui.py
```
- User-friendly interface with drag-and-drop support
- No risk of hanging or freezing
- Manual input option if automatic detection fails
- Real-time progress feedback

**Note:** Always activate your virtual environment first to ensure all dependencies are available.

**Option 2: Interactive Script**
```bash
# Double-click run_pattern_splitter.sh (Mac/Linux) or run_pattern_splitter.bat (Windows)
# Or run from terminal:
./run_pattern_splitter.sh
```

**Option 3: Drag & Drop**
```bash
# Drag your PDF file onto run_pattern_splitter.sh in Finder
# The script will automatically process it
```

### ⌨️ Command Line Methods

```bash
# Recommended: Use the new version with image preservation
.venv/bin/python pattern_splitter_fixed.py input.pdf

# Or activate virtual environment first
source .venv/bin/activate
python pattern_splitter_fixed.py input.pdf

# Specify a different output directory
python pattern_splitter_fixed.py input.pdf -o /path/to/output/directory

# Google Drive URLs (also outputs to Pattern Splitter folder by default)
python pattern_splitter_fixed.py "https://drive.google.com/file/d/FILE_ID/view?usp=sharing"

# Legacy version (text only, no images)
.venv/bin/python pattern_splitter.py input.pdf
```

**Note:** By default, all split patterns are saved to your Google Drive Pattern Splitter folder. You only need to specify `-o` if you want to save them somewhere else.

## Versions

### 🆕 Version 2.0 (pattern_splitter_fixed.py) - **RECOMMENDED**
- **Full image and color preservation** using pymupdf library
- Maintains original PDF formatting, fonts, and layout
- All images appear in full color in split files
- Same functionality as original version
- Requires `pymupdf` package

### 📜 Legacy Version (pattern_splitter.py)
- Text-only extraction using PyPDF2
- Images and colors are lost in split files
- Lighter weight, fewer dependencies
- Still functional for text-based patterns

---

## Features

- 🔍 **Smart Detection**: Automatically finds table of contents in PDF files
- 📖 **Pattern Recognition**: Identifies individual patterns by their page numbers
- 📁 **Clean Organization**: Creates separate PDF files with descriptive names
- 🎯 **Accurate Splitting**: Handles various PDF layouts and page numbering schemes
- 🖼️ **Image Preservation**: Full-color images and formatting preserved in split files
- 🎨 **Complete Fidelity**: Maintains original colors, fonts, and layout
- 🚀 **Easy to Use**: Simple command-line interface
- 🌐 **Google Drive Support**: Works with shared Google Drive links
- 📚 **Multiple Formats**: Supports LITTLELOOMS, LONGTHREADMEDIA, inkle, and other formats

## How It Works

1. **Table of Contents Detection**: The script searches the first few pages of the PDF for a table of contents
2. **Pattern Identification**: It looks for entries that match the pattern "Pattern Name by Author ... Page Number"
3. **Page Number Mapping**: Maps the printed page numbers from the TOC to actual PDF page numbers
4. **File Creation**: Creates individual PDF files for each pattern with descriptive names

## Example Output

For a PDF containing multiple weaving patterns, the script will create files like:

- `Embellished Scarves.pdf`
- `V-Shaped Scarves.pdf`
- `Ombré Silk Shawl.pdf`
- `Log Cabin Ruana.pdf`
- `Soysilk Top.pdf`
- `Waffle-Weave Table Runner.pdf`
- etc.

## Troubleshooting

### Application Freezing or Hanging (FIXED! ✅)
**Previous Issue**: The application used to hang during PDF analysis or manual input.
**Solution**: Updated to use non-blocking operations and timeout mechanisms.

- **GUI Version**: Use `python pdf_splitter_gui.py` for the best experience
- **Timeout Protection**: PDF analysis will timeout after 30 seconds if the file is too complex
- **Manual Input**: Now handled entirely through GUI dialogs (no terminal input required)
- **Error Recovery**: Better error messages when operations fail or timeout

### Missing Dependencies
If you get import errors:
```bash
# For the new version (recommended)
.venv/bin/pip install pymupdf requests

# For the legacy version
pip install --upgrade PyPDF2 requests
```

### Pattern Not Found
If a pattern isn't being split correctly:
- Check that the PDF has a clear table of contents
- Ensure page numbers in the TOC match the actual page numbers in the PDF
- Verify that pattern titles follow the "Name by Author" format
- **NEW**: If automatic detection fails, use "Manual Input" in the GUI

### File Permission Errors
- Make sure you have write permissions to the output directory
- Close the PDF file in other applications before running the script

### Images Missing or Black & White?
Use the new version for full image and color preservation:
```bash
.venv/bin/python pattern_splitter_fixed.py input.pdf
```

### GUI Not Responding?
- **Fixed!** The GUI now runs all heavy operations in background threads
- If analysis takes too long, it will timeout and suggest manual input
- Use the "Manual Input" button if automatic detection fails

### Need Help?
Run the test script to verify everything is working:
```bash
python test_fixes.py
```

For command-line help:
```bash
# New version
python pattern_splitter_fixed.py -h

# Legacy version
.venv/bin/python pattern_splitter.py -h
```

---

## 🏷️ Pattern Renamer Tool

The Pattern Renamer is a companion tool that automatically renames PDF pattern files based on their internal titles.

### Features

- **Batch Processing**: Select and analyze multiple PDF files at once
- **Smart Title Detection**: Automatically extracts pattern names from PDF content
- **Manual Override**: Double-click to edit any proposed filename
- **Conflict Detection**: Warns about filename conflicts before renaming
- **Safe Operation**: Preview all changes before applying them
- **Export Results**: Save rename lists to CSV for record keeping

### Usage

**GUI Version (Recommended)**:
```bash
# First, activate your virtual environment
source .venv/bin/activate  # Mac/Linux
# OR
.venv\Scripts\activate     # Windows

# Then run the renamer GUI
python pattern_renamer_gui.py
```

**Or use the launcher script**:
```bash
./run_pattern_renamer.sh
```

### How It Works

1. **Title Extraction**: Searches PDF metadata and content for pattern titles
2. **Smart Recognition**: Looks for common pattern naming conventions
3. **Filename Sanitization**: Cleans titles to be filesystem-safe
4. **Preview & Edit**: Shows proposed names before any changes
5. **Batch Rename**: Safely renames multiple files at once

---

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.
