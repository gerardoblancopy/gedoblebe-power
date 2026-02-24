import fitz
import re

def extract_buses(pdf_path):
    doc = fitz.open(pdf_path)
    lines = []
    for page in doc:
        lines.extend([l.strip() for l in page.get_text().splitlines() if l.strip()])
    
    buses = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r'^(\d+)\s+(\d)\s*-?\s*(PQ|PV|Slack|Referência)?', line, re.IGNORECASE)
        if match:
            num = match.group(1)
            tipo = match.group(2)
            
            bus_data = [line]
            i += 1
            while i < len(lines):
                if re.match(r'^\d+\s+\d\s*-?\s*(PQ|PV|Slack|Referência)', lines[i], re.IGNORECASE) or lines[i].startswith('ANA') or lines[i].startswith('Sistema'):
                    break
                bus_data.append(lines[i])
                i += 1
            buses.append(bus_data)
        else:
            i += 1
            
    print(f"Extracted {len(buses)} buses")
    print(buses[0])
    
extract_buses('1740419496_2_1_REDECA_merged.pdf')
