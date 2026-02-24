import pdfplumber
import re

def s2f(s):
    s = s.strip()
    if not s: return 0.0
    try: return float(s.replace(',', '.'))
    except: return 0.0

ramas_list = []
with pdfplumber.open('1740419496_2_1_REDECA_merged.pdf') as pdf:
    for page in pdf.pages:
        text = page.extract_text(layout=True)
        lines = text.split('\n')
        for line in lines:
            line_s = line.strip()
            if re.match(r'^\d+', line_s) and ('Ligado' in line_s or 'Deslig' in line_s):
                parts = line_s.split()
                # find indices of 'Ligado' or 'Deslig'
                ligado_idx = [i for i, x in enumerate(parts) if 'Ligado' in x or 'Deslig' in x]
                if len(ligado_idx) >= 3 and len(parts) >= 12:
                    try:
                        de_bus = int(parts[0])
                        para_bus_str = parts[ligado_idx[0]+1]
                        if not para_bus_str.isdigit(): continue
                        para_bus = int(para_bus_str)
                        
                        r = s2f(parts[-7])
                        x = s2f(parts[-6])
                        b = s2f(parts[-4])
                        rateA = s2f(parts[-3])
                        
                        estado = 1 if 'Ligado' in parts[ligado_idx[2]] else 0
                        circuit = parts[ligado_idx[1]+1]
                        
                        ramas_list.append({
                            'De': de_bus,
                            'Para': para_bus,
                            'Circuito': circuit,
                            'R': r,
                            'X': x,
                            'B': b,
                            'RateA': rateA,
                            'Tap': 1.0,   # assuming líneas until we parse transformers
                            'Phase': 0.0,
                            'Estado': estado
                        })
                    except:
                        pass
print(f"Buses: {ramas_list[0]}")
print(f"Buses: {ramas_list[-1]}")
print("Found branches:", len(ramas_list))
