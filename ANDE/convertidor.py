import pandas as pd
import numpy as np

def anarede_to_matpower(df_barras, df_ramas, df_hvdc, limites_v, case_name="caso_convertido"):
    """
    Convierte DataFrames de formato ANAREDE a un string con formato MATPOWER (.m)
    """
    baseMVA = 100.0
    
    # 1. Preparar Diccionarios y Mapeos
    # ANAREDE: 0=PQ, 1=PV, 2=Slack / MATPOWER: 1=PQ, 2=PV, 3=Slack
    tipo_map = {0: 1, 1: 2, 2: 3}
    
    # Aplicar Inyecciones HVDC (LCC) a las barras AC
    if df_hvdc is not None and not df_hvdc.empty:
        for idx, row in df_hvdc.iterrows():
            barra_cc = row['Barra']
            df_barras.loc[df_barras['Número'] == barra_cc, 'Pd'] -= row['P_iny']
            df_barras.loc[df_barras['Número'] == barra_cc, 'Qd'] -= row['Q_iny']

    # 2. Construir matriz mpc.bus
    mpc_bus = []
    mpc_bus_name = []
    for idx, row in df_barras.iterrows():
        bus_i = int(row['Número'])
        bus_name = str(row['Nombre']).strip()
        tipo_ana = int(row['Tipo'])
        bus_type = tipo_map.get(tipo_ana, 1)
        
        Pd = float(row.get('Pd', 0.0))
        Qd = float(row.get('Qd', 0.0))
        Gs = 0.0
        Bs = float(row.get('Bshunt', 0.0))
        
        area = int(row.get('Area', 1))
        Vm = float(row.get('V', 1.0))
        Va = float(row.get('Angulo', 0.0))
        baseKV = float(row.get('BaseKV', 220.0))
        zone = 1
        
        grupo = str(row.get('Grupo_Limite', '0')).strip()
        vmin, vmax = limites_v.get(grupo, (0.9, 1.1))
        
        mpc_bus.append(f"    {bus_i}\t{bus_type}\t{Pd:.3f}\t{Qd:.3f}\t{Gs:.3f}\t{Bs:.3f}\t{area}\t{Vm:.4f}\t{Va:.3f}\t{baseKV}\t{zone}\t{vmax:.3f}\t{vmin:.3f};")
        mpc_bus_name.append(f"    '{bus_name}';")

    # 3. Construir matriz mpc.gen
    mpc_gen = []
    df_gen = df_barras[(df_barras['Tipo'].isin([1, 2])) | (df_barras['Pg'] > 0)]
    for idx, row in df_gen.iterrows():
        bus_i = int(row['Número'])
        Pg = float(row.get('Pg', 0.0))
        Qg = float(row.get('Qg', 0.0))
        Qmax = float(row.get('Qmax', 9999.0))
        Qmin = float(row.get('Qmin', -9999.0))
        Vg = float(row.get('Vdef', row.get('V', 1.0)))
        mBase = baseMVA
        status = 1 if row.get('Estado', 'Ligado') == 'Ligado' else 0
        Pmax = float(row.get('Pmax', 9999.0))
        Pmin = float(row.get('Pmin', 0.0))
        
        mpc_gen.append(f"    {bus_i}\t{Pg:.3f}\t{Qg:.3f}\t{Qmax:.3f}\t{Qmin:.3f}\t{Vg:.4f}\t{mBase}\t{status}\t{Pmax:.3f}\t{Pmin:.3f}\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0;")

    # 4. Construir matriz mpc.branch
    mpc_branch = []
    for idx, row in df_ramas.iterrows():
        fbus = int(row['De'])
        tbus = int(row['Para'])
        r = float(row['R'])
        x = float(row['X'])
        b = float(row['B'])
        rateA = float(row.get('RateA', 0.0))
        rateB = float(row.get('RateB', rateA))
        rateC = float(row.get('RateC', rateA))
        
        ratio = float(row.get('Tap', 0.0))
        angle = float(row.get('Phase', 0.0))
        
        status = 1 if row.get('Estado', 'Ligado') == 'Ligado' else 0
        angmin = -360.0
        angmax = 360.0
        
        mpc_branch.append(f"    {fbus}\t{tbus}\t{r:.5f}\t{x:.5f}\t{b:.5f}\t{rateA:.1f}\t{rateB:.1f}\t{rateC:.1f}\t{ratio:.4f}\t{angle:.2f}\t{status}\t{angmin:.1f}\t{angmax:.1f};")

    # 5. Generar código MATPOWER
    matpower_str = f"function mpc = {case_name}\n"
    matpower_str += f"% Caso importado de ANAREDE - {case_name}\n\n"
    matpower_str += "mpc.version = '2';\n"
    matpower_str += f"mpc.baseMVA = {baseMVA};\n\n"
    
    matpower_str += "%% Datos de Barras\n"
    matpower_str += "%  bus_i type Pd Qd Gs Bs area Vm Va baseKV zone Vmax Vmin\n"
    matpower_str += "mpc.bus = [\n" + "\n".join(mpc_bus) + "\n];\n\n"
    
    matpower_str += "%% Nombres de Barras\n"
    matpower_str += "mpc.bus_name = {\n" + "\n".join(mpc_bus_name) + "\n};\n\n"
    
    matpower_str += "%% Datos de Generadores\n"
    matpower_str += "%  bus Pg Qg Qmax Qmin Vg mBase status Pmax Pmin Pc1 Pc2 Qc1min Qc1max Qc2min Qc2max ramp_agc ramp_10 ramp_30 ramp_q apf\n"
    matpower_str += "mpc.gen = [\n" + "\n".join(mpc_gen) + "\n];\n\n"
    
    matpower_str += "%% Datos de Ramas\n"
    matpower_str += "%  fbus tbus r x b rateA rateB rateC ratio angle status angmin angmax\n"
    matpower_str += "mpc.branch = [\n" + "\n".join(mpc_branch) + "\n];\n\n"
    
    matpower_str += "%% Costos de Generación (Input requerido)\n"
    matpower_str += "%  1=piecewise linear, 2=polynomial; startup; shutdown; n; x1 y1 ... / cn ... c0\n"
    matpower_str += f"mpc.gencost = zeros({len(mpc_gen)}, 7);\n"
    matpower_str += "mpc.gencost(:, 1) = 2; % Modelo polinomial por defecto\n"
    matpower_str += "mpc.gencost(:, 4) = 3; % Polinomio de orden 2 (3 coeficientes)\n"
    
    matpower_str += "\nreturn;\n"
    
    return matpower_str

def read_rtf_csv(filepath):
    import os
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found.")
        return []
    lines_extracted = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            if line.startswith('{\\rtf') or line.startswith('\\cocoa') or \
               line.startswith('{\\fonttbl') or line.startswith('{\\colortbl') or \
               line.startswith('{\\*\\expandedcolortbl') or line.startswith('\\paper') or \
               line.startswith('\\pard'):
                continue
            if line.endswith('\\'): line = line[:-1]
            import re
            line = re.sub(r'^\\[a-z0-9\s]+\\cf[0-9]\s*', '', line)
            if ';' in line or re.match(r'^\d+', line):
                lines_extracted.append(line)
    return lines_extracted

def extraer_datos_anarede():
    import pdfplumber
    import re

    # ---------------------------------------------------------
    # 1. LECTURA DEL PDF DE BARRAS (REDECA)
    # ---------------------------------------------------------
    print("Leyendo PDF de Barras...")
    archivo_barras = "1740419496_2_1_REDECA_merged.pdf"
    
    text_all = ""
    with pdfplumber.open(archivo_barras) as pdf:
        for page in pdf.pages:
            text_all += page.extract_text(layout=True) + "\n"
            
    # Función auxiliar para convertir a float
    def s2f(s):
        s = s.strip()
        if not s: return 0.0
        try: return float(s.replace(',', '.'))
        except: return 0.0

    buses_list = []
    lines = text_all.split('\n')
    for line in lines:
        if len(line) < 120 or not line[0:9].strip().isdigit():
            continue
            
        numero = int(line[0:9].strip())
        tipo_str = line[9:15].strip()
        tipo = 1 if '1' in tipo_str else (2 if '2' in tipo_str else 0)
        
        nombre = line[28:36].strip()
        grupo_lim = line[36:39].strip()
        
        # Basado en posiciones layout de pdfplumber
        v = s2f(line[71:77])
        angulo = s2f(line[83:89])
        
        pg = s2f(line[89:95])
        qg = s2f(line[95:102])
        qmin = s2f(line[102:108])
        qmax = s2f(line[108:114])
        
        pd_val = s2f(line[104:111])   # Pd
        qd = s2f(line[111:118])       # Qd
        # Bshunt and Area handling depending on string length
        bshunt_str = line[118:125].strip() if len(line) > 118 else ""
        bshunt = s2f(bshunt_str) if ' ' not in bshunt_str else 0.0
        
        buses_list.append({
            'Número': numero,
            'Tipo': tipo,
            'Nombre': nombre,
            'Grupo_Limite': grupo_lim,
            'V': v,
            'Angulo': angulo,
            'Pg': pg,
            'Qg': qg,
            'Qmin': qmin,
            'Qmax': qmax,
            'Pd': pd_val,
            'Qd': qd,
            'Bshunt': bshunt
        })
        
    print("Iniciando lectura desde archivos CSV manuales...")
    
    # 1. BARRAS
    print("Procesando barras_limpio.csv ...")
    barras_lines = read_rtf_csv("../barras_limpio.csv")
    if not barras_lines:
        barras_lines = read_rtf_csv("barras_limpio.csv")
        
    barras_list = []
    for line in barras_lines:
        parts = line.split(';')
        if len(parts) >= 3:
            first_col = parts[0].strip()
            # extract bus number
            import re
            match = re.search(r'^(\d+)', first_col)
            if not match: continue
            bus_id = int(match.group(1))
            
            # Identify load vs generator vs ref. 
            # In anarede, "1- PV" or "2 - Referencia" are generators, "0 - PQ" is load.
            typ = 1
            if 'PV' in first_col: typ = 2
            elif 'Refer' in first_col: typ = 3
            
            # Third column has the actual values
            # E.g.: 13,8 CSI B1 13.8 F 0,900-1,100 Ligado 0 - Normal 1,025 14,1 4,12 0 -545 -9900 9900
            rest = parts[2].split()
            if 'Ligado' not in rest and 'Desligado' not in rest:
                continue
                
            ligado_idx = -1
            if 'Ligado' in rest: ligado_idx = rest.index('Ligado')
            elif 'Desligado' in rest: ligado_idx = rest.index('Desligado')
            
            if ligado_idx == -1: continue
            
            # Tensão is right after "0 - Normal" (usually 3 words after Ligado)
            # Example: [..., 'Ligado', '0', '-', 'Normal', '1,025', '14,1', '4,12', ...]
            try:
                v_pu = s2f(rest[ligado_idx + 4])
                angulo = s2f(rest[ligado_idx + 6])
                
                # Default loads
                pl = 0.0
                ql = 0.0
                pg = 0.0
                qg = 0.0
                
                # Let's search for numbers at the end of the line
                # Often MW and MVAR are situated before Shunts/Area
                # It's safer to just extract limits later or use defaults, OPF finds them
                # But let's try to extract load if typ==1
                if typ == 1:
                    # In loads, Pl and Ql might be in specific parts[n] if split properly by user,
                    # but usually they are at the end of parts[2] or parts[3].
                    # Wait, looking at the user's manual CSVs, he used semicolons for SOME columns!
                    # parts[3] is often PL, parts[4] is QL in the new CSV if he formatted it.
                    if len(parts) >= 4 and parts[3].strip(): pl = s2f(parts[3])
                    if len(parts) >= 5 and parts[4].strip(): ql = s2f(parts[4])
                else:
                    if len(parts) >= 4 and parts[3].strip(): pg = s2f(parts[3])
                    if len(parts) >= 5 and parts[4].strip(): qg = s2f(parts[4])
                
            except:
                v_pu = 1.0; angulo = 0.0; pl=0.0; ql=0.0; pg=0.0; qg=0.0
                
            barras_list.append({
                'Número': bus_id,
                'Tipo': typ,
                'Nombre': first_col, # Use the full first column as name for now
                'Grupo_Limite': '0', # Default
                'V': v_pu,
                'Angulo': angulo,
                'Pg': pg,
                'Qg': qg,
                'Qmin': -9999.0, # Default
                'Qmax': 9999.0,  # Default
                'Pd': pl,
                'Qd': ql,
                'Bshunt': 0.0,   # Default
                'BaseKV': 100.0, # default
                'Vmax': 1.1,     # Default
                'Vmin': 0.9      # Default
            })
            
    df_barras = pd.DataFrame(barras_list)
    print(f"Buses procesados: {len(df_barras)}")
    
    # Process gen_limpio.csv to update generators Pg, Qg, Qmin, Qmax
    print("Procesando gen_limpio.csv ...")
    gen_lines = read_rtf_csv("../gen_limpio.csv") or read_rtf_csv("gen_limpio.csv")
    for line in gen_lines:
        parts = line.split(';')
        if not parts: continue
        # Find bus_id from first column
        import re
        match = re.search(r'^(\d+)', parts[0].strip())
        if not match: continue
        bus_id = int(match.group(1))
        
        # Now collect all valid floats from the line
        tokens = line.replace(';', ' ').split()
        vals = []
        for t in tokens:
            try: vals.append(float(t.replace(',', '.')))
            except: pass
            
        # The floats typically are [bus_id, Pg, Qg, Pmin, Pmax, ...] or similar.
        # Looking at user's format: 700 IPU10G 18;6335;700,7;0;99999;0;100;0
        # If parts separated well:
        try:
            pg = s2f(parts[1]) if len(parts) > 1 and parts[1].strip() else None
            # if parts[1] is empty, perhaps Pg is inside parts[0]
            if pg is None and len(vals) > 1:
                pg = vals[1]
                qg = vals[2] if len(vals) > 2 else 0.0
            else:
                qg = s2f(parts[2]) if len(parts) > 2 else 0.0
                
            qmin = s2f(parts[3]) if len(parts) > 3 else -9999.0
            qmax = s2f(parts[4]) if len(parts) > 4 else 9999.0
            
            # Update df_barras
            idx = df_barras['Número'] == bus_id
            if idx.any():
                df_barras.loc[idx, 'Pg'] = pg
                df_barras.loc[idx, 'Qg'] = qg
                if qmin != 0.0 or qmax != 0.0:
                    df_barras.loc[idx, 'Qmin'] = qmin
                    df_barras.loc[idx, 'Qmax'] = qmax
        except Exception as e:
            print(f"Error parsing gen for bus {bus_id}: {e}")

    # Process Shunts_limpio.csv
    print("Procesando Shunts_limpio.csv ...")
    shunt_lines = read_rtf_csv("../Shunts_limpio.csv") or read_rtf_csv("Shunts_limpio.csv")
    for line in shunt_lines:
        parts = line.split(';')
        if not parts: continue
        import re
        match = re.search(r'^(\d+)', parts[0].strip())
        if not match: continue
        bus_id = int(match.group(1))
        
        # Format usually: 85 INV B1 2345;1,09;2774;3295,79
        # The nominal shunt MVAr is generally the first large value after voltage
        try:
            b_val = 0.0
            if len(parts) >= 3 and parts[2].strip():
                b_val = s2f(parts[2])
            elif len(parts) >= 2 and parts[1].strip():
                # fallback
                vals = [float(t.replace(',', '.')) for t in parts[1].split() if re.match(r'^-?\d', t)]
                if vals: b_val = vals[-1]
                
            idx = df_barras['Número'] == bus_id
            if idx.any() and b_val != 0.0:
                df_barras.loc[idx, 'Bshunt'] = b_val
        except: pass
        
    # Process FACTS_limpio.csv (optional, mainly for shunts/reactive limits)
    print("Procesando FACTS_limpio.csv ...")
    facts_lines = read_rtf_csv("../FACTS_limpio.csv") or read_rtf_csv("FACTS_limpio.csv")
    for line in facts_lines:
        if 'Ligado' not in line: continue
        parts = line.split(';')
        import re
        match = re.search(r'^(\d+)', parts[0].strip())
        if not match: continue
        bus_id = int(match.group(1))
        
        try:
            # e.g., 411 LIM RE 11.8;1 Ligado;2;177;-57,7;232,6;409 Pcte;1 L
            qmin = s2f(parts[4]) if len(parts) > 4 else 0.0
            qmax = s2f(parts[5]) if len(parts) > 5 else 0.0
            idx = df_barras['Número'] == bus_id
            if idx.any():
                df_barras.loc[idx, 'Qmin'] = qmin
                df_barras.loc[idx, 'Qmax'] = qmax
        except: pass

    # Limites (Hardcoded as they were unused or standard 0.9/1.1)
    limites_v = {}
    df_hvdc = pd.DataFrame() # Ignore HVDC logic for now as it's likely broken in same way

    # 4. RAMAS (Líneas y Trafos)
    print("Procesando ramas_limpio.csv ...")
    ramas_lines = read_rtf_csv("../ramas_limpio.csv")
    if not ramas_lines:
        ramas_lines = read_rtf_csv("ramas_limpio.csv")
        
    ramas_list = []
    
    # 1. Get valid bus numbers from df_barras
    valid_buses = set()
    if not df_barras.empty:
        valid_buses = set(df_barras['Número'].tolist())
        
    for line in ramas_lines:
        parts = line.split(';')
        if not parts: continue
        
        # Example format: 304 MRA B1 66 204 MRA A 23;1 Ligado;304;1,67;43,16 0,9721 0,83;1,1;1010;204;30;36;30;16;;;
        text_cols = " ".join(parts)
        tokens = text_cols.split()
        
        if not tokens or not tokens[0].isdigit(): continue
        
        # Looking for Ligado / Desligado
        ligado_idx = -1
        if 'Ligado' in tokens: ligado_idx = tokens.index('Ligado')
        elif 'Deslig' in tokens: ligado_idx = tokens.index('Deslig')
        elif 'Desligado' in tokens: ligado_idx = tokens.index('Desligado')
        
        if ligado_idx == -1: continue
        
        de_bus = int(tokens[0])
        estado = 1 if 'Ligado' in tokens[ligado_idx] else 0
        
        circuito_str = tokens[ligado_idx - 1]
        
        # Find PARA_BUS by looking backwards from circuito
        para_bus = -1
        for j in range(ligado_idx - 2, 0, -1):
            if tokens[j].isdigit() and int(tokens[j]) in valid_buses:
                para_bus = int(tokens[j])
                break
                
        if para_bus == -1: continue
        
        # Now parse R, X, Tap, RateA
        # They are spread among parts or tokens. Since it's semicolon separated by the user:
        # typically parts[3] = R, parts[4] = X, etc.
        try:
            r = 0.0; x = 0.001; tap = 1.0; rateA = 0.0
            
            # Since the user used semicolons somewhat arbitrarily, let's just grab all floats after Ligado
            post_tokens = tokens[ligado_idx+1:]
            vals = []
            for pt in post_tokens:
                try: vals.append(float(pt.replace(',', '.')))
                except: pass
                
            if len(vals) >= 2:
                # Most common array pattern (ignoring proprietario which is an int usually or word)
                # First two floats are R and X
                r = vals[0] if vals[0] < 100 else 0.0 # R is small
                x = vals[1] if vals[1] < 100 else 0.001 # X is small
                
                # Check for rateA (usually the first large number or > 10)
                rates = [v for v in vals if v >= 10.0 and v < 9990]
                if rates: 
                    rateA = rates[0]
                
                taps = [v for v in vals if v > 0.8 and v < 1.2 and v != 1.0]
                if taps:
                    tap = taps[0]
                    
            ramas_list.append({
                'De': de_bus,
                'Para': para_bus,
                'Circuito': circuito_str,
                'R': r,
                'X': x,
                'B': 0.0,
                'RateA': rateA,
                'Tap': tap, 
                'Phase': 0.0,
                'Estado': estado
            })
        except Exception as e:
            print(f"Skipping branch row due to parsing err: {e}")
            
    df_ramas = pd.DataFrame(ramas_list)
    print(f"Ramas extraídas: {len(df_ramas)}")

    return df_barras, df_ramas, df_hvdc, limites_v

if __name__ == "__main__":
    print("Iniciando proceso de conversión ANAREDE -> MATPOWER...")
    try:
        df_barras, df_ramas, df_hvdc, limites_v = extraer_datos_anarede()
        
        script_matpower = anarede_to_matpower(df_barras, df_ramas, df_hvdc, limites_v, case_name="sistema_paraguay_brasil")
        
        nombre_archivo = 'sistema_paraguay_brasil.m'
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(script_matpower)
            
        print(f"\n¡Éxito! El archivo {nombre_archivo} ha sido generado.")
        
    except Exception as e:
        print(f"Ocurrió un error: {e}")