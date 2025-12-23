#!/usr/bin/env python3
"""
PDF Table of Contents Splitter

A lightweight tool that reads a table of contents in a PDF file, automatically
detects page numbers, and splits the PDF by page ranges. Can also accept manual
page range input as a fallback.

Features:
- Automatic TOC extraction from PDFs
- Manual page range input option
- Smart filename sanitization
- Preserves all PDF content (images, formatting, etc.)
- Easy-to-use interactive interface
"""

import argparse
import os
import re
import sys
import json
import signal
import threading
from pathlib import Path
from typing import List, Tuple, Optional, Dict

try:
    import fitz  # pymupdf
except ImportError:
    print("Error: pymupdf is required but not installed.")
    print("Please install it with: pip install pymupdf")
    sys.exit(1)


class TimeoutError(Exception):
    """Exception raised when an operation times out."""
    pass


def timeout_handler(signum, frame):
    """Handle timeout signal."""
    raise TimeoutError("Operation timed out")


def with_timeout(timeout_seconds=30):
    """Decorator to add timeout to functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Set up timeout (Unix only)
            if hasattr(signal, 'SIGALRM'):
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout_seconds)
                
                try:
                    result = func(*args, **kwargs)
                    signal.alarm(0)  # Cancel alarm
                    return result
                except TimeoutError:
                    print(f"Operation timed out after {timeout_seconds} seconds")
                    raise
                finally:
                    signal.signal(signal.SIGALRM, old_handler)
            else:
                # Windows doesn't have SIGALRM, just run normally
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


class PDFTOCSplitter:
    def __init__(self, pdf_path: str, output_dir: Optional[str] = None):
        """Initialize the PDF TOC Splitter.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save split files (defaults to pdf location)
        """
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir) if output_dir else self.pdf_path.parent / "split_pdfs"
        self.doc = None
        self.toc_entries = []
        
    def __enter__(self):
        """Context manager entry."""
        self.doc = fitz.open(str(self.pdf_path))
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.doc:
            self.doc.close()
    
    def extract_toc_from_pdf(self) -> List[Tuple[str, int]]:
        """Extract table of contents entries from the PDF.
        
        Returns:
            List of tuples: (section_name, page_number)
        """
        if not self.doc:
            raise RuntimeError("PDF document not loaded")
        
        print("Searching for table of contents...")
        toc_entries = []
        
        # Try to use built-in TOC first
        built_in_toc = self.doc.get_toc()
        if built_in_toc:
            print("Found built-in table of contents!")
            for level, title, page in built_in_toc:
                if title.strip() and page > 0:
                    toc_entries.append((title.strip(), page))
            return toc_entries
        
        # Search for TOC in first few pages
        for page_num in range(min(5, len(self.doc))):
            text = self.doc[page_num].get_text()
            entries = self._parse_text_toc(text, page_num + 1)
            if entries:
                print(f"Found table of contents on page {page_num + 1}")
                toc_entries.extend(entries)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_entries = []
        for entry in toc_entries:
            if entry not in seen:
                seen.add(entry)
                unique_entries.append(entry)
        
        return unique_entries
    
    def _parse_text_toc(self, text: str, page_num: int) -> List[Tuple[str, int]]:
        """Parse table of contents from page text.
        
        Args:
            text: Page text to parse
            page_num: Current page number (for context)
            
        Returns:
            List of (section_name, page_number) tuples
        """
        entries = []
        lines = text.split('\n')
        
        # Skip if this doesn't look like a TOC
        if not self._looks_like_toc(text):
            return entries
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Pattern 1: "Chapter Name ... Page Number"
            match = re.search(r'^(.+?)[\.\s]{3,}(\d+)$', line)
            if match:
                title, page = match.groups()
                title = title.strip()
                if self._is_valid_title(title):
                    entries.append((title, int(page)))
                    continue
            
            # Pattern 2: "Chapter Name    Page Number" (multiple spaces)
            match = re.search(r'^(.+?)\s{4,}(\d+)$', line)
            if match:
                title, page = match.groups()
                title = title.strip()
                if self._is_valid_title(title):
                    entries.append((title, int(page)))
                    continue
            
            # Pattern 3: "Page Number Chapter Name"
            match = re.match(r'^(\d+)\s+(.+)', line)
            if match:
                page, title = match.groups()
                title = title.strip()
                if self._is_valid_title(title) and int(page) > page_num:
                    entries.append((title, int(page)))
                    continue
            
            # Pattern 4: "Chapter Number. Chapter Name ... Page"
            match = re.search(r'^(\d+\.?\s+)?(.+?)[\.\s]{3,}(\d+)$', line)
            if match:
                _, title, page = match.groups()
                title = title.strip()
                if self._is_valid_title(title):
                    entries.append((title, int(page)))
        
        return entries
    
    def _looks_like_toc(self, text: str) -> bool:
        """Check if text looks like a table of contents."""
        lower_text = text.lower()
        
        # Common TOC indicators
        toc_indicators = [
            'contents', 'table of contents', 'index', 'chapter'
        ]
        
        # Look for page number patterns
        page_patterns = [
            r'\.{3,}\s*\d+',  # dots followed by numbers
            r'\s{4,}\d+$',    # multiple spaces followed by numbers
            r'^\d+\s+\w',     # line starting with number and text
        ]
        
        has_indicator = any(indicator in lower_text for indicator in toc_indicators)
        has_page_pattern = any(re.search(pattern, text, re.MULTILINE) for pattern in page_patterns)
        
        return has_indicator or has_page_pattern
    
    def _is_valid_title(self, title: str) -> bool:
        """Check if a title is valid for a TOC entry."""
        if len(title) < 3 or len(title) > 100:
            return False
        
        # Skip obviously invalid entries
        skip_words = [
            'copyright', 'page', 'contents', 'table', 'index', '©', 
            'all rights reserved', 'www.', 'http', '.com'
        ]
        
        lower_title = title.lower()
        return not any(skip in lower_title for skip in skip_words)
    
    def get_manual_page_ranges(self) -> List[Tuple[str, int, int]]:
        """Get page ranges from user input (non-interactive version for GUI use).
        
        This method is now non-blocking and should be called from GUI dialogs.
        Returns empty list - GUI should handle input collection.
        
        Returns:
            List of (section_name, start_page, end_page) tuples
        """
        # This method is now handled by the GUI - return empty list
        return []
    
    def validate_page_range(self, start: int, end: int) -> tuple[bool, str]:
        """Validate a page range.
        
        Args:
            start: Start page number
            end: End page number
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if start > end:
            return False, f"Start page {start} cannot be greater than end page {end}"
        elif end > len(self.doc):
            return False, f"End page {end} exceeds PDF length ({len(self.doc)} pages)"
        elif start < 1:
            return False, f"Start page {start} must be at least 1"
        return True, ""
    
    def _show_manual_input_help(self):
        """Show help for manual input format."""
        print("\nManual input examples:")
        print("  'Introduction: 1-5'")
        print("  'Chapter 1 - Getting Started: 6-20'")
        print("  'Appendix A: 45-50'")
        print("  'Bibliography: 51-55'")
        print("\nNotes:")
        print("- Page numbers should be the actual PDF page numbers")
        print("- Ranges can overlap if needed")
        print("- Section names will be used for filenames")
    
    def confirm_toc_entries(self, entries: List[Tuple[str, int]]) -> List[Tuple[str, int, int]]:
        """Convert TOC entries to page ranges (non-interactive version for GUI use).
        
        Args:
            entries: List of (title, page) tuples from TOC extraction
            
        Returns:
            List of (title, start_page, end_page) tuples
        """
        if not entries:
            return []
        
        # Auto-convert to ranges (each section goes to next section's start - 1)
        ranges = []
        for i, (title, page) in enumerate(entries):
            start_page = page
            end_page = entries[i + 1][1] - 1 if i + 1 < len(entries) else len(self.doc)
            ranges.append((title, start_page, end_page))
        return ranges
    
    def edit_toc_entries(self, entries: List[Tuple[str, int]], edits: Dict[int, dict]) -> List[Tuple[str, int, int]]:
        """Apply edits to TOC entries (non-blocking version for GUI use).
        
        Args:
            entries: Original list of (title, page) tuples
            edits: Dictionary where key is entry index, value is dict with 'action', 'title', 'page'
                  e.g., {0: {'action': 'rename', 'title': 'New Name'}, 1: {'action': 'skip'}}
        
        Returns:
            List of (title, start_page, end_page) tuples
        """
        edited_entries = []
        for i, (title, page) in enumerate(entries):
            if i in edits:
                edit = edits[i]
                action = edit.get('action', 'keep')
                
                if action == 'skip':
                    continue
                elif action == 'rename':
                    new_title = edit.get('title', title).strip()
                    edited_entries.append((new_title if new_title else title, page))
                elif action == 'change_page':
                    new_page = edit.get('page', page)
                    if 1 <= new_page <= len(self.doc):
                        edited_entries.append((title, new_page))
                    else:
                        edited_entries.append((title, page))  # Keep original if invalid
                else:  # 'keep' or unknown action
                    edited_entries.append((title, page))
            else:
                edited_entries.append((title, page))  # Keep as-is
        
        # Convert to ranges
        ranges = []
        for i, (title, page) in enumerate(edited_entries):
            start_page = page
            end_page = edited_entries[i + 1][1] - 1 if i + 1 < len(edited_entries) else len(self.doc)
            ranges.append((title, start_page, end_page))
        
        return ranges
    
    def clean_pattern_name(self, name: str) -> str:
        """Clean pattern name by removing page numbers and unwanted prefixes."""
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
    
    def sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use as a filename."""
        # First clean the pattern name
        cleaned = self.clean_pattern_name(name)
        
        # Remove/replace problematic characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', cleaned)
        sanitized = re.sub(r'\s+', ' ', sanitized)  # Normalize spaces
        sanitized = sanitized.strip('. ')
        
        # Limit length
        if len(sanitized) > 100:
            sanitized = sanitized[:100].rsplit(' ', 1)[0]  # Break at word boundary
        
        return sanitized if sanitized else "Unnamed_Section"
    
    def split_pdf(self, ranges: List[Tuple[str, int, int]]) -> List[str]:
        """Split PDF into separate files based on page ranges.
        
        Args:
            ranges: List of (section_name, start_page, end_page) tuples
            
        Returns:
            List of created file paths
        """
        if not ranges:
            print("No page ranges to split")
            return []
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        created_files = []
        used_names = set()
        
        for section_name, start_page, end_page in ranges:
            # Handle duplicate names
            base_name = self.sanitize_filename(section_name)
            filename = base_name
            counter = 1
            while filename in used_names:
                filename = f"{base_name}_{counter}"
                counter += 1
            used_names.add(filename)
            
            # Create new PDF
            new_doc = fitz.open()
            new_doc.insert_pdf(self.doc, from_page=start_page-1, to_page=end_page-1)
            
            # Save file
            output_path = self.output_dir / f"{filename}.pdf"
            new_doc.save(str(output_path))
            new_doc.close()
            
            created_files.append(str(output_path))
            print(f"Created: {output_path.name} (pages {start_page}-{end_page})")
        
        return created_files
    
    def run_interactive(self) -> List[str]:
        """Run the splitter in interactive mode (CLI only).
        
        This method should only be used from command line, not GUI.
        GUI should use extract_toc_from_pdf() and split_pdf() directly.
        """
        print(f"PDF TOC Splitter")
        print(f"Processing: {self.pdf_path.name}")
        print(f"Total pages: {len(self.doc)}")
        print(f"Output directory: {self.output_dir}")
        
        # Try automatic TOC extraction
        toc_entries = self.extract_toc_from_pdf()
        
        if toc_entries:
            print(f"\nAutomatically found {len(toc_entries)} TOC entries")
            ranges = self.confirm_toc_entries(toc_entries)
        else:
            print("\nNo table of contents found automatically")
            ranges = []
        
        # For CLI usage, fallback to manual input if needed
        if not ranges and hasattr(sys, 'ps1'):
            # Only do manual input if running interactively
            try:
                choice = input("\nWould you like to manually specify page ranges? (y/n): ").lower().strip()
                if choice in ['y', 'yes']:
                    # This would need to be implemented for CLI use
                    print("Manual input not implemented in non-blocking version.")
                    print("Please use the GUI for manual input.")
            except (EOFError, KeyboardInterrupt):
                print("\nExiting without splitting")
                return []
        
        # Split the PDF
        if ranges:
            return self.split_pdf(ranges)
        else:
            print("No page ranges specified")
            return []


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Split PDF files based on table of contents or manual page ranges',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf
  %(prog)s document.pdf -o ./output
  %(prog)s document.pdf --manual
        """
    )
    
    parser.add_argument('pdf_file', help='PDF file to split')
    parser.add_argument('-o', '--output-dir', help='Output directory for split files')
    parser.add_argument('--manual', action='store_true', 
                       help='Skip automatic TOC detection, go straight to manual input')
    parser.add_argument('--quiet', action='store_true',
                       help='Minimal output (for scripting)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_file):
        print(f"Error: File '{args.pdf_file}' not found")
        return 1
    
    try:
        with PDFTOCSplitter(args.pdf_file, args.output_dir) as splitter:
            if args.manual:
                # Skip automatic detection - CLI manual input not supported in non-blocking version
                print("Manual input mode requires the GUI interface.")
                print("Please run: python pdf_splitter_gui.py")
                return 1
            else:
                # Run interactive mode
                created_files = splitter.run_interactive()
            
            if not args.quiet:
                print(f"\nCompleted! Created {len(created_files)} files.")
                if created_files:
                    print(f"Files saved to: {splitter.output_dir}")
            
            return 0 if created_files else 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())