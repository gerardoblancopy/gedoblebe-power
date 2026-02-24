import pdfplumber

archivo = "ANDE/1740419496_3_1_REDECA_merged.pdf"
with pdfplumber.open(archivo) as pdf:
    for i in range(23, min(30, len(pdf.pages))):
        text = pdf.pages[i].extract_text()
        if text and "Barra DE" in text:
            print(f"--- Page {i+1} ---")
            lines = text.split('\n')
            for j in range(min(20, len(lines))):
                print(lines[j])
            break
