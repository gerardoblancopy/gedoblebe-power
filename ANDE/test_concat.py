import tabula
import pandas as pd
t = tabula.read_pdf('1740419496_2_1_REDECA_merged.pdf', pages='all', multiple_tables=True, guess=False, pandas_options={'header': None, 'dtype': str})

print("Pages detected:", len(t))
df_all = pd.concat(t[1:], ignore_index=True)
print("DF_ALL shape:", df_all.shape)

# Count how many rows start with numbers
nums = pd.to_numeric(df_all[0], errors='coerce')
valid_buses = df_all[nums.notna()]
print("Found valid buses:", len(valid_buses))

