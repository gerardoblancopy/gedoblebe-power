import convertidor
import Traductor

df_barras, df_ramas, df_hvdc, limites_v = convertidor.extraer_datos_anarede()

matpower_str = Traductor.anarede_to_matpower(df_barras, df_ramas, df_hvdc, limites_v, case_name="case_ANDE")

output_path = '../backend/app/cases/case_ANDE.m'
with open(output_path, 'w') as f:
    f.write(matpower_str)
print(f"Saved {output_path} successfully!")
