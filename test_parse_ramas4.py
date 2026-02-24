import pdfplumber

def s2f(s):
    s = s.strip()
    if not s: return 0.0
    try: return float(s.replace(',', '.'))
    except: return 0.0

archivo_barras = "ANDE/1740419496_2_1_REDECA_merged.pdf"
archivo_ramas = "ANDE/1740419496_3_1_REDECA_merged.pdf"

# 1. Get valid bus numbers
valid_buses = set()
with pdfplumber.open(archivo_barras) as pdf:
    for page in pdf.pages:
        for line in page.extract_text().split('\n'):
            line = line.strip()
            if line and line.split()[0].isdigit():
                valid_buses.add(int(line.split()[0]))

print(f"Loaded {len(valid_buses)} valid buses.")

# 2. Parse branches
lines_extracted = []
with pdfplumber.open(archivo_ramas) as pdf:
    for i in range(23, len(pdf.pages)):
        text = pdf.pages[i].extract_text()
        if not text: continue
        
        for line in text.split('\n'):
            parts = line.split()
            if not parts or not parts[0].isdigit(): continue
            
            ligado_idx = -1
            if 'Ligado' in parts: ligado_idx = parts.index('Ligado')
            elif 'Deslig' in parts: ligado_idx = parts.index('Deslig')
            
            if ligado_idx == -1: continue
            
            de_bus = int(parts[0])
            circuito = int(parts[ligado_idx - 1])
            estado = 1 if parts[ligado_idx] == 'Ligado' else 0
            
            # Find PARA_BUS by looking backwards from circuito
            para_bus = -1
            for j in range(ligado_idx - 2, 0, -1):
                if parts[j].isdigit() and int(parts[j]) in valid_buses:
                    # Is it really the para_bus? Tensions like 66 might also be valid bus numbers?
                    # Bus 66 exists? No, mostly 23, 66 are voltages, but let's check.
                    para_bus = int(parts[j])
                    break
                    
            if para_bus == -1: continue
            
            rest = parts[ligado_idx+1:]
            if len(rest) >= 4:
                # rest[0] = Proprietario
                r = s2f(rest[1])
                x = s2f(rest[2])
                tap = s2f(rest[3])
                
                if tap == 1.0 or tap == 0.0:
                    tap = 1.0
                    try: rateA = s2f(rest[4])
                    except: rateA = 0.0
                else:
                    try: rateA = s2f(rest[8])
                    except: rateA = 0.0
                    
                lines_extracted.append((de_bus, para_bus, circuito, estado, r, x, tap, rateA))

print(f"Extracted {len(lines_extracted)} branches.")
for i in range(15):
    if i < len(lines_extracted):
        print(lines_extracted[i])
