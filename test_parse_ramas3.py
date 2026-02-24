import pdfplumber
import re

def s2f(s):
    s = s.strip()
    if not s: return 0.0
    try: return float(s.replace(',', '.'))
    except: return 0.0

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
                
                rest = line[match.end():].split()
                if len(rest) >= 5:
                    r = s2f(rest[1])
                    x = s2f(rest[2])
                    tap = s2f(rest[3])
                    
                    if tap == 1.0 or tap == 0.0:
                        tap = 1.0
                        # Usually RateA is at index 4
                        try: rateA = s2f(rest[4])
                        except: rateA = 0.0
                    else:
                        # Has Tap Min, Max, Tensao Def, Barra Controlada
                        try: rateA = s2f(rest[8])
                        except: rateA = 0.0
                        
                    lines_extracted.append((de_bus, para_bus, circuito, estado, r, x, tap, rateA))

print(f"Extracted {len(lines_extracted)} lines")
for i in range(15):
    if i < len(lines_extracted):
        print(lines_extracted[i])
