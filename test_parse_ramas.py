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
            # Looking for branches: De_Bus, Para_Bus, etc
            # Should have "Ligado" or "Deslig" and start with spaces or a number
            match = re.search(r'^\s*(\d+)\s+.*?\s+(\d+)\s+.*?\s+(\d+)\s+(Ligado|Deslig)', line)
            if match:
                de_bus = int(match.group(1))
                para_bus = int(match.group(2))
                circuito = int(match.group(3))
                estado = match.group(4)
                
                # Split the rest of the line (after estado)
                rest = line[match.end():].split()
                if len(rest) >= 5:
                    # Depending on if there's a Tap, the number of floats changes
                    # E.g. rest might be: ['213', '0,005', '9,24', '1', '40', '48', '40']
                    lines_extracted.append((de_bus, para_bus, circuito, estado, rest))

print(f"Extracted {len(lines_extracted)} lines")
for i in range(10):
    if i < len(lines_extracted):
        print(lines_extracted[i])
