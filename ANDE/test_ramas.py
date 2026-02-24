import pdfplumber

with pdfplumber.open('1740419496_2_1_REDECA_merged-3.pdf') as pdf:
    for page in pdf.pages[:2]:
        text = page.extract_text(layout=True)
        for line in text.split('\n'):
            if line.strip() and line.strip().split()[0].isdigit() and len(line) > 50:
                print(repr(line))
