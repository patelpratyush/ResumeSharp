#!/usr/bin/env python3

import pdfplumber
import sys

def debug_pdf_extraction(pdf_path):
    print(f"=== DEBUG: Extracting text from {pdf_path} ===")
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"\n--- Page {i+1} ---")
            
            # Try different extraction methods
            layout_text = page.extract_text(layout=True)
            regular_text = page.extract_text()
            
            print("=== LAYOUT EXTRACTION ===")
            print(repr(layout_text[:500]) if layout_text else "None")
            
            print("\n=== REGULAR EXTRACTION ===") 
            print(repr(regular_text[:500]) if regular_text else "None")
            
            # Look specifically for Python mentions
            if layout_text and "python" in layout_text.lower():
                print(f"\n*** PYTHON FOUND IN LAYOUT TEXT ***")
                lines = layout_text.split('\n')
                for j, line in enumerate(lines):
                    if 'python' in line.lower():
                        print(f"Line {j}: {repr(line)}")
                        
            if regular_text and "python" in regular_text.lower():
                print(f"\n*** PYTHON FOUND IN REGULAR TEXT ***")
                lines = regular_text.split('\n')
                for j, line in enumerate(lines):
                    if 'python' in line.lower():
                        print(f"Line {j}: {repr(line)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_pdf.py <pdf_path>")
        sys.exit(1)
    
    debug_pdf_extraction(sys.argv[1])