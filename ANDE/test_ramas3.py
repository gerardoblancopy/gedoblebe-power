import pdfplumber

with pdfplumber.open('1740419496_2_1_REDECA_merged-3.pdf') as pdf:
    for page in pdf.pages[:3]:
        text = page.extract_text(layout=True)
        print("Page start:")
        print('\n'.join(text.split('\n')[20:40]))
