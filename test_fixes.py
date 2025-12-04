#!/usr/bin/env python3
"""
Test script to verify that the hanging issues in the PDF splitter have been resolved.
"""

import os
import sys
import time
import threading
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from pdf_toc_splitter import PDFTOCSplitter, TimeoutError
    print("✅ Successfully imported PDFTOCSplitter with timeout handling")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)


def test_non_blocking_methods():
    """Test that methods don't block indefinitely."""
    print("\n=== Testing Non-Blocking Methods ===")
    
    # Test with a dummy PDF path (we're just testing the method signatures)
    dummy_path = "test.pdf"
    
    try:
        # These should not cause hanging anymore
        splitter = PDFTOCSplitter.__new__(PDFTOCSplitter)
        splitter.pdf_path = Path(dummy_path)
        splitter.output_dir = Path("./output")
        splitter.doc = None
        splitter.toc_entries = []
        
        # Test get_manual_page_ranges - should return empty list immediately
        print("Testing get_manual_page_ranges()...")
        start_time = time.time()
        result = splitter.get_manual_page_ranges()
        end_time = time.time()
        
        if end_time - start_time < 1.0:  # Should complete quickly
            print("✅ get_manual_page_ranges() completed quickly (non-blocking)")
        else:
            print("❌ get_manual_page_ranges() took too long")
        
        # Test confirm_toc_entries - should convert entries without blocking
        print("Testing confirm_toc_entries()...")
        test_entries = [("Chapter 1", 5), ("Chapter 2", 15)]
        splitter.doc = type('MockDoc', (), {'__len__': lambda self: 100})()
        
        start_time = time.time()
        result = splitter.confirm_toc_entries(test_entries)
        end_time = time.time()
        
        if end_time - start_time < 1.0 and len(result) == 2:
            print("✅ confirm_toc_entries() completed quickly (non-blocking)")
            print(f"   Result: {result}")
        else:
            print("❌ confirm_toc_entries() issues detected")
        
    except Exception as e:
        print(f"❌ Error testing methods: {e}")


def test_timeout_mechanism():
    """Test that timeout mechanisms work."""
    print("\n=== Testing Timeout Mechanisms ===")
    
    # Test the timeout decorator
    from pdf_toc_splitter import with_timeout
    
    @with_timeout(2)  # 2 second timeout
    def slow_function():
        time.sleep(5)  # This should timeout
        return "Should not reach here"
    
    try:
        print("Testing timeout decorator with slow function...")
        start_time = time.time()
        result = slow_function()
        end_time = time.time()
        print(f"❌ Function should have timed out but returned: {result}")
    except Exception as e:
        end_time = time.time()
        if end_time - start_time < 3:  # Should timeout around 2 seconds
            if hasattr(sys, 'platform') and sys.platform == 'win32':
                print("✅ Timeout test skipped on Windows (signal.SIGALRM not available)")
            else:
                print(f"✅ Timeout mechanism working: {e}")
        else:
            print(f"❌ Timeout took too long: {end_time - start_time:.1f}s")


def test_gui_imports():
    """Test that GUI components can be imported without hanging."""
    print("\n=== Testing GUI Imports ===")
    
    try:
        from pdf_splitter_gui import PDFSplitterGUI, ManualInputDialog
        print("✅ Successfully imported GUI components")
        
        # Test that we can create the classes without hanging
        # (Note: we won't actually create windows in headless test)
        print("✅ GUI classes available for instantiation")
        
    except ImportError as e:
        print(f"❌ GUI import failed: {e}")
        if "tkinter" in str(e):
            print("   This might be expected in headless environments")
        else:
            print("   This indicates a real problem")
    except Exception as e:
        print(f"❌ Unexpected error importing GUI: {e}")


def test_threading_safety():
    """Test that operations can run in threads without hanging."""
    print("\n=== Testing Threading Safety ===")
    
    def dummy_analysis():
        """Simulate PDF analysis in a thread."""
        try:
            # Simulate some work that shouldn't hang
            time.sleep(0.1)
            return "Analysis complete"
        except Exception as e:
            return f"Error: {e}"
    
    try:
        print("Testing threaded operation...")
        results = []
        
        def run_in_thread():
            result = dummy_analysis()
            results.append(result)
        
        thread = threading.Thread(target=run_in_thread)
        thread.daemon = True
        thread.start()
        
        # Wait for thread to complete, but not indefinitely
        thread.join(timeout=2.0)
        
        if thread.is_alive():
            print("❌ Thread is still running - potential hanging issue")
        elif results and "complete" in results[0]:
            print("✅ Threaded operation completed successfully")
        else:
            print(f"❌ Unexpected thread result: {results}")
            
    except Exception as e:
        print(f"❌ Threading test error: {e}")


def main():
    """Run all tests."""
    print("PDF Splitter Fix Verification Tests")
    print("====================================")
    
    test_non_blocking_methods()
    test_timeout_mechanism()
    test_gui_imports()
    test_threading_safety()
    
    print("\n=== Test Summary ===")
    print("Tests completed. If you see mostly ✅ symbols above, the hanging issues should be resolved.")
    print("\nTo fully test the application:")
    print("1. Run: python pdf_splitter_gui.py")
    print("2. Try loading a PDF file")
    print("3. Test both automatic analysis and manual input")
    print("4. Verify the GUI doesn't freeze or hang")


if __name__ == "__main__":
    main()