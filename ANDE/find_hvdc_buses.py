import sys
sys.path.append('.')
from convertidor import extraer_datos_anarede
try:
    df_barras, _, _, _ = extraer_datos_anarede(
        'Copia de ANAREDE - Barras - Escenario 2.pdf',
        'Copia de ANAREDE - Ramas - Escenario 2.pdf',
        'Copia de ANAREDE - Elo CC - Escenario 2.pdf',
        'Copia de ANAREDE - Limites de Tension - Escenario 2.pdf'
    )
    for index, row in df_barras.iterrows():
        name = str(row.get('Nombre', '')).upper()
        if 'FOZ' in name or 'ROQUE' in name or 'IBIUNA' in name or 'ITAIPU' in name or 'HVDC' in name or 'ELO CC' in name:
            print(f"Match: Bus {row.get('Número')} - {name}")
except Exception as e:
    import traceback
    traceback.print_exc()
