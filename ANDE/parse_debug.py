import pdfplumber

def s2f(s):
    s = s.strip()
    if not s: return 0.0
    try: return float(s.replace(',', '.'))
    except: return 0.0

archivo_barras = '1740419496_2_1_REDECA_merged.pdf'
with pdfplumber.open(archivo_barras) as pdf:
    text = pdf.pages[1].extract_text(layout=True)
    for line in text.split('\n'):
        if 'SLO A 23' in line:
            print("LINE:", repr(line))
            
            numero = int(line[0:9].strip())
            nombre = line[28:35].strip()
            
            pd_val = s2f(line[104:111])   # Pd
            qd = s2f(line[111:118])       # Qd
            
            print(f"Num: {numero}, Name: '{nombre}', Pd: {pd_val}, Qd: {qd}")
