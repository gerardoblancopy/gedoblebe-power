import pdfplumber

archivo = "ANDE/1740419496_3_1_REDECA_merged.pdf"
with pdfplumber.open(archivo) as pdf:
    # Page index 23 is page 24 (1-indexed)
    page = pdf.pages[23]
    text_layout = page.extract_text(layout=True)
    lines = text_layout.split('\n')
    
    print("0123456789" * 15)
    print("0         1         2         3         4         5         6         7         8         9         10        11        12        13        14")
    
    for idx in [5, 6, 7, 11, 18]:
        if idx < len(lines):
            print(lines[idx])

