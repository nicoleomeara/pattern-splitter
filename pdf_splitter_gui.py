#!/usr/bin/env python3
"""
PDF TOC Splitter - GUI Version

A user-friendly graphical interface for splitting PDFs based on table of contents.
This version provides drag-and-drop support and visual feedback.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
import shutil
from pathlib import Path

# Import our PDF splitter functionality
try:
    from pdf_toc_splitter import PDFTOCSplitter, TimeoutError
except ImportError:
    # If running as standalone, add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from pdf_toc_splitter import PDFTOCSplitter, TimeoutError

try:
    import fitz  # pymupdf
except ImportError:
    print("pymupdf is required but not installed.")
    print("Please install it with: pip install pymupdf")
    print("Or use the launcher scripts which auto-install dependencies.")
    
    # Try to show error in GUI if tkinter is available
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        messagebox.showerror("Missing Dependency", 
                            "pymupdf is required but not installed.\n"
                            "Please install it with: pip install pymupdf\n"
                            "Or use the launcher scripts which auto-install dependencies.")
        root.destroy()
    except:
        pass  # If tkinter is not available, just print to console
    
    sys.exit(1)


class PDFSplitterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Table of Contents Splitter")
        self.root.geometry("900x800")
        self.root.minsize(700, 600)
        
        # Variables
        self.pdf_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        # Set default output directory to Google Drive Pattern Splitter folder
        self.output_dir.set('/Users/nicoleomeara/Library/CloudStorage/GoogleDrive-nicole.a.omeara@gmail.com/.shortcut-targets-by-id/1AIiIGTbbLNB5YetWeeByl94AInhyERDg/Weaving/Pattern Splitter')
        self.toc_entries = []
        self.page_ranges = []
        
        # Setup GUI
        self.setup_gui()
        
        # Setup drag and drop
        self.setup_drag_drop()
    
    def setup_gui(self):
        """Setup the GUI layout."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=3)  # Give more weight to results area
        
        # Title
        title_label = ttk.Label(main_frame, text="PDF Table of Contents Splitter", 
                               font=('Helvetica', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection
        ttk.Label(main_frame, text="PDF File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        file_frame.columnconfigure(0, weight=1)
        
        self.file_entry = ttk.Entry(file_frame, textvariable=self.pdf_path, width=50)
        self.file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        browse_btn = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_btn.grid(row=0, column=1)
        
        # Output directory
        ttk.Label(main_frame, text="Output Dir:").grid(row=2, column=0, sticky=tk.W, pady=5)
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        dir_frame.columnconfigure(0, weight=1)
        
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.output_dir, width=50)
        self.dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        dir_browse_btn = ttk.Button(dir_frame, text="Browse", command=self.browse_directory)
        dir_browse_btn.grid(row=0, column=1)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=20)
        
        self.analyze_btn = ttk.Button(button_frame, text="Analyze PDF", 
                                     command=self.analyze_pdf, state=tk.DISABLED)
        self.analyze_btn.pack(side=tk.LEFT, padx=5)
        
        self.manual_btn = ttk.Button(button_frame, text="Manual Input", 
                                    command=self.manual_input, state=tk.DISABLED)
        self.manual_btn.pack(side=tk.LEFT, padx=5)
        
        self.split_btn = ttk.Button(button_frame, text="Split PDF", 
                                   command=self.split_pdf, state=tk.DISABLED)
        self.split_btn.pack(side=tk.LEFT, padx=5)
        
        # Results area
        results_frame = ttk.LabelFrame(main_frame, text="Table of Contents / Page Ranges", padding="5")
        results_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(1, weight=1)
        
        # Selection controls
        selection_frame = ttk.Frame(results_frame)
        selection_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(selection_frame, text="Select sections to split (double-click to edit):").pack(side=tk.LEFT)
        ttk.Button(selection_frame, text="Select All", command=self.select_all).pack(side=tk.RIGHT, padx=5)
        ttk.Button(selection_frame, text="Select None", command=self.select_none).pack(side=tk.RIGHT)
        
        # Treeview for showing TOC entries
        columns = ('Section', 'Start Page', 'End Page')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings')
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=200)
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Select a PDF file to begin.")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Bind file entry changes
        try:
            # Try the new method first (Tcl 9+)
            self.pdf_path.trace_add('write', self.on_file_changed)
        except AttributeError:
            # Fall back to old method (Tcl 8)
            self.pdf_path.trace('w', self.on_file_changed)
        
        # Bind tree click for checkbox toggling and double-click for editing
        self.tree.bind('<Button-1>', self.on_tree_click)
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        
        # Track selected items and editing state
        self.selected_items = set()
        self.editing_item = None
        self.edit_entry = None
    
    def setup_drag_drop(self):
        """Setup drag and drop functionality (basic version)."""
        # This is a simplified version - full drag/drop would require tkinterdnd2
        # For now, we'll just handle file path pasting
        def on_drop(event):
            # Handle dropped files (if the path is pasted)
            pass
        
        self.file_entry.bind('<Control-v>', lambda e: self.root.after(10, self.check_pasted_file))
    
    def check_pasted_file(self):
        """Check if a file path was pasted."""
        path = self.pdf_path.get().strip().strip('"\'')
        if path and os.path.exists(path) and path.lower().endswith('.pdf'):
            self.set_output_dir_from_pdf(path)
    
    def browse_file(self):
        """Browse for PDF file."""
        filename = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.pdf_path.set(filename)
            self.set_output_dir_from_pdf(filename)
    
    def browse_directory(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir.set(directory)
    
    def set_output_dir_from_pdf(self, pdf_path):
        """Set default output directory to Google Drive Pattern Splitter folder."""
        if not self.output_dir.get():
            # Default to Google Drive Pattern Splitter folder
            default_output = '/Users/nicoleomeara/Library/CloudStorage/GoogleDrive-nicole.a.omeara@gmail.com/.shortcut-targets-by-id/1AIiIGTbbLNB5YetWeeByl94AInhyERDg/Weaving/Pattern Splitter'
            self.output_dir.set(default_output)
    
    def on_file_changed(self, *args):
        """Handle file path changes."""
        has_file = bool(self.pdf_path.get().strip())
        self.analyze_btn.config(state=tk.NORMAL if has_file else tk.DISABLED)
        self.manual_btn.config(state=tk.NORMAL if has_file else tk.DISABLED)
        
        if has_file and os.path.exists(self.pdf_path.get()):
            self.status_var.set(f"Ready to analyze: {os.path.basename(self.pdf_path.get())}")
        elif has_file:
            self.status_var.set("File not found. Please select a valid PDF file.")
        else:
            self.status_var.set("Ready. Select a PDF file to begin.")
    
    def analyze_pdf(self):
        """Analyze PDF for table of contents."""
        pdf_path = self.pdf_path.get().strip()
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("Error", "Please select a valid PDF file.")
            return
        
        self.status_var.set("Analyzing PDF...")
        self.analyze_btn.config(state=tk.DISABLED)
        
        # Run analysis in separate thread to prevent GUI freezing
        thread = threading.Thread(target=self._analyze_pdf_thread, args=(pdf_path,))
        thread.daemon = True
        thread.start()
    
    def _analyze_pdf_thread(self, pdf_path):
        """Analyze PDF in background thread."""
        import threading
        
        # Create a flag to track if operation completed
        completed = threading.Event()
        results = {}
        
        def do_analysis():
            try:
                with PDFTOCSplitter(pdf_path, self.output_dir.get()) as splitter:
                    toc_entries = splitter.extract_toc_from_pdf()
                    
                    # Convert to page ranges
                    ranges = []
                    for i, (title, page) in enumerate(toc_entries):
                        start_page = page
                        end_page = toc_entries[i + 1][1] - 1 if i + 1 < len(toc_entries) else len(splitter.doc)
                        ranges.append((title, start_page, end_page))
                    
                    results['ranges'] = ranges
                    results['total_pages'] = len(splitter.doc)
                    
            except Exception as e:
                results['error'] = str(e)
            finally:
                completed.set()
        
        # Start analysis in a separate thread
        analysis_thread = threading.Thread(target=do_analysis)
        analysis_thread.daemon = True
        analysis_thread.start()
        
        # Wait for completion with timeout
        if completed.wait(timeout=30):  # 30 second timeout
            if 'error' in results:
                error_msg = f"Analysis failed: {results['error']}"
                self.root.after(0, self._analysis_error, error_msg)
            else:
                self.root.after(0, self._update_analysis_results, results['ranges'], results['total_pages'])
        else:
            error_msg = "PDF analysis timed out. This PDF may be too complex or corrupted. Try using manual input instead."
            self.root.after(0, self._analysis_error, error_msg)
    
    def _update_analysis_results(self, ranges, total_pages):
        """Update GUI with analysis results."""
        self.page_ranges = ranges
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add new items with checkboxes (initially all selected)
        self.selected_items.clear()
        for i, (title, start, end) in enumerate(ranges):
            item_id = self.tree.insert('', tk.END, values=('☑', title, start, end))
            self.selected_items.add(item_id)
        
        if ranges:
            self.status_var.set(f"Found {len(ranges)} sections in {total_pages}-page PDF. Double-click to edit names/pages. Ready to split!")
            self.split_btn.config(state=tk.NORMAL)
        else:
            self.status_var.set("No table of contents found. Try manual input instead.")
        
        self.analyze_btn.config(state=tk.NORMAL)
    
    def _analysis_error(self, error_msg):
        """Handle analysis error."""
        self.status_var.set("Analysis failed. Try manual input instead.")
        self.analyze_btn.config(state=tk.NORMAL)
        messagebox.showerror("Analysis Error", f"Failed to analyze PDF:\n{error_msg}")
    
    def manual_input(self):
        """Open manual input dialog."""
        pdf_path = self.pdf_path.get().strip()
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("Error", "Please select a valid PDF file.")
            return
        
        dialog = ManualInputDialog(self.root, pdf_path)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            self.page_ranges = dialog.result
            
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Add new items with checkboxes (initially all selected)
            self.selected_items.clear()
            for title, start, end in self.page_ranges:
                item_id = self.tree.insert('', tk.END, values=('☑', title, start, end))
                self.selected_items.add(item_id)
            
            self.status_var.set(f"Manually configured {len(self.page_ranges)} sections. Ready to split!")
            self.split_btn.config(state=tk.NORMAL)
    
    def split_pdf(self):
        """Split the PDF based on selected page ranges."""
        if not self.page_ranges:
            messagebox.showerror("Error", "No page ranges defined. Analyze PDF or use manual input first.")
            return
        
        # Get only selected ranges
        selected_ranges = []
        for item_id in self.tree.get_children():
            if item_id in self.selected_items:
                values = self.tree.item(item_id, 'values')
                # Skip the checkbox column (index 0)
                selected_ranges.append((values[1], int(values[2]), int(values[3])))
        
        if not selected_ranges:
            messagebox.showerror("Error", "No sections selected. Please select at least one section to split.")
            return
        
        self.page_ranges = selected_ranges
        
        pdf_path = self.pdf_path.get().strip()
        output_dir = self.output_dir.get().strip()
        
        if not output_dir:
            output_dir = os.path.join(os.path.dirname(pdf_path), "split_pdfs")
            self.output_dir.set(output_dir)
        
        self.status_var.set("Splitting PDF...")
        self.split_btn.config(state=tk.DISABLED)
        
        # Run splitting in separate thread
        thread = threading.Thread(target=self._split_pdf_thread, args=(pdf_path, output_dir))
        thread.daemon = True
        thread.start()
    
    def _split_pdf_thread(self, pdf_path, output_dir):
        """Split PDF in background thread."""
        try:
            with PDFTOCSplitter(pdf_path, output_dir) as splitter:
                created_files = splitter.split_pdf(self.page_ranges)
                self.root.after(0, self._split_complete, created_files, output_dir)
                
        except Exception as e:
            self.root.after(0, self._split_error, str(e))
    
    def _split_complete(self, created_files, output_dir):
        """Handle successful PDF split."""
        self.status_var.set(f"Successfully created {len(created_files)} files!")
        self.split_btn.config(state=tk.NORMAL)
        
        # Move original file to "already split" folder
        self._move_original_file()
        
        # Show success message with option to open folder
        result = messagebox.askquestion(
            "Split Complete", 
            f"Successfully created {len(created_files)} PDF files!\n\n"
            f"Files saved to:\n{output_dir}\n\n"
            f"Original file moved to 'ebooks already split' folder.\n\n"
            "Would you like to open the output folder?",
            icon='question'
        )
        
        if result == 'yes':
            # Open folder in Finder (macOS)
            os.system(f'open "{output_dir}"')
    
    def _split_error(self, error_msg):
        """Handle split error."""
        self.status_var.set("Split failed. Check your settings and try again.")
        self.split_btn.config(state=tk.NORMAL)
        messagebox.showerror("Split Error", f"Failed to split PDF:\n{error_msg}")
    
    def on_tree_click(self, event):
        """Handle tree click for checkbox toggling."""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify("column", event.x, event.y)
            if column == '#1':  # First column (Select)
                item = self.tree.identify("row", event.x, event.y)
                if item:
                    self.toggle_selection(item)
    
    def toggle_selection(self, item):
        """Toggle the selection state of an item."""
        if item in self.selected_items:
            self.selected_items.remove(item)
            values = list(self.tree.item(item, 'values'))
            values[0] = '☐'  # Unchecked
            self.tree.item(item, values=values)
        else:
            self.selected_items.add(item)
            values = list(self.tree.item(item, 'values'))
            values[0] = '☑'  # Checked
            self.tree.item(item, values=values)
        
        # Update split button state
        self.split_btn.config(state=tk.NORMAL if self.selected_items else tk.DISABLED)
    
    def select_all(self):
        """Select all items."""
        for item in self.tree.get_children():
            if item not in self.selected_items:
                self.selected_items.add(item)
                values = list(self.tree.item(item, 'values'))
                values[0] = '☑'
                self.tree.item(item, values=values)
        self.split_btn.config(state=tk.NORMAL if self.selected_items else tk.DISABLED)
    
    def select_none(self):
        """Deselect all items."""
        for item in self.tree.get_children():
            if item in self.selected_items:
                self.selected_items.remove(item)
                values = list(self.tree.item(item, 'values'))
                values[0] = '☐'
                self.tree.item(item, values=values)
        self.split_btn.config(state=tk.DISABLED)
    
    def on_tree_double_click(self, event):
        """Handle double-click for inline editing."""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify("column", event.x, event.y)
            item = self.tree.identify("row", event.x, event.y)
            
            # Only allow editing of Section, Start Page, and End Page columns
            if item and column in ['#2', '#3', '#4']:  # Skip checkbox column (#1)
                self.start_editing(item, column, event.x, event.y)
    
    def start_editing(self, item, column, x, y):
        """Start inline editing of a cell."""
        if self.editing_item:
            self.finish_editing()
        
        # Get current value
        values = list(self.tree.item(item, 'values'))
        column_index = int(column[1:]) - 1  # Convert '#2' to index 1
        current_value = values[column_index]
        
        # Get cell coordinates
        bbox = self.tree.bbox(item, column)
        if not bbox:
            return
        
        # Create entry widget for editing
        self.editing_item = item
        self.editing_column = column
        self.editing_column_index = column_index
        
        self.edit_entry = tk.Entry(self.tree)
        self.edit_entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        self.edit_entry.insert(0, str(current_value))
        self.edit_entry.select_range(0, tk.END)
        self.edit_entry.focus()
        
        # Bind events
        self.edit_entry.bind('<Return>', lambda e: self.finish_editing())
        self.edit_entry.bind('<KP_Enter>', lambda e: self.finish_editing())  # Numpad Enter
        self.edit_entry.bind('<Escape>', lambda e: self.cancel_editing())
        self.edit_entry.bind('<FocusOut>', lambda e: self.finish_editing())
    
    def finish_editing(self):
        """Finish inline editing and update the cell."""
        if not self.editing_item or not self.edit_entry:
            return
        
        new_value = self.edit_entry.get().strip()
        
        # Validate the input based on column
        if self.editing_column in ['#3', '#4']:  # Start/End Page columns
            try:
                new_value = int(new_value)
                if new_value < 1:
                    raise ValueError("Page number must be at least 1")
            except ValueError as e:
                messagebox.showerror("Invalid Input", f"Please enter a valid page number: {e}")
                self.cancel_editing()
                return
        elif self.editing_column == '#2':  # Section name column
            if not new_value:
                messagebox.showerror("Invalid Input", "Section name cannot be empty")
                self.cancel_editing()
                return
        
        # Update the tree item
        values = list(self.tree.item(self.editing_item, 'values'))
        values[self.editing_column_index] = new_value
        self.tree.item(self.editing_item, values=values)
        
        # Update the page_ranges list
        self.update_page_ranges_from_tree()
        
        self.cleanup_editing()
    
    def cancel_editing(self):
        """Cancel inline editing without saving changes."""
        self.cleanup_editing()
    
    def cleanup_editing(self):
        """Clean up editing widgets and state."""
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None
        self.editing_item = None
        self.editing_column = None
        self.editing_column_index = None
    
    def update_page_ranges_from_tree(self):
        """Update the page_ranges list from current tree contents."""
        self.page_ranges = []
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            # Skip checkbox column (index 0)
            section_name = values[1]
            start_page = int(values[2])
            end_page = int(values[3])
            self.page_ranges.append((section_name, start_page, end_page))
    
    def _move_original_file(self):
        """Move the original PDF file to the 'ebooks already split' folder."""
        try:
            original_path = self.pdf_path.get().strip()
            if not original_path or not os.path.exists(original_path):
                return
            
            # Destination folder
            dest_folder = '/Users/nicoleomeara/Library/CloudStorage/GoogleDrive-nicole.a.omeara@gmail.com/.shortcut-targets-by-id/1AIiIGTbbLNB5YetWeeByl94AInhyERDg/Weaving/ebooks already split'
            
            # Create destination folder if it doesn't exist
            os.makedirs(dest_folder, exist_ok=True)
            
            # Get filename
            filename = os.path.basename(original_path)
            dest_path = os.path.join(dest_folder, filename)
            
            # Handle duplicate filenames
            counter = 1
            base_name, ext = os.path.splitext(filename)
            while os.path.exists(dest_path):
                new_filename = f"{base_name}_{counter}{ext}"
                dest_path = os.path.join(dest_folder, new_filename)
                counter += 1
            
            # Move the file
            shutil.move(original_path, dest_path)
            print(f"Moved original file to: {dest_path}")
            
        except Exception as e:
            print(f"Warning: Could not move original file: {e}")
            # Don't show error to user as this is not critical


class ManualInputDialog:
    def __init__(self, parent, pdf_path):
        self.result = None
        
        # Get PDF page count
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            doc.close()
        except:
            total_pages = "unknown"
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Manual Page Range Input")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog on parent
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50, 
            parent.winfo_rooty() + 50
        ))
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        instructions = ttk.Label(main_frame, 
            text=f"Enter page ranges for: {os.path.basename(pdf_path)}\n"
                 f"Total pages: {total_pages}\n\n"
                 "Format: Section Name, Start Page, End Page\n"
                 "Example: Chapter 1, 5, 20",
            font=('Helvetica', 10))
        instructions.pack(pady=(0, 10))
        
        # Entry area
        entry_frame = ttk.LabelFrame(main_frame, text="Page Ranges", padding="5")
        entry_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Columns
        columns = ('Select', 'Section Name', 'Start Page', 'End Page')
        self.tree = ttk.Treeview(entry_frame, columns=columns, show='headings', height=10)
        self.selected_items = set()
        
        # Configure columns
        self.tree.heading('Select', text='✓')
        self.tree.column('Select', width=40, anchor='center')
        self.tree.heading('Section Name', text='Section Name')
        self.tree.column('Section Name', width=200)
        self.tree.heading('Start Page', text='Start Page')
        self.tree.column('Start Page', width=100, anchor='center')
        self.tree.heading('End Page', text='End Page')
        self.tree.column('End Page', width=100, anchor='center')
        
        # Bind click for checkbox toggling
        self.tree.bind('<Button-1>', self.on_tree_click)
        
        scrollbar = ttk.Scrollbar(entry_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # Input fields
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(input_frame, text="Section:").grid(row=0, column=0, padx=5)
        self.section_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.section_var, width=20).grid(row=0, column=1, padx=5)
        
        ttk.Label(input_frame, text="Start:").grid(row=0, column=2, padx=5)
        self.start_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.start_var, width=10).grid(row=0, column=3, padx=5)
        
        ttk.Label(input_frame, text="End:").grid(row=0, column=4, padx=5)
        self.end_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.end_var, width=10).grid(row=0, column=5, padx=5)
        
        ttk.Button(input_frame, text="Add", command=self.add_range).grid(row=0, column=6, padx=10)
        ttk.Button(input_frame, text="Remove", command=self.remove_range).grid(row=0, column=7, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.RIGHT)
        
        # Bind Enter key to add button
        self.dialog.bind('<Return>', lambda e: self.add_range())
        self.dialog.bind('<KP_Enter>', lambda e: self.add_range())  # Numpad Enter
    
    def add_range(self):
        """Add a page range to the list."""
        section = self.section_var.get().strip()
        start = self.start_var.get().strip()
        end = self.end_var.get().strip()
        
        if not all([section, start, end]):
            messagebox.showerror("Error", "Please fill in all fields.")
            return
        
        try:
            start_int = int(start)
            end_int = int(end)
            if start_int > end_int:
                raise ValueError("Start page must be <= end page")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid page numbers: {e}")
            return
        
        item_id = self.tree.insert('', tk.END, values=('☑', section, start_int, end_int))
        self.selected_items.add(item_id)
        
        # Clear fields
        self.section_var.set('')
        self.start_var.set('')
        self.end_var.set('')
    
    def remove_range(self):
        """Remove selected range from the list."""
        selected = self.tree.selection()
        if selected:
            for item in selected:
                if item in self.selected_items:
                    self.selected_items.remove(item)
            self.tree.delete(selected)
    
    def toggle_selection(self, item):
        """Toggle the selection state of an item."""
        if item in self.selected_items:
            self.selected_items.remove(item)
            values = list(self.tree.item(item, 'values'))
            values[0] = '☐'  # Unchecked
            self.tree.item(item, values=values)
        else:
            self.selected_items.add(item)
            values = list(self.tree.item(item, 'values'))
            values[0] = '☑'  # Checked
            self.tree.item(item, values=values)
    
    def ok(self):
        """Confirm and return results."""
        ranges = []
        selected_ranges = []
        
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            # Skip checkbox column (index 0) for ranges
            ranges.append((values[1], int(values[2]), int(values[3])))
            if item in self.selected_items:
                selected_ranges.append((values[1], int(values[2]), int(values[3])))
        
        if not ranges:
            messagebox.showerror("Error", "Please add at least one page range.")
            return
        
        if not selected_ranges:
            messagebox.showerror("Error", "Please select at least one section to split.")
            return
        
        self.result = selected_ranges
        self.dialog.destroy()
    
    def on_tree_click(self, event):
        """Handle tree click for checkbox toggling."""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify("column", event.x, event.y)
            if column == '#1':  # First column (Select)
                item = self.tree.identify("row", event.x, event.y)
                if item:
                    self.toggle_selection(item)
    
    def toggle_selection(self, item):
        """Toggle the selection state of an item."""
        if item in self.selected_items:
            self.selected_items.remove(item)
            values = list(self.tree.item(item, 'values'))
            values[0] = '☐'  # Unchecked
            self.tree.item(item, values=values)
        else:
            self.selected_items.add(item)
            values = list(self.tree.item(item, 'values'))
            values[0] = '☑'  # Checked
            self.tree.item(item, values=values)
    
    def cancel(self):
        """Cancel dialog."""
        self.result = None
        self.dialog.destroy()


def main():
    """Main entry point for GUI version."""
    root = tk.Tk()
    app = PDFSplitterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()