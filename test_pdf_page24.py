import pdfplumber

archivo = "ANDE/1740419496_3_1_REDECA_merged.pdf"
with pdfplumber.open(archivo) as pdf:
    # Page index 23 is page 24 (1-indexed)
    if len(pdf.pages) > 23:
        page = pdf.pages[23]
        text_layout = page.extract_text(layout=True)
        text_normal = page.extract_text()
        
        print("--- EXTRACT_TEXT(layout=True) ---")
        lines = text_layout.split('\n')
        for idx in range(min(50, len(lines))):
            print(f"[{idx}] {lines[idx]}")
            
        print("\n--- EXTRACT_TEXT() ---")
        lines = text_normal.split('\n')
        for idx in range(min(50, len(lines))):
            print(f"[{idx}] {lines[idx]}")
    else:
        print(f"Document only has {len(pdf.pages)} pages")
