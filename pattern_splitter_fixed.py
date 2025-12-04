#!/usr/bin/env python3
"""
Pattern Splitter - A tool to split PDF files containing multiple patterns
into individual PDF files named after each pattern.

This version uses pymupdf (fitz) to properly preserve images, colors, and formatting.
"""

import argparse
import os
import re
import sys
import tempfile
import requests
import shutil
from urllib.parse import urlparse, parse_qs
try:
    import fitz  # pymupdf
except ImportError:
    print("Error: pymupdf is required but not installed.")
    print("Please install it with: pip install pymupdf")
    sys.exit(1)

# Constants for text length thresholds
MIN_PATTERN_NAME_LENGTH = 3
MAX_PATTERN_NAME_LENGTH = 100
MAX_TITLE_LENGTH = 80
MIN_CAPS_TITLE_LENGTH = 5
MAX_CAPS_TITLE_LENGTH = 50
MAX_FILENAME_LENGTH = 100

# Default output directory
DEFAULT_OUTPUT_DIR = '/Users/nicoleomeara/Library/CloudStorage/GoogleDrive-nicole.a.omeara@gmail.com/.shortcut-targets-by-id/1AIiIGTbbLNB5YetWeeByl94AInhyERDg/Weaving/Pattern Splitter'


def extract_text_from_page(page):
    """
    Extract text from a PDF page, with better handling of different PDF formats.
    """
    return page.get_text()


def find_pattern_name(text):
    """
    Extract pattern name from page text.
    """
    lines = text.split('\n')
    
    # Look for pattern name - usually a longer line near the top
    for line in lines[:20]:  # Check first 20 lines
        line = line.strip()
        
        if is_likely_pattern_name(line):
            return line
    
    # Fallback: look for any reasonable line
    for line in lines:
        line = line.strip()
        if MIN_PATTERN_NAME_LENGTH <= len(line) <= MAX_PATTERN_NAME_LENGTH:
            # Skip lines that are clearly not pattern names
            if not any(skip in line.lower() for skip in ['page', 'copyright', '©', 'www.', 'photo']):
                return line
    
    return "Unnamed Pattern"


def is_likely_pattern_name(line):
    """
    Check if a line is likely to be a pattern name.
    """
    if not line:
        return False
    
    # Check length
    if len(line) < MIN_PATTERN_NAME_LENGTH or len(line) > MAX_TITLE_LENGTH:
        return False
    
    # Skip copyright/header content
    if is_copyright_or_header_line(line):
        return False
    
    # Skip lines that are just numbers/spaces
    if re.match(r'^[\d\s]+$', line):
        return False
    
    # Skip page number references
    if re.match(r'^page\s+\d+', line, re.IGNORECASE):
        return False
    
    return True


def is_copyright_or_header_line(line):
    """Check if a line contains copyright or header information."""
    copyright_indicators = [
        '©', 'copyright', 'all rights reserved', 'reproduction', 'permitted',
        'longthreadmedia', 'interweave', 'handwoven', 'weaving today', 
        'copies may be made', 'personal use only', 'unauthorized',
        'little looms', 'littlelooms'
    ]
    
    return any(indicator in line.lower() for indicator in copyright_indicators)


def clean_pattern_name(name):
    """
    Clean pattern name by removing page numbers and unwanted prefixes.
    """
    # Remove leading page numbers like "5 Pattern Name" or "12. Pattern Name"
    cleaned = re.sub(r'^\d+\.?\s*', '', name)
    
    # Remove trailing page references like "Pattern Name ... 25" or "Pattern Name    25"
    cleaned = re.sub(r'\s*[.\s]{3,}\d+$', '', cleaned)
    cleaned = re.sub(r'\s{3,}\d+$', '', cleaned)
    
    # Remove other common prefixes that might be page numbers
    cleaned = re.sub(r'^page\s*\d+\s*[:\-\.]?\s*', '', cleaned, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned if cleaned else name


def sanitize_filename(name):
    """
    Sanitize a string to be used as a filename.
    Removes or replaces characters that are not allowed in filenames.
    """
    # First clean the pattern name
    cleaned = clean_pattern_name(name)
    
    # Remove or replace problematic characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', cleaned)
    sanitized = sanitized.strip('. ')
    
    # Limit length
    if len(sanitized) > MAX_FILENAME_LENGTH:
        sanitized = sanitized[:MAX_FILENAME_LENGTH]
    
    return sanitized if sanitized else "Unnamed_Pattern"


def is_pattern_start(current_text, previous_text=None):
    """
    Determine if the current page is the start of a new pattern.
    """
    lines = current_text.split('\n')
    
    # Look for pattern indicators in the first few lines
    for line in lines[:10]:
        line = line.strip()
        if is_likely_pattern_name(line):
            return True
    
    return False


def download_from_google_drive(url):
    """
    Download a file from Google Drive and return the local path.
    """
    # Parse the Google Drive URL
    parsed = urlparse(url)
    
    # Extract file ID from different Google Drive URL formats
    file_id = None
    if 'drive.google.com' in parsed.netloc:
        if 'open' in parsed.path:
            # Format: https://drive.google.com/open?id=FILE_ID
            query_params = parse_qs(parsed.query)
            file_id = query_params.get('id', [None])[0]
        elif '/file/d/' in parsed.path:
            # Format: https://drive.google.com/file/d/FILE_ID/view
            file_id = parsed.path.split('/file/d/')[1].split('/')[0]
    
    if not file_id:
        raise ValueError("Could not extract file ID from Google Drive URL")
    
    # Create download URL
    download_url = f"https://drive.google.com/uc?id={file_id}&export=download"
    
    # Download the file
    response = requests.get(download_url)
    response.raise_for_status()
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_file.write(response.content)
    temp_file.close()
    
    return temp_file.name


def extract_toc_from_pdf(doc):
    """
    Extract table of contents patterns from the PDF.
    """
    toc_patterns = []
    
    # Check page 2 for table of contents (most common location)
    if len(doc) > 1:
        page = doc[1]  # 0-indexed, so page 2
        text = extract_text_from_page(page)
        print("Found table of contents on PDF page 2")
        
        lines = text.split('\n')
        
        # Look for specific known patterns first
        known_patterns = [
            # Add patterns here if needed for specific PDFs
        ]
        
        if known_patterns:
            toc_entries = [
                (pattern.replace(' ', r'\s+'), pattern) 
                for pattern in known_patterns
            ]
            
            for pattern_regex, clean_name in toc_entries:
                for line in lines:
                    # Look for the pattern followed by dots and page number
                    match = re.search(pattern_regex + r'.*?(\d+)', line, re.IGNORECASE | re.DOTALL)
                    if match:
                        printed_page = int(match.group(1))
                        toc_patterns.append((clean_name, printed_page))
                        print(f"Found: {clean_name} -> page {printed_page}")
                        break
        
        # If no specific patterns found, try generic pattern detection
        if not toc_patterns:
            print("No specific patterns found, trying generic TOC parsing...")
            
            # Look for general TOC patterns: 
            # Format 1: "Pattern Name by Author ... page"
            # Format 2: "Page Number PATTERN NAME" followed by "Author Name"
            # Format 3: "Page# Pattern Name" (inkle format like "2 An Inkling of Summer")
            for i, line in enumerate(lines):
                    line = line.strip()
                    
                    # Format 3: Lines starting with "page# Pattern Name" (inkle format)
                    match = re.match(r'^(\d+)\s+([A-Za-z][A-Za-z\s&\-\'\.:]{3,})', line)
                    if match:
                        page_num = int(match.group(1))
                        pattern_name = match.group(2).strip()
                        
                        # Check if pattern name continues on next line (for split entries)
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            # If next line doesn't start with a number and looks like a continuation
                            # but isn't author info, add it
                            if (not re.match(r'^\d+', next_line) and 
                                len(next_line) > 3 and 
                                not any(word in next_line.lower() for word in ['excerpted', 'from', ',']) and
                                len(next_line.split()) < 4):  # Short continuation, not author info
                                pattern_name += " " + next_line
                        
                        # Skip obvious non-patterns and very short entries
                        if (page_num > 1 and len(pattern_name) > 5 and
                            not any(skip_word in pattern_name.lower() for skip_word in 
                                   ['copyright', 'contents', 'table', 'longthreadmedia', 'customer', 'assistance', 'need help', 'excerpted'])):
                            toc_patterns.append((pattern_name, page_num))
                            print(f"Found: {pattern_name} -> page {page_num}")
                            continue
            
            for i, line in enumerate(lines):
                    line = line.strip()
                    if not line or len(line) < 10:
                        continue
                    
                    # Format 1: "Pattern Name by Author .... page#"
                    if ' by ' in line and ('.' in line or 'page' in line.lower()):
                        # Extract pattern name (everything before " by ")
                        pattern_name = line.split(' by ')[0].strip()
                        
                        # Extract page number (look for digits at the end)
                        page_match = re.search(r'(\d+)$', line)
                        if page_match and len(pattern_name) > MIN_PATTERN_NAME_LENGTH:
                            printed_page = int(page_match.group(1))
                            if printed_page > 1:  # Skip obviously wrong page numbers
                                toc_patterns.append((pattern_name, printed_page))
                                print(f"Found: {pattern_name} -> page {printed_page}")
                                continue
                    
                    # Format 2: "Page Number PATTERN NAME" followed by "Author" on next line
                    # Look for lines that start with a number followed by caps text
                    match = re.match(r'^(\d+)\s+([A-Z][A-Z\s&\-\']{5,50})', line)
                    if match and i + 1 < len(lines):
                        printed_page = int(match.group(1))
                        pattern_name = match.group(2).strip()
                        next_line = lines[i + 1].strip()
                        
                        # Skip if page number seems unrealistic for a typical publication
                        if printed_page > 50:
                            continue
                            
                        # Check if next line looks like an author name (has capital letters, reasonable length)
                        if (len(next_line) > 3 and len(next_line) < 50 and 
                            any(c.isupper() for c in next_line) and 
                            not any(skip_word in next_line.lower() for skip_word in ['page', 'contents', 'copyright'])):
                            toc_patterns.append((pattern_name, printed_page))
                            print(f"Found: {pattern_name} -> page {printed_page}")
                            continue
                    
                    # Format 3: Line ending with "page# Pattern Name" (e.g. "...2 Soft and Snuggly Blanket")
                    # Handle cases where years get concatenated with page numbers (e.g. "201914 Pattern")
                    match = re.search(r'(?:20\d{2})?(\d{1,2})\s+([A-Z][A-Za-z\s&\-\']+)$', line)
                    if match and i + 1 < len(lines):
                        printed_page = int(match.group(1))
                        pattern_name = match.group(2).strip()
                        next_line = lines[i + 1].strip()
                        
                        # Skip if page number seems unrealistic (too high for a small publication)
                        if printed_page > 50:
                            continue
                            
                        # Check if next line looks like project type (contains "project" or "loom")
                        if ('project' in next_line.lower() or 'loom' in next_line.lower() or 
                            'rigid-heddle' in next_line.lower() or 'inkle' in next_line.lower() or 'pin' in next_line.lower()):
                            toc_patterns.append((pattern_name, printed_page))
                            print(f"Found: {pattern_name} -> page {printed_page}")
                            continue
                    
                    # Format 4: Look for dot leaders (e.g., "Pattern Name ........ 15")
                    if '.' in line and re.search(r'[A-Za-z].*?\.{3,}.*?(\d+)', line):
                        match = re.search(r'^([A-Za-z][A-Za-z\s&\-\']{5,50}?)\s*\.{3,}\s*(\d+)', line)
                        if match:
                            pattern_name = match.group(1).strip()
                            printed_page = int(match.group(2))
                            
                            # Skip obvious non-patterns
                            if (printed_page > 2 and 
                                not any(skip_word in pattern_name.lower() for skip_word in 
                                       ['copyright', 'contents', 'table', 'longthreadmedia', 'customer', 'assistance'])):
                                toc_patterns.append((pattern_name, printed_page))
                                print(f"Found: {pattern_name} -> page {printed_page}")
    
    return toc_patterns


def find_pdf_page_for_printed_page(doc, target_printed_page):
    """
    Find the PDF page number that corresponds to a printed page number.
    
    Args:
        doc: fitz Document object
        target_printed_page: The printed page number to find
        
    Returns:
        PDF page number (1-indexed) or None if not found
    """
    print(f"  Searching for printed page {target_printed_page}...")
    
    for pdf_page_num in range(len(doc)):
        text = extract_text_from_page(doc[pdf_page_num])
        lines = text.strip().split('\n')
        
        # Check last 5 lines for LITTLELOOMS.COM format: "# LITTLELOOMS.COM © ..."
        for line in lines[-5:]:
            line = line.strip()
            match = re.search(rf'^(\d+)\s+LITTLELOOMS\.COM', line)
            if match:
                found_page = int(match.group(1))
                if found_page == target_printed_page:
                    print(f"  Found printed page {target_printed_page} on PDF page {pdf_page_num + 1} (LITTLELOOMS format)")
                    return pdf_page_num + 1  # Convert to 1-indexed
        
        # Check last 5 lines for LONGTHREADMEDIA format: "# LONGTHREADMEDIA.COM © ..."
        for line in lines[-5:]:
            line = line.strip()
            # Handle Unicode spaces that might appear in the text
            line_normalized = re.sub(r'[\u2000-\u206F\u2E00-\u2E7F]+', ' ', line)
            match = re.search(rf'^(\d+)\s+LONGTHREADMEDIA\.COM', line_normalized)
            if match:
                found_page = int(match.group(1))
                if found_page == target_printed_page:
                    print(f"  Found printed page {target_printed_page} on PDF page {pdf_page_num + 1} (LONGTHREADMEDIA format)")
                    return pdf_page_num + 1  # Convert to 1-indexed
        
        # Check other formats for compatibility
        for line in lines:
            line = line.strip()
            
            # Skip TOC entries (they have dots)
            if ('.......' in line or '........' in line):
                continue
                
            # Standard page formats
            if re.match(rf'^[Pp]age\s+{target_printed_page}\b', line):
                print(f"  Found printed page {target_printed_page} on PDF page {pdf_page_num + 1} (Page N format)")
                return pdf_page_num + 1
            
            if re.search(rf'\b{target_printed_page}\s+weavingtoday\.com', line):
                print(f"  Found printed page {target_printed_page} on PDF page {pdf_page_num + 1} (weavingtoday format)")
                return pdf_page_num + 1
    
    print(f"  Could not find printed page {target_printed_page}")
    return None


def move_to_processed_dir(original_file_path):
    """
    Move the original PDF file to the 'ebooks already split' directory after successful processing.
    """
    try:
        # Define the target directory
        processed_dir = '/Users/nicoleomeara/Library/CloudStorage/GoogleDrive-nicole.a.omeara@gmail.com/.shortcut-targets-by-id/1AIiIGTbbLNB5YetWeeByl94AInhyERDg/Weaving/ebooks already split'
        
        # Create the directory if it doesn't exist
        os.makedirs(processed_dir, exist_ok=True)
        
        # Get the filename from the original path
        filename = os.path.basename(original_file_path)
        target_path = os.path.join(processed_dir, filename)
        
        # Handle duplicate filenames
        counter = 1
        base_name, ext = os.path.splitext(filename)
        while os.path.exists(target_path):
            new_filename = f"{base_name}_{counter}{ext}"
            target_path = os.path.join(processed_dir, new_filename)
            counter += 1
        
        # Move the file
        shutil.move(original_file_path, target_path)
        print(f"\nMoved original file to: {target_path}")
        
    except Exception as e:
        print(f"\nWarning: Could not move original file to processed directory: {e}")
        print("The file remains in its original location.")


def split_pdf_by_toc(doc, toc_patterns, input_pdf_path, output_dir):
    """
    Split PDF based on table of contents patterns.
    """
    if not output_dir:
        output_dir = DEFAULT_OUTPUT_DIR
    
    os.makedirs(output_dir, exist_ok=True)
    
    patterns = []  # List of (pdf_start_page, pattern_name)
    
    # Add the introduction/best of section (pages 1-2 in PDF are usually intro)
    patterns.append((0, "Best of Rigid-Heddle"))
    
    for pattern_name, printed_page in toc_patterns:
        pdf_page = find_pdf_page_for_printed_page(doc, printed_page)
        if pdf_page is not None:
            # Convert from 1-indexed to 0-indexed for internal use
            patterns.append((pdf_page - 1, pattern_name))
            print(f"Pattern '{pattern_name}' starts at PDF page {pdf_page} (printed page {printed_page})")
        else:
            print(f"Warning: Could not find PDF page for printed page {printed_page} ({pattern_name})")
    
    # Sort patterns by PDF page number
    patterns.sort(key=lambda x: x[0])
    
    # Create individual PDFs
    created_files = []
    used_names = {}
    
    for i, (start_page, pattern_name) in enumerate(patterns):
        # Determine end page
        if i + 1 < len(patterns):
            end_page = patterns[i + 1][0] - 1  # End before next pattern starts
        else:
            end_page = len(doc) - 1  # Last pattern goes to end of PDF
        
        # Handle duplicate pattern names
        if pattern_name in used_names:
            used_names[pattern_name] += 1
            unique_name = f"{pattern_name}_{used_names[pattern_name]}"
        else:
            used_names[pattern_name] = 0
            unique_name = pattern_name
        
        # Create new PDF for this pattern
        new_doc = fitz.open()  # Create new empty document
        new_doc.insert_pdf(doc, from_page=start_page, to_page=end_page)  # Insert pages with full content
        
        # Save the pattern PDF
        filename = sanitize_filename(unique_name)
        output_path = os.path.join(output_dir, f"{filename}.pdf")
        new_doc.save(output_path)
        new_doc.close()
        
        created_files.append(output_path)
        print(f"Created: {output_path} (PDF pages {start_page + 1}-{end_page + 1})")
    
    # Only move original file to "ebooks already split" directory if we successfully split multiple patterns
    # (Don't move if we only created the intro/best-of file)
    if len(created_files) > 1:
        move_to_processed_dir(input_pdf_path)
    else:
        print(f"\nWarning: Only created {len(created_files)} file(s). Original file not moved to preserve it.")
    
    return created_files


def split_pdf_by_original_method(doc, input_pdf_path, output_dir, total_pages):
    """
    Original method for splitting PDFs when TOC parsing fails.
    """
    if not output_dir:
        output_dir = DEFAULT_OUTPUT_DIR
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Create patterns list
    patterns = []
    current_pattern = None
    current_start = 0
    
    for page_num in range(total_pages):
        page = doc[page_num]
        text = extract_text_from_page(page)
        
        # Check if this page starts a new pattern
        if is_pattern_start(text):
            if current_pattern:
                patterns.append((current_start, page_num - 1, current_pattern))
            
            current_pattern = find_pattern_name(text)
            current_start = page_num
    
    # Add the last pattern
    if current_pattern:
        patterns.append((current_start, total_pages - 1, current_pattern))
    
    # Create individual PDFs
    created_files = []
    
    for start_page, end_page, pattern_name in patterns:
        new_doc = fitz.open()  # Create new empty document
        new_doc.insert_pdf(doc, from_page=start_page, to_page=end_page)  # Insert pages with full content
        
        # Save the pattern PDF
        filename = sanitize_filename(pattern_name)
        output_path = os.path.join(output_dir, f"{filename}.pdf")
        new_doc.save(output_path)
        new_doc.close()
        
        created_files.append(output_path)
        print(f"Created: {output_path} (pages {start_page + 1}-{end_page + 1})")
    
    # Only move original file to "ebooks already split" directory if we successfully split multiple patterns
    if len(created_files) > 1:
        move_to_processed_dir(input_pdf_path)
    else:
        print(f"\nWarning: Only created {len(created_files)} file(s). Original file not moved to preserve it.")
    
    return created_files


def split_pdf_by_patterns(input_pdf_path, output_dir=None):
    """
    Split PDF into individual pattern files based on table of contents.
    """
    doc = fitz.open(input_pdf_path)
    total_pages = len(doc)
    
    print(f"Processing PDF with {total_pages} pages...")
    
    try:
        # Try to extract table of contents from page 2
        toc_patterns = extract_toc_from_pdf(doc)
        
        if toc_patterns:
            return split_pdf_by_toc(doc, toc_patterns, input_pdf_path, output_dir)
        else:
            # Fallback to original method
            print("No TOC patterns found, using original splitting method...")
            return split_pdf_by_original_method(doc, input_pdf_path, output_dir, total_pages)
    finally:
        doc.close()


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Split a PDF containing multiple patterns into individual PDF files.'
    )
    parser.add_argument(
        'input_pdf',
        help='Path to the input PDF file or Google Drive URL'
    )
    parser.add_argument(
        '-o', '--output-dir',
        help='Directory to save the split PDF files (defaults to Google Drive Pattern Splitter folder)'
    )
    
    args = parser.parse_args()
    
    try:
        input_path = args.input_pdf
        
        # Check if input is a Google Drive URL
        if input_path.startswith('http') and 'drive.google.com' in input_path:
            print(f"Downloading from Google Drive: {input_path}")
            input_path = download_from_google_drive(input_path)
            
            try:
                doc = fitz.open(input_path)
                
                if len(doc) == 0:
                    print("Error: The downloaded PDF appears to be empty or corrupted.")
                    return []
                
                print(f"Downloaded to: {input_path}")
                
                # If output dir not specified, use current directory for Google Drive files
                output_dir = args.output_dir or '.'
                
                created_files = split_pdf_by_patterns(input_path, output_dir)
                print(f"\nSuccessfully created {len(created_files)} pattern PDF(s).")
            finally:
                doc.close()
        else:
            created_files = split_pdf_by_patterns(input_path, args.output_dir)
            print(f"\nSuccessfully created {len(created_files)} pattern PDF(s).")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())