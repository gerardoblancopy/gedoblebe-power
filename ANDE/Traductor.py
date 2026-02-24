import pandas as pd
import numpy as np

def anarede_to_matpower(df_barras, df_ramas, df_hvdc, limites_v, case_name="caso_convertido"):
    """
    Convierte DataFrames de formato ANAREDE a un string con formato MATPOWER (.m)
    
    Parámetros:
    - df_barras: DataFrame con datos de barras (Número, Nombre, Tipo, Grupo Limite, V, Angulo, Pg, Qg, Pd, Qd, Bshunt)
    - df_ramas: DataFrame con datos de líneas y transformadores (De, Para, R, X, B, RateA, Tap, Phase)
    - df_hvdc: DataFrame con las inyecciones equivalentes de los enlaces CC (Barra, P_iny, Q_iny)
    - limites_v: Diccionario con los límites de tensión ej. {'F': (0.9, 1.1), 'M': (0.9, 1.1)}
    """
    
    baseMVA = 100.0
    
    # 1. Preparar Diccionarios y Mapeos
    # ANAREDE: 0=PQ, 1=PV, 2=Slack / MATPOWER: 1=PQ, 2=PV, 3=Slack
    tipo_map = {0: 1, 1: 2, 2: 3}
    
    # Aplicar Inyecciones HVDC (LCC) a las barras AC
    # Asumimos que df_hvdc tiene inyecciones positivas hacia la barra.
    # MATPOWER define demanda (Pd, Qd) saliendo de la barra, por lo que Inyección = -Demanda
    if df_hvdc is not None and not df_hvdc.empty:
        for idx, row in df_hvdc.iterrows():
            barra_cc = row['Barra']
            # Restamos la inyección a la demanda existente (si inyecta 100MW, demanda baja 100MW)
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
        Gs = 0.0 # Conductancia shunt (raro en ANAREDE, usualmente 0)
        Bs = float(row.get('Bshunt', 0.0)) # Susceptancia shunt
        
        area = int(row.get('Area', 1))
        Vm = float(row.get('V', 1.0))
        Va = float(row.get('Angulo', 0.0))
        baseKV = float(row.get('BaseKV', 220.0))
        zone = 1
        
        # Asignar límites según el grupo
        grupo = str(row.get('Grupo_Limite', '0')).strip()
        vmin, vmax = limites_v.get(grupo, (0.9, 1.1)) # Default 0.9 - 1.1 si no existe
        
        mpc_bus.append(f"    {bus_i}\t{bus_type}\t{Pd:.3f}\t{Qd:.3f}\t{Gs:.3f}\t{Bs:.3f}\t{area}\t{Vm:.4f}\t{Va:.3f}\t{baseKV}\t{zone}\t{vmax:.3f}\t{vmin:.3f};")
        mpc_bus_name.append(f"    '{bus_name}';")

    # 3. Construir matriz mpc.gen
    mpc_gen = []
    # Filtramos generadores (PV, Slack, o cualquier barra con Pg > 0)
    df_gen = df_barras[(df_barras['Tipo'].isin([1, 2])) | (df_barras['Pg'] > 0)]
    for idx, row in df_gen.iterrows():
        bus_i = int(row['Número'])
        Pg = float(row.get('Pg', 0.0))
        Qg = float(row.get('Qg', 0.0))
        Qmax = float(row.get('Qmax', 9999.0))
        Qmin = float(row.get('Qmin', -9999.0))
        Vg = float(row.get('Vdef', row.get('V', 1.0))) # Tensión de consigna
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
        rateA = float(row.get('RateA', 0.0)) # Capacidad normal
        rateB = float(row.get('RateB', rateA))
        rateC = float(row.get('RateC', rateA))
        
        # Transformadores: ratio (tap) y angle (desfase)
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

# --- EJEMPLO DE USO ---
if __name__ == "__main__":
    # Limites extraidos de GRUPO_LIMITE_merged.pdf
    limites_v = {
        'F': (0.90, 1.10),
        'M': (0.90, 1.10),
        'H': (0.90, 1.10),
        'B': (0.90, 1.10),
        '1': (0.90, 1.10),
        '0': (0.95, 1.05),
        'KOJGENL': (0.90, 1.10)
    }
    
    # Aquí cargarías tus CSVs limpios generados a partir de los reportes
    # df_barras = pd.read_csv('barras.csv')
    # df_ramas = pd.read_csv('ramas.csv')
    # df_hvdc = pd.read_csv('hvdc_inyecciones.csv')
    
    # string_matpower = anarede_to_matpower(df_barras, df_ramas, df_hvdc, limites_v)
    
    # with open('caso_anarede_mpc.m', 'w', encoding='utf-8') as f:
    #     f.write(string_matpower)
    # print("Conversión completada. Archivo caso_anarede_mpc.m generado.")