import pdfplumber

with pdfplumber.open('1740419496_3_1_REDECA_merged-2.pdf') as pdf:
    for page in pdf.pages[:2]:
        text = page.extract_text(layout=True)
        print("Page start:")
        print('\n'.join(text.split('\n')[:20]))
