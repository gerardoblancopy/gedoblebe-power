import tabula
import pandas as pd
import re

t = tabula.read_pdf('1740419496_2_1_REDECA_merged.pdf', pages='all', multiple_tables=True, guess=False, pandas_options={'header': None, 'dtype': str})

df_all = pd.concat(t[1:], ignore_index=True)
buses = []
for _, row in df_all.iterrows():
    vals = [str(x).strip() for x in row.values if pd.notna(x) and str(x).strip() != '']
    if not vals: continue
    
    match = re.match(r'^(\d+)', vals[0])
    if match:
        buses.append(vals)

print("Found valid buses:", len(buses))
print("Bus 0:", buses[0])
print("Bus 1:", buses[1])
for i in range(5):
    print(f"Bus {i} len:", len(buses[i]))
