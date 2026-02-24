import pdfplumber
import re

hvdc_list = []
with pdfplumber.open('1740419496_5_1_REDECC_merged.pdf') as pdf:
    for page in pdf.pages:
        text = page.extract_text(layout=True)
        for line in text.split('\n'):
            # Look for conversores (G, P) or FOZ / IBT entries that have numbers
            if "RET+ELO" in line or "INV+ELO" in line:
                # Based on earlier script:
                # 1   803 FOZ B1 500 10 RET+ELO01 30 NEU0ELO01R G   P     N        717     0   0,0001  12,5    5  84,99 0,9375 1,238 1,238   1
                match = re.search(r'^\s*\d+\s+(\d+)\s+([A-Z0-9 ]+)\s+(\d+)\s+(RET\+ELO\d+|INV\+ELO\d+)', line)
                if match:
                    barra_ca = match.group(1)
                    mode = "RET" if "RET" in match.group(4) else "INV"
                    
                    # Need P_iny and Q_iny which actually come from the flow. 
                    # Actually, the user's hardcoded hvdc was:
                    # 'Barra': [803, 86], 'P_iny': [-1575, 1575], 'Q_iny': [-300, -350]
                    # This means 1575 MW flow. The python dataframe has 8 conversores 
                    # (4 for 803 and 4 for 86). 
            pass

print("Hardcoding HVDC is safer since ANAREDE LCC model is complex to parse.")
