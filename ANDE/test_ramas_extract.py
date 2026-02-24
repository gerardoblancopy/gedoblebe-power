import pdfplumber

with pdfplumber.open('1740419496_2_1_REDECA_merged-3.pdf') as pdf:
    # Let's check headers
    for page in pdf.pages[:3]:
        text = page.extract_text(layout=True)
        print("Page start:")
        print('\n'.join(text.split('\n')[20:30]))
        
# Actually 1740419496_2_1_REDECA_merged.pdf is BARRAS
# 1740419496_2_1_REDECA_merged-2.pdf is ???
# 1740419496_2_1_REDECA_merged-3.pdf is ???
# Let's inspect 1740419496_2_1_REDECA_merged-2.pdf
with pdfplumber.open('1740419496_2_1_REDECA_merged-2.pdf') as pdf:
    for page in pdf.pages[:1]:
        text = page.extract_text(layout=True)
        print("MERGED-2 Page start:")
        print('\n'.join(text.split('\n')[:40]))
