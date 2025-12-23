#!/usr/bin/env python3
"""
PDF Pattern Renamer - GUI Version

A user-friendly graphical interface for batch renaming PDF pattern files
based on their internal titles or table of contents.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
import shutil
import subprocess
from pathlib import Path
import re
import fitz  # pymupdf

class PatternRenamerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Pattern Renamer")
        self.root.geometry("800x600")
        
        # Configure style
        style = ttk.Style()
        if style.theme_use() != 'clam':
            try:
                style.theme_use('clam')
            except:
                pass
        
        # Variables
        self.pdf_files = []
        self.rename_data = []
        
        self.create_widgets()
        self.center_window()
    
    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_reqwidth()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_reqheight()) // 2
        self.root.geometry(f"+{x}+{y}")
    
    def create_widgets(self):
        """Create and layout the GUI widgets."""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="PDF Pattern Renamer", 
                               font=('Helvetica', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Instructions
        instructions = ttk.Label(main_frame, 
            text="Select PDF pattern files to analyze and rename based on their internal titles.\n" +
                 "Use Enter to view files, Space to toggle selection, or right-click for more options.",
            font=('Helvetica', 10))
        instructions.pack(pady=(0, 15))
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Buttons for file operations
        button_frame = ttk.Frame(file_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.select_btn = ttk.Button(button_frame, text="Select PDF Files", 
                                    command=self.select_files)
        self.select_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.analyze_btn = ttk.Button(button_frame, text="Analyze Titles", 
                                     command=self.analyze_files, state=tk.DISABLED)
        self.analyze_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(button_frame, text="Clear All", 
                                   command=self.clear_files)
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(file_frame, variable=self.progress_var, 
                                          maximum=100, length=300)
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready - Select PDF files to begin")
        status_label = ttk.Label(file_frame, textvariable=self.status_var)
        status_label.pack(pady=(5, 0))
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Rename Preview", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Treeview for showing files and proposed names
        columns = ('Select', 'Current Name', 'Detected Title', 'New Name', 'Status')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=12)
        self.selected_items = set()  # Track selected items
        
        # Configure columns
        self.tree.heading('Select', text='✓')
        self.tree.column('Select', width=40, anchor='center')
        self.tree.heading('Current Name', text='Current Filename')
        self.tree.column('Current Name', width=180)
        self.tree.heading('Detected Title', text='Detected Pattern Title')
        self.tree.column('Detected Title', width=220)
        self.tree.heading('New Name', text='Proposed New Name')
        self.tree.column('New Name', width=180)
        self.tree.heading('Status', text='Status')
        self.tree.column('Status', width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # Enable double-click editing of new names and single-click for checkboxes
        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<Button-1>', self.on_single_click)
        
        # Add right-click context menu
        self.tree.bind('<Button-2>', self.show_context_menu)  # Right-click on Mac
        self.tree.bind('<Button-3>', self.show_context_menu)  # Right-click on Windows/Linux
        
        # Create context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="View File", command=self.view_context_file)
        self.context_menu.add_command(label="Show in Finder", command=self.show_in_finder)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Edit Name", command=self.edit_context_name)
        
        # Context menu state
        self.context_item = None
        
        # Keyboard shortcuts
        self.root.bind('<Return>', lambda e: self.view_selected_file())
        self.root.bind('<KP_Enter>', lambda e: self.view_selected_file())
        self.root.bind('<space>', lambda e: self.toggle_selected_item())
        
        # Add right-click context menu
        self.tree.bind('<Button-2>', self.show_context_menu)  # Right-click on Mac
        self.tree.bind('<Button-3>', self.show_context_menu)  # Right-click on Windows/Linux
        
        # Create context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="View File", command=self.view_context_file)
        self.context_menu.add_command(label="Show in Finder", command=self.show_in_finder)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Edit Name", command=self.edit_context_name)
        
        # Context menu state
        self.context_item = None
        
        # Editing variables
        self.edit_entry = None
        self.editing_item = None
        
        # Selection buttons
        selection_frame = ttk.Frame(main_frame)
        selection_frame.pack(fill=tk.X, pady=(5, 5))
        
        ttk.Button(selection_frame, text="Select All", 
                  command=self.select_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(selection_frame, text="Unselect All", 
                  command=self.unselect_all).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Separator(selection_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=(10, 10))
        
        ttk.Button(selection_frame, text="View Selected File", 
                  command=self.view_selected_file).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Separator(selection_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=(10, 10))
        
        ttk.Button(selection_frame, text="View Selected File", 
                  command=self.view_selected_file).pack(side=tk.LEFT, padx=(0, 5))
        
        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X)
        
        self.rename_btn = ttk.Button(action_frame, text="Rename Selected Files", 
                                    command=self.rename_files, state=tk.DISABLED)
        self.rename_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.export_btn = ttk.Button(action_frame, text="Export List", 
                                    command=self.export_list, state=tk.DISABLED)
        self.export_btn.pack(side=tk.RIGHT)
    
    def select_files(self):
        """Open file dialog to select PDF files."""
        files = filedialog.askopenfilenames(
            title="Select PDF Pattern Files",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if files:
            self.pdf_files = list(files)
            self.status_var.set(f"Selected {len(self.pdf_files)} files")
            self.analyze_btn.config(state=tk.NORMAL)
            
            # Clear previous results
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.rename_data = []
            self.rename_btn.config(state=tk.DISABLED)
    
    def clear_files(self):
        """Clear all selected files and results."""
        self.pdf_files = []
        self.rename_data = []
        
        # Clear treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Reset UI state
        self.analyze_btn.config(state=tk.DISABLED)
        self.rename_btn.config(state=tk.DISABLED)
        self.export_btn.config(state=tk.DISABLED)
        self.status_var.set("Ready - Select PDF files to begin")
        self.progress_var.set(0)
        self.context_item = None
        self.selected_items.clear()
    
    def analyze_files(self):
        """Analyze selected PDF files to extract pattern titles."""
        if not self.pdf_files:
            messagebox.showwarning("Warning", "Please select PDF files first.")
            return
        
        self.analyze_btn.config(state=tk.DISABLED)
        self.status_var.set("Analyzing PDF files...")
        self.progress_var.set(0)
        
        # Run analysis in a separate thread to prevent GUI freezing
        thread = threading.Thread(target=self._analyze_files_thread, daemon=True)
        thread.start()
    
    def _analyze_files_thread(self):
        """Thread function for analyzing PDF files."""
        try:
            total_files = len(self.pdf_files)
            self.rename_data = []
            
            for i, pdf_path in enumerate(self.pdf_files):
                # Update progress
                progress = (i / total_files) * 100
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                self.root.after(0, lambda f=os.path.basename(pdf_path): 
                               self.status_var.set(f"Analyzing: {f}"))
                
                # Extract title from PDF
                title = self.extract_pattern_title(pdf_path)
                current_name = os.path.basename(pdf_path)
                
                # Generate new filename
                if title:
                    new_name = self.sanitize_filename(title) + ".pdf"
                    status = "Ready"
                else:
                    new_name = current_name
                    status = "No title found"
                    title = "Not detected"
                
                # Check if new name would conflict
                if new_name != current_name:
                    target_path = os.path.join(os.path.dirname(pdf_path), new_name)
                    if os.path.exists(target_path):
                        status = "Name conflict"
                
                self.rename_data.append({
                    'path': pdf_path,
                    'current_name': current_name,
                    'detected_title': title,
                    'new_name': new_name,
                    'status': status,
                    'selected': True  # Default to selected
                })
            
            # Update UI on main thread
            self.root.after(0, self._update_results)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Analysis failed: {str(e)}"))
            self.root.after(0, lambda: self.analyze_btn.config(state=tk.NORMAL))
    
    def _update_results(self):
        """Update the results treeview with analysis data."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add new items
        for i, data in enumerate(self.rename_data):
            checkbox = '☑' if data['selected'] else '☐'
            item = self.tree.insert('', tk.END, values=(
                checkbox,
                data['current_name'],
                data['detected_title'],
                data['new_name'],
                data['status']
            ))
            if data['selected']:
                self.selected_items.add(item)
        
        # Update UI state
        self.progress_var.set(100)
        self.status_var.set(f"Analysis complete - {len(self.rename_data)} files processed")
        self.analyze_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.NORMAL)
        
        # Enable rename button if there are selected files ready to rename
        ready_count = sum(1 for data in self.rename_data if data['status'] == 'Ready' and data['selected'])
        if ready_count > 0:
            self.rename_btn.config(state=tk.NORMAL)
    
    def extract_pattern_title(self, pdf_path):
        """Extract pattern title from PDF file."""
        try:
            doc = fitz.open(pdf_path)
            
            # Strategy 1: Check PDF metadata
            title = doc.metadata.get('title', '').strip()
            if title and len(title) > 3:
                doc.close()
                return title
            
            # Strategy 2: Look in first few pages for title patterns
            title = self.find_title_in_pages(doc)
            doc.close()
            return title
            
        except Exception as e:
            print(f"Error extracting title from {pdf_path}: {e}")
            return None
    
    def find_title_in_pages(self, doc, max_pages=3):
        """Search for pattern titles in the first few pages."""
        title_patterns = [
            # Common pattern title formats
            r'^([A-Z][A-Za-z\s&\-\']+(?:Scarf|Shawl|Wrap|Top|Sweater|Cardigan|Hat|Bag|Blanket|Throw|Runner|Placemat|Towel|Napkin)s?)',
            r'(?:Pattern|Project):\s*([A-Z][A-Za-z\s&\-\']+)',
            r'^([A-Z][A-Za-z\s&\-\']{5,40})\s*(?:by|By)',
            r'^([A-Z][A-Za-z\s&\-\']{5,40})$',
            # Look for titles that start with capital letters and are on their own line
            r'^([A-Z][A-Za-z\s&\-\']{10,50})',
        ]
        
        for page_num in range(min(max_pages, len(doc))):
            try:
                page = doc[page_num]
                text = page.get_text()
                lines = text.split('\n')
                
                # Clean and filter lines
                clean_lines = []
                for line in lines:
                    line = line.strip()
                    if len(line) > 5 and not line.isdigit():
                        clean_lines.append(line)
                
                # Try different patterns
                for pattern in title_patterns:
                    for line in clean_lines[:10]:  # Check first 10 meaningful lines
                        match = re.match(pattern, line.strip())
                        if match:
                            title = match.group(1).strip()
                            # Validate the title
                            if self.is_valid_title(title):
                                return title
                
                # Look for standalone lines that might be titles
                for line in clean_lines[:5]:
                    if self.is_potential_title(line):
                        return line
                        
            except Exception as e:
                print(f"Error processing page {page_num}: {e}")
                continue
        
        return None
    
    def is_valid_title(self, title):
        """Check if extracted text looks like a valid pattern title."""
        if not title or len(title) < 5:
            return False
        
        # Skip common non-title text
        skip_words = ['page', 'copyright', 'all rights', 'materials', 'yarn', 'gauge', 
                     'instructions', 'abbreviations', 'notes', 'introduction']
        title_lower = title.lower()
        
        for skip in skip_words:
            if skip in title_lower:
                return False
        
        # Good indicators
        good_words = ['scarf', 'shawl', 'wrap', 'top', 'sweater', 'cardigan', 'hat', 
                     'bag', 'blanket', 'throw', 'runner', 'placemat', 'towel', 'napkin']
        
        for good in good_words:
            if good in title_lower:
                return True
        
        # Check if it looks like a title (proper case, reasonable length)
        words = title.split()
        if len(words) >= 2 and len(words) <= 8:
            if title[0].isupper() and any(word[0].isupper() for word in words[1:]):
                return True
        
        return False
    
    def is_potential_title(self, text):
        """Check if a line of text could be a pattern title."""
        if not text or len(text) < 5 or len(text) > 60:
            return False
        
        # Must start with capital letter
        if not text[0].isupper():
            return False
        
        # Should have reasonable word count
        words = text.split()
        if len(words) < 2 or len(words) > 10:
            return False
        
        # Should not be all caps (likely headers)
        if text.isupper():
            return False
        
        return True
    
    def sanitize_filename(self, filename):
        """Clean filename to be filesystem-safe."""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        
        # Replace multiple spaces with single space
        filename = re.sub(r'\s+', ' ', filename)
        
        # Trim and remove leading/trailing dots
        filename = filename.strip(' .')
        
        # Limit length
        if len(filename) > 100:
            filename = filename[:100].strip()
        
        return filename
    
    def on_single_click(self, event):
        """Handle single-click for checkbox toggling."""
        item = self.tree.identify('item', event.x, event.y)
        column = self.tree.identify_column(event.x)
        
        if item and column == '#1':  # First column (Select)
            self.toggle_selection(item)
    
    def toggle_selection(self, item):
        """Toggle the selection state of an item."""
        item_index = self.tree.index(item)
        
        # Toggle selection state in data
        self.rename_data[item_index]['selected'] = not self.rename_data[item_index]['selected']
        
        # Update checkbox display
        values = list(self.tree.item(item, 'values'))
        values[0] = '☑' if self.rename_data[item_index]['selected'] else '☐'
        self.tree.item(item, values=values)
        
        # Update selected_items set
        if self.rename_data[item_index]['selected']:
            self.selected_items.add(item)
        else:
            self.selected_items.discard(item)
        
        # Update rename button state
        ready_count = sum(1 for data in self.rename_data if data['status'] == 'Ready' and data['selected'])
        self.rename_btn.config(state=tk.NORMAL if ready_count > 0 else tk.DISABLED)
    
    def on_double_click(self, event):
        """Handle double-click on treeview for editing."""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item:
            return
        
        # Get column and position
        column = self.tree.identify_column(event.x)
        if column != '#4':  # Only allow editing the "New Name" column (now 4th column)
            return
        
        self.start_editing(item, column)
    
    def start_editing(self, item, column):
        """Start inline editing of a cell."""
        if self.edit_entry:
            self.finish_editing()
        
        # Get cell position
        bbox = self.tree.bbox(item, column)
        if not bbox:
            return
        
        current_value = self.tree.item(item, 'values')[3]  # New Name column (now 4th column)
        
        self.editing_item = item
        
        # Create entry widget
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
        """Finish editing and update the value."""
        if not self.editing_item or not self.edit_entry:
            return
        
        new_value = self.edit_entry.get().strip()
        
        if new_value:
            # Ensure .pdf extension
            if not new_value.lower().endswith('.pdf'):
                new_value += '.pdf'
            
            # Sanitize filename
            new_value = self.sanitize_filename(new_value.replace('.pdf', '')) + '.pdf'
            
            # Update tree and data
            values = list(self.tree.item(self.editing_item, 'values'))
            values[3] = new_value  # New Name column (now 4th column)
            
            # Update status
            item_index = self.tree.index(self.editing_item)
            old_path = self.rename_data[item_index]['path']
            target_path = os.path.join(os.path.dirname(old_path), new_value)
            
            if os.path.exists(target_path) and target_path != old_path:
                values[4] = "Name conflict"  # Status column (now 5th column)
            else:
                values[4] = "Ready" if new_value != values[1] else "No change"  # Compare with current name (2nd column)
            
            self.tree.item(self.editing_item, values=values)
            self.rename_data[item_index]['new_name'] = new_value
            self.rename_data[item_index]['status'] = values[4]
        
        self.cleanup_editing()
    
    def cancel_editing(self):
        """Cancel editing without saving."""
        self.cleanup_editing()
    
    def cleanup_editing(self):
        """Clean up editing widgets."""
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None
        self.editing_item = None
    
    def rename_files(self):
        """Rename the PDF files based on the new names."""
        ready_items = [data for data in self.rename_data if data['status'] == 'Ready' and data['selected']]
        
        if not ready_items:
            messagebox.showwarning("Warning", "No selected files are ready to be renamed.")
            return
        
        # Confirm with user
        count = len(ready_items)
        response = messagebox.askyesno("Confirm Rename", 
                                     f"Rename {count} file(s)? This operation cannot be undone.")
        if not response:
            return
        
        # Perform renames
        success_count = 0
        error_count = 0
        
        self.status_var.set("Renaming files...")
        self.progress_var.set(0)
        
        for i, data in enumerate(ready_items):
            try:
                old_path = data['path']
                new_path = os.path.join(os.path.dirname(old_path), data['new_name'])
                
                os.rename(old_path, new_path)
                success_count += 1
                
                # Update tree item status
                for item in self.tree.get_children():
                    if self.tree.item(item, 'values')[1] == data['current_name']:  # Current name is now 2nd column
                        values = list(self.tree.item(item, 'values'))
                        values[4] = "Renamed ✓"  # Status is now 5th column
                        self.tree.item(item, values=values)
                        break
                
            except Exception as e:
                error_count += 1
                print(f"Error renaming {data['current_name']}: {e}")
                
                # Update tree item status
                for item in self.tree.get_children():
                    if self.tree.item(item, 'values')[1] == data['current_name']:  # Current name is now 2nd column
                        values = list(self.tree.item(item, 'values'))
                        values[4] = "Error ✗"  # Status is now 5th column
                        self.tree.item(item, values=values)
                        break
            
            # Update progress
            progress = ((i + 1) / len(ready_items)) * 100
            self.progress_var.set(progress)
        
        # Show results
        self.progress_var.set(100)
        self.status_var.set(f"Rename complete: {success_count} succeeded, {error_count} failed")
        
        if error_count > 0:
            messagebox.showwarning("Partial Success", 
                                 f"Renamed {success_count} files successfully.\n"
                                 f"{error_count} files had errors.")
        else:
            messagebox.showinfo("Success", f"Successfully renamed {success_count} files.")
    
    def select_all(self):
        """Select all items for renaming."""
        for i, item in enumerate(self.tree.get_children()):
            if not self.rename_data[i]['selected']:
                self.toggle_selection(item)
    
    def unselect_all(self):
        """Unselect all items for renaming."""
        for i, item in enumerate(self.tree.get_children()):
            if self.rename_data[i]['selected']:
                self.toggle_selection(item)
    
    def view_selected_file(self):
        """Open the selected file in the default PDF viewer."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file to view.")
            return
        
        item = selection[0]
        item_index = self.tree.index(item)
        file_path = self.rename_data[item_index]['path']
        self.open_file(file_path)
    
    def show_context_menu(self, event):
        """Show context menu on right-click."""
        item = self.tree.identify('item', event.x, event.y)
        if item:
            self.context_item = item
            self.tree.selection_set(item)
            try:
                self.context_menu.post(event.x_root, event.y_root)
            except tk.TclError:
                pass  # Menu might be posted outside screen bounds
    
    def view_context_file(self):
        """View file from context menu."""
        if self.context_item:
            item_index = self.tree.index(self.context_item)
            file_path = self.rename_data[item_index]['path']
            self.open_file(file_path)
    
    def show_in_finder(self):
        """Show file in Finder/File Explorer."""
        if self.context_item:
            item_index = self.tree.index(self.context_item)
            file_path = self.rename_data[item_index]['path']
            self.reveal_in_finder(file_path)
    
    def edit_context_name(self):
        """Edit filename from context menu."""
        if self.context_item:
            self.start_editing(self.context_item, '#4')
    
    def open_file(self, file_path):
        """Open a file with the default application."""
        try:
            if sys.platform == 'darwin':  # macOS
                subprocess.run(['open', file_path], check=True)
            elif sys.platform == 'win32':  # Windows
                os.startfile(file_path)
            else:  # Linux and other Unix-like systems
                subprocess.run(['xdg-open', file_path], check=True)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Could not open file: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {str(e)}")
    
    def reveal_in_finder(self, file_path):
        """Reveal file in Finder/File Explorer."""
        try:
            if sys.platform == 'darwin':  # macOS
                subprocess.run(['open', '-R', file_path], check=True)
            elif sys.platform == 'win32':  # Windows
                subprocess.run(['explorer', '/select,', file_path], check=True)
            else:  # Linux
                # Try to open the parent directory
                parent_dir = os.path.dirname(file_path)
                subprocess.run(['xdg-open', parent_dir], check=True)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Could not reveal file: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not reveal file: {str(e)}")
    
    def toggle_selected_item(self):
        """Toggle selection of the currently selected item (spacebar shortcut)."""
        selection = self.tree.selection()
        if selection:
            self.toggle_selection(selection[0])
    
    def view_selected_file(self):
        """Open the selected file in the default PDF viewer."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file to view.")
            return
        
        item = selection[0]
        item_index = self.tree.index(item)
        file_path = self.rename_data[item_index]['path']
        self.open_file(file_path)
    
    def show_context_menu(self, event):
        """Show context menu on right-click."""
        item = self.tree.identify('item', event.x, event.y)
        if item:
            self.context_item = item
            self.tree.selection_set(item)
            try:
                self.context_menu.post(event.x_root, event.y_root)
            except tk.TclError:
                pass  # Menu might be posted outside screen bounds
    
    def view_context_file(self):
        """View file from context menu."""
        if self.context_item:
            item_index = self.tree.index(self.context_item)
            file_path = self.rename_data[item_index]['path']
            self.open_file(file_path)
    
    def show_in_finder(self):
        """Show file in Finder/File Explorer."""
        if self.context_item:
            item_index = self.tree.index(self.context_item)
            file_path = self.rename_data[item_index]['path']
            self.reveal_in_finder(file_path)
    
    def edit_context_name(self):
        """Edit filename from context menu."""
        if self.context_item:
            self.start_editing(self.context_item, '#4')
    
    def open_file(self, file_path):
        """Open a file with the default application."""
        try:
            if sys.platform == 'darwin':  # macOS
                subprocess.run(['open', file_path], check=True)
            elif sys.platform == 'win32':  # Windows
                os.startfile(file_path)
            else:  # Linux and other Unix-like systems
                subprocess.run(['xdg-open', file_path], check=True)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Could not open file: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {str(e)}")
    
    def reveal_in_finder(self, file_path):
        """Reveal file in Finder/File Explorer."""
        try:
            if sys.platform == 'darwin':  # macOS
                subprocess.run(['open', '-R', file_path], check=True)
            elif sys.platform == 'win32':  # Windows
                subprocess.run(['explorer', '/select,', file_path], check=True)
            else:  # Linux
                # Try to open the parent directory
                parent_dir = os.path.dirname(file_path)
                subprocess.run(['xdg-open', parent_dir], check=True)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Could not reveal file: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not reveal file: {str(e)}")
    
    def export_list(self):
        """Export the rename list to a CSV file."""
        if not self.rename_data:
            messagebox.showwarning("Warning", "No data to export.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Rename List"
        )
        
        if file_path:
            try:
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Selected', 'Current Name', 'Detected Title', 'New Name', 'Status'])
                    for data in self.rename_data:
                        writer.writerow([data['selected'], data['current_name'], data['detected_title'], 
                                       data['new_name'], data['status']])
                
                messagebox.showinfo("Success", f"Rename list exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export list: {str(e)}")

def main():
    """Main function to run the application."""
    # Check for required dependencies
    try:
        import fitz
    except ImportError:
        print("pymupdf is required but not installed.")
        print("Please install it with: pip install pymupdf")
        
        # Try to show error in GUI if tkinter is available
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Missing Dependency", 
                                "pymupdf is required but not installed.\n"
                                "Please install it with: pip install pymupdf")
            root.destroy()
        except:
            pass
        
        sys.exit(1)
    
    # Create and run the application
    root = tk.Tk()
    app = PatternRenamerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()