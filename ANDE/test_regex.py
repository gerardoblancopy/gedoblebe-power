import tabula
import pandas as pd
import re

t = tabula.read_pdf('1740419496_2_1_REDECA_merged.pdf', pages='all', multiple_tables=True, guess=False, pandas_options={'header': None, 'dtype': str})
df_all = pd.concat(t[1:], ignore_index=True)

buses_dict = []
for _, row in df_all.iterrows():
    vals = [str(x).strip() for x in row.values if pd.notna(x) and str(x).strip() != '']
    if not vals: continue
    full_str = " ".join(vals)
    
    match = re.match(r'^(\d+)\s+(.+?)\s+(Ligado|Desligado)\s+(.+?)\s+([\d.,\- ]+)$', full_str)
    if match:
        num = match.group(1)
        tipo_str = match.group(2)
        estado = match.group(3)
        estado_op = match.group(4)
        numbers = match.group(5)
        
        # 'numbers' string contains all the numeric values at the end, e.g. "1,09 376,1 4,12 66 2774 15 1,05"
        nums_list = [float(x.replace(',','.')) for x in numbers.split()]
        buses_dict.append({"num": num, "nums_list": nums_list})

print("Found valid buses:", len(buses_dict))
print("Bus 0:", buses_dict[0])
print("Bus 1:", buses_dict[1])
