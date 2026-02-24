import pdfplumber
import re

archivo = "ANDE/1740419496_3_1_REDECA_merged.pdf"
lines_extracted = []
with pdfplumber.open(archivo) as pdf:
    # Page index 23 is page 24
    for i in range(23, len(pdf.pages)):
        text = pdf.pages[i].extract_text(layout=True)
        if not text: continue
        
        for line in text.split('\n'):
            match = re.search(r'^\s*(\d+)\s+.*?\s+(\d+)\s+.*?\s+(\d+)\s+(Ligado|Deslig)', line)
            if match:
                de_bus = int(match.group(1))
                para_bus = int(match.group(2))
                circuito = int(match.group(3))
                estado = 1 if match.group(4) == 'Ligado' else 0
                
                # We can safely use offsets for the rest since they are fixed width
                line_padded = line.ljust(150)
                try:
                    r = float(line_padded[54:62].strip().replace(',', '.'))
                except: r = 0.0
                try:
                    x = float(line_padded[62:70].strip().replace(',', '.'))
                except: x = 0.0
                try:
                    tap = float(line_padded[70:77].strip().replace(',', '.'))
                except: tap = 1.0
                if tap == 0.0: tap = 1.0
                try:
                    rateA = float(line_padded[110:118].strip().replace(',', '.'))
                except: rateA = 0.0
                
                lines_extracted.append((de_bus, para_bus, circuito, estado, r, x, tap, rateA))

print(f"Extracted {len(lines_extracted)} lines")
for i in range(10):
    if i < len(lines_extracted):
        print(lines_extracted[i])
