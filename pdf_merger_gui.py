#!/usr/bin/env python3
"""
PDF Merger GUI
A simple graphical user interface for the PDF merger application.

Author: GitHub Copilot
Date: December 2, 2025
"""

import os
import sys
import threading
from pathlib import Path
from tkinter import *
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

# Import our main PDF merger class
try:
    from pdf_merger import PDFMerger
except ImportError:
    messagebox.showerror("Error", "Could not import pdf_merger module. Make sure pdf_merger.py is in the same directory.")
    sys.exit(1)


class PDFMergerGUI:
    """GUI wrapper for the PDF Merger application."""
    
    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("PDF Merger & Compressor")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Variables
        self.pdf_files = []
        self.output_dir = StringVar(value="output")
        self.output_name = StringVar()
        self.email_limit = DoubleVar(value=25.0)
        
        # Create GUI elements
        self.create_widgets()
        
        # PDF Merger instance
        self.merger = None
        
    def create_widgets(self):
        """Create and layout GUI widgets."""
        
        # Main frame
        main_frame = Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Title
        title_label = Label(main_frame, text="PDF Merger & Compressor", 
                           font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # File selection frame
        file_frame = LabelFrame(main_frame, text="Select PDF Files", padx=10, pady=10)
        file_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        # File list
        self.file_listbox = Listbox(file_frame, height=8)
        self.file_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Scrollbar for file list
        scrollbar = Scrollbar(file_frame, orient=VERTICAL)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Button frame for file operations
        file_btn_frame = Frame(file_frame)
        file_btn_frame.pack(side=RIGHT, fill=Y, padx=(10, 0))
        
        Button(file_btn_frame, text="Add Files", command=self.add_files).pack(fill=X, pady=(0, 5))
        Button(file_btn_frame, text="Add Folder", command=self.add_folder).pack(fill=X, pady=(0, 5))
        Button(file_btn_frame, text="Remove Selected", command=self.remove_selected).pack(fill=X, pady=(0, 5))
        Button(file_btn_frame, text="Clear All", command=self.clear_all).pack(fill=X, pady=(0, 5))
        
        # Settings frame
        settings_frame = LabelFrame(main_frame, text="Settings", padx=10, pady=10)
        settings_frame.pack(fill=X, pady=(0, 10))
        
        # Output directory
        dir_frame = Frame(settings_frame)
        dir_frame.pack(fill=X, pady=(0, 5))
        Label(dir_frame, text="Output Directory:").pack(side=LEFT)
        Entry(dir_frame, textvariable=self.output_dir, width=30).pack(side=LEFT, padx=(10, 5))
        Button(dir_frame, text="Browse", command=self.browse_output_dir).pack(side=LEFT)
        
        # Output filename
        name_frame = Frame(settings_frame)
        name_frame.pack(fill=X, pady=(0, 5))
        Label(name_frame, text="Output Filename (optional):").pack(side=LEFT)
        Entry(name_frame, textvariable=self.output_name, width=30).pack(side=LEFT, padx=(10, 0))
        
        # Email size limit
        limit_frame = Frame(settings_frame)
        limit_frame.pack(fill=X, pady=(0, 5))
        Label(limit_frame, text="Email Size Limit (MB):").pack(side=LEFT)
        Entry(limit_frame, textvariable=self.email_limit, width=10).pack(side=LEFT, padx=(10, 0))
        
        # Action buttons
        action_frame = Frame(main_frame)
        action_frame.pack(fill=X, pady=(0, 10))
        
        self.process_btn = Button(action_frame, text="Merge & Compress PDFs", 
                                 command=self.start_processing, bg="#4CAF50", fg="white",
                                 font=("Arial", 12, "bold"))
        self.process_btn.pack(side=LEFT, padx=(0, 10))
        
        Button(action_frame, text="Open Output Folder", 
               command=self.open_output_folder).pack(side=LEFT)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=X, pady=(0, 10))
        
        # Log output
        log_frame = LabelFrame(main_frame, text="Log Output", padx=10, pady=10)
        log_frame.pack(fill=BOTH, expand=True)
        
        self.log_text = ScrolledText(log_frame, height=8, state=DISABLED)
        self.log_text.pack(fill=BOTH, expand=True)
        
    def add_files(self):
        """Add PDF files to the list."""
        files = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        for file in files:
            if file not in self.pdf_files:
                self.pdf_files.append(file)
                self.file_listbox.insert(END, os.path.basename(file))
                
    def add_folder(self):
        """Add all PDF files from a folder."""
        folder = filedialog.askdirectory(title="Select Folder with PDF Files")
        
        if folder:
            pdf_files = list(Path(folder).glob("*.pdf"))
            
            for pdf_file in pdf_files:
                file_path = str(pdf_file)
                if file_path not in self.pdf_files:
                    self.pdf_files.append(file_path)
                    self.file_listbox.insert(END, pdf_file.name)
                    
    def remove_selected(self):
        """Remove selected files from the list."""
        selection = self.file_listbox.curselection()
        
        for index in reversed(selection):
            self.file_listbox.delete(index)
            del self.pdf_files[index]
            
    def clear_all(self):
        """Clear all files from the list."""
        self.file_listbox.delete(0, END)
        self.pdf_files.clear()
        
    def browse_output_dir(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        
        if directory:
            self.output_dir.set(directory)
            
    def open_output_folder(self):
        """Open the output folder in file explorer."""
        output_path = Path(self.output_dir.get())
        
        if output_path.exists():
            if sys.platform == "win32":
                os.startfile(output_path)
            elif sys.platform == "darwin":  # macOS
                os.system(f"open '{output_path}'")
            else:  # Linux
                os.system(f"xdg-open '{output_path}'")
        else:
            messagebox.showwarning("Warning", f"Output directory '{output_path}' does not exist.")
            
    def log_message(self, message):
        """Add a message to the log output."""
        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, message + "\n")
        self.log_text.config(state=DISABLED)
        self.log_text.see(END)
        self.root.update_idletasks()
        
    def start_processing(self):
        """Start the PDF processing in a separate thread."""
        if not self.pdf_files:
            messagebox.showwarning("Warning", "Please select at least one PDF file.")
            return
            
        # Disable the process button and start progress
        self.process_btn.config(state=DISABLED)
        self.progress.start()
        
        # Clear log
        self.log_text.config(state=NORMAL)
        self.log_text.delete(1.0, END)
        self.log_text.config(state=DISABLED)
        
        # Start processing in a separate thread
        thread = threading.Thread(target=self.process_pdfs)
        thread.daemon = True
        thread.start()
        
    def process_pdfs(self):
        """Process the PDFs (runs in separate thread)."""
        try:
            self.log_message("Starting PDF processing...")
            
            # Create merger instance
            self.merger = PDFMerger(self.output_dir.get())
            
            # Redirect logging to our log widget
            import logging
            
            class GUILogHandler(logging.Handler):
                def __init__(self, gui):
                    super().__init__()
                    self.gui = gui
                    
                def emit(self, record):
                    msg = self.format(record)
                    self.gui.log_message(msg)
            
            # Add GUI log handler
            gui_handler = GUILogHandler(self)
            gui_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            self.merger.logger.addHandler(gui_handler)
            
            # Process files
            output_name = self.output_name.get() if self.output_name.get().strip() else None
            merged_pdf, compressed_file = self.merger.process_pdfs(
                self.pdf_files,
                output_name,
                self.email_limit.get()
            )
            
            self.log_message("\n" + "="*50)
            self.log_message("PROCESSING COMPLETED SUCCESSFULLY!")
            self.log_message("="*50)
            self.log_message(f"Merged PDF: {merged_pdf}")
            self.log_message(f"Compressed file: {compressed_file}")
            self.log_message("="*50)
            
            # Show success message
            self.root.after(0, lambda: messagebox.showinfo(
                "Success", 
                f"PDFs merged and compressed successfully!\n\n"
                f"Merged PDF: {os.path.basename(merged_pdf)}\n"
                f"Compressed file: {os.path.basename(compressed_file)}"
            ))
            
        except Exception as e:
            error_msg = f"Error during processing: {str(e)}"
            self.log_message(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            
        finally:
            # Re-enable button and stop progress
            self.root.after(0, self._processing_finished)
            
    def _processing_finished(self):
        """Called when processing is finished (runs in main thread)."""
        self.progress.stop()
        self.process_btn.config(state=NORMAL)


def main():
    """Main entry point for the GUI application."""
    root = Tk()
    app = PDFMergerGUI(root)
    
    # Center the window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()