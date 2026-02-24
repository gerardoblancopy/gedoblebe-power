import pdfplumber
import re
import sys 

archivo_ramas = "ANDE/1740419496_3_1_REDECA_merged.pdf"
text_ramas = ""
with pdfplumber.open(archivo_ramas) as pdf:
    for i, page in enumerate(pdf.pages):
        text_ramas += page.extract_text(layout=True) + "\n"

lines = text_ramas.split('\n')
for i, line in enumerate(lines):
    if "Reat" in line or "Ligado" in line:
        print(f"Line {i}: {line.strip()}")
        # print next 10 lines
        for j in range(1, 15):
            if i+j < len(lines):
                print(lines[i+j])
        break
