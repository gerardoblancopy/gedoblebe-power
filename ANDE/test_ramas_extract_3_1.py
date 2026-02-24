import pdfplumber

with pdfplumber.open('1740419496_3_1_REDECA_merged.pdf') as pdf:
   for page in pdf.pages[:3]:
       text = page.extract_text(layout=True)
       print("PAGE START:")
       print('\n'.join(text.split('\n')[:20]))

