#!/usr/bin/env python3
"""
Pattern Splitter - A tool to split PDF files containing multiple patterns
into individual PDF files named after each pattern.
"""

import argparse
import os
import re
from PyPDF2 import PdfReader, PdfWriter

# Constants for text length thresholds
MIN_PATTERN_NAME_LENGTH = 3
MAX_PATTERN_NAME_LENGTH = 100
MAX_TITLE_LENGTH = 80
MIN_CAPS_TITLE_LENGTH = 5
MAX_CAPS_TITLE_LENGTH = 50
MAX_FILENAME_LENGTH = 100


def extract_text_from_page(page):
    """Extract text content from a PDF page."""
    try:
        return page.extract_text() or ""
    except Exception:
        return ""


def find_pattern_name(text):
    """
    Find the pattern name from page text.
    
    Looks for common pattern naming conventions like:
    - "Pattern: <name>"
    - "Pattern Name: <name>"
    - "<name> Pattern"
    - Lines that look like titles (short, at the start)
    
    Returns the pattern name if found, None otherwise.
    """
    if not text:
        return None
    
    lines = text.strip().split('\n')
    
    # Look for explicit pattern markers
    for line in lines[:10]:  # Check first 10 lines
        line = line.strip()
        
        # Match "Pattern: <name>" or "Pattern Name: <name>"
        match = re.match(r'^Pattern(?:\s+Name)?:\s*(.+)$', line, re.IGNORECASE)
        if match:
            return sanitize_filename(match.group(1).strip())
        
        # Match "<name> Pattern" at the start of a line
        match = re.match(r'^(.+?)\s+Pattern\s*$', line, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if MIN_PATTERN_NAME_LENGTH < len(name) < MAX_PATTERN_NAME_LENGTH:
                return sanitize_filename(name)
    
    # If no explicit pattern marker, use the first non-empty line as title
    # if it looks like a title (short, possibly capitalized)
    for line in lines[:5]:
        line = line.strip()
        if line and MIN_PATTERN_NAME_LENGTH < len(line) < MAX_TITLE_LENGTH:
            # Skip lines that look like page numbers or headers
            if re.match(r'^[\d\s]+$', line):
                continue
            if re.match(r'^page\s+\d+', line, re.IGNORECASE):
                continue
            return sanitize_filename(line)
    
    return None


def sanitize_filename(name):
    """
    Sanitize a string to be used as a filename.
    Removes or replaces characters that are not allowed in filenames.
    """
    # Remove or replace problematic characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
    sanitized = sanitized.strip('. ')
    
    # Limit length
    if len(sanitized) > MAX_FILENAME_LENGTH:
        sanitized = sanitized[:MAX_FILENAME_LENGTH]
    
    return sanitized if sanitized else "Unnamed_Pattern"


def is_pattern_start(current_text, previous_text=None):
    """
    Determine if the current page is the start of a new pattern.
    
    Heuristics used:
    - Page contains "Pattern:" or similar markers
    - Page has a clear title format that ends with "Pattern"
    - First line looks like a distinct pattern title (not a continuation)
    """
    if not current_text:
        return False
    
    lines = current_text.strip().split('\n')
    
    # Check for explicit pattern markers
    for line in lines[:10]:
        line_lower = line.strip().lower()
        if 'pattern:' in line_lower or 'pattern name:' in line_lower:
            return True
        # Match lines ending with "Pattern" (e.g., "Cozy Blanket Pattern")
        if re.match(r'^.+\s+pattern\s*$', line_lower):
            # Skip if it looks like a continuation (contains "page" followed by number)
            if re.search(r'page\s*\d+', line_lower, re.IGNORECASE):
                continue
            return True
    
    # Check if first line looks like a new pattern title
    if lines:
        first_line = lines[0].strip()
        first_line_lower = first_line.lower()
        
        # Skip if it looks like a continuation page
        if 'page' in first_line_lower and re.search(r'\d+', first_line_lower):
            return False
        if re.match(r'^(continued|cont\.)', first_line_lower):
            return False
        
        # Title-like: ends with "Pattern" in title case or all caps
        if re.match(r'^.+\s+Pattern\s*$', first_line):
            return True
        
        # Check for all-caps title that looks like a pattern name
        if first_line.isupper() and MIN_CAPS_TITLE_LENGTH < len(first_line) < MAX_CAPS_TITLE_LENGTH:
            # Only count as pattern start if it's not a generic header
            if not re.match(r'^(MATERIALS|INSTRUCTIONS|NOTES|ABBREVIATIONS)', first_line):
                return True
    
    return False


def split_pdf_by_patterns(input_pdf_path, output_dir=None):
    """
    Split a PDF containing multiple patterns into individual PDF files.
    
    Args:
        input_pdf_path: Path to the input PDF file
        output_dir: Directory to save output PDFs (default: same as input)
    
    Returns:
        List of created PDF file paths
    """
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"Input PDF not found: {input_pdf_path}")
    
    if output_dir is None:
        output_dir = os.path.dirname(input_pdf_path) or '.'
    
    os.makedirs(output_dir, exist_ok=True)
    
    reader = PdfReader(input_pdf_path)
    total_pages = len(reader.pages)
    
    if total_pages == 0:
        print("PDF has no pages.")
        return []
    
    # First pass: identify pattern boundaries
    patterns = []  # List of (start_page, pattern_name)
    
    previous_text = None
    for page_num in range(total_pages):
        page = reader.pages[page_num]
        text = extract_text_from_page(page)
        
        if page_num == 0 or is_pattern_start(text, previous_text):
            pattern_name = find_pattern_name(text)
            if pattern_name:
                patterns.append((page_num, pattern_name))
            elif page_num == 0:
                # First page should start a pattern even if no name found
                patterns.append((page_num, "Pattern_1"))
        
        previous_text = text
    
    # If no patterns found, treat the whole document as one pattern
    if not patterns:
        patterns = [(0, "Pattern_1")]
    
    # Second pass: create individual PDFs
    created_files = []
    used_names = {}
    
    for i, (start_page, pattern_name) in enumerate(patterns):
        # Determine end page
        if i + 1 < len(patterns):
            end_page = patterns[i + 1][0]
        else:
            end_page = total_pages
        
        # Handle duplicate names
        base_name = pattern_name
        if base_name in used_names:
            used_names[base_name] += 1
            pattern_name = f"{base_name}_{used_names[base_name]}"
        else:
            used_names[base_name] = 1
        
        # Create the output PDF
        writer = PdfWriter()
        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])
        
        output_path = os.path.join(output_dir, f"{pattern_name}.pdf")
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        created_files.append(output_path)
        print(f"Created: {output_path} (pages {start_page + 1}-{end_page})")
    
    return created_files


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Split a PDF containing multiple patterns into individual PDF files.'
    )
    parser.add_argument(
        'input_pdf',
        help='Path to the input PDF file containing multiple patterns'
    )
    parser.add_argument(
        '-o', '--output-dir',
        help='Output directory for split PDFs (default: same as input file)'
    )
    
    args = parser.parse_args()
    
    try:
        created_files = split_pdf_by_patterns(args.input_pdf, args.output_dir)
        print(f"\nSuccessfully created {len(created_files)} pattern PDF(s).")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
