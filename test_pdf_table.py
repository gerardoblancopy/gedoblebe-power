import pdfplumber
import json

archivo = "ANDE/1740419496_3_1_REDECA_merged.pdf"
with pdfplumber.open(archivo) as pdf:
    for i in range(23, min(26, len(pdf.pages))):
        page = pdf.pages[i]
        text = page.extract_text()
        if "Barra DE" not in text: continue
        
        # ANAREDE tables usually don't have borders, so we might need text strategies
        table = page.extract_table({
            "vertical_strategy": "text", 
            "horizontal_strategy": "text"
        })
        if table:
            print(f"--- Table from page {i+1} ---")
            for row in table[:15]:
                print(row)
            break
        else:
            print(f"No table on page {i+1}")
