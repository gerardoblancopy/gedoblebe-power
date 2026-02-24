import pdfplumber
import re
import sys 

archivo_ramas = "ANDE/1740419496_3_1_REDECA_merged-2.pdf"
text_ramas = ""
with pdfplumber.open(archivo_ramas) as pdf:
    for i, page in enumerate(pdf.pages):
        text_ramas += page.extract_text(layout=True) + "\n"
        if i >= 1: # just first 2 pages
            break

count = 0
for line in text_ramas.split('\n'):
    line_s = line.strip()
    if line_s and line_s[0].isdigit():
        print(line_s)
        count += 1
        if count >= 30: break
