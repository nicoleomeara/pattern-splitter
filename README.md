# pattern-splitter

A Python tool to split PDF files containing multiple craft patterns into individual PDF files, automatically naming each file after the pattern it contains.

## Features

- Reads PDF files with multiple patterns
- Identifies pattern boundaries based on titles and markers
- Splits patterns into individual PDF files
- Names output files based on the pattern name

## Installation

1. Clone the repository:
```bash
git clone https://github.com/nicoleomeara/pattern-splitter.git
cd pattern-splitter
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

```bash
python pattern_splitter.py <input_pdf> [-o OUTPUT_DIR]
```

### Arguments

- `input_pdf`: Path to the PDF file containing multiple patterns
- `-o, --output-dir`: (Optional) Directory to save the split PDFs. Defaults to the same directory as the input file.

### Example

```bash
# Split patterns into the same directory as the input
python pattern_splitter.py my_patterns.pdf

# Split patterns into a specific output directory
python pattern_splitter.py my_patterns.pdf -o ./output
```

## How it Works

The tool analyzes each page of the PDF and looks for pattern boundaries using:
- Explicit markers like "Pattern:" or "Pattern Name:"
- Title-like text that ends with "Pattern" (e.g., "Cozy Blanket Pattern")
- All-caps titles that indicate a new section

Pages between pattern boundaries are grouped together and saved as individual PDF files named after the pattern.

## Requirements

- Python 3.7+
- PyPDF2
