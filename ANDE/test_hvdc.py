import pdfplumber

hvdc_data = []

with pdfplumber.open('1740419496_5_1_REDECC_merged.pdf') as pdf:
    for page in pdf.pages:
        text = page.extract_text(layout=True)
        # the table "Dados de Conversores" has columns:
        # Número Barra CA / Nome / Barra CC / Nome / Modo / Número Pontes / Corrente Nominal / Reatância / Tensão / Potência
        # example line:
        # 1      803 FOZ B1 500    10 RET+ELO01     30 NEU0ELO01R R            4      2625     17,8    127,3    470,2
        for line in text.split('\n'):
            if "FOZ" in line or "IBT" in line:
                print(repr(line))
