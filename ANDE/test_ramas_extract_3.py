import pdfplumber

with pdfplumber.open('1740419496_2_1_REDECA_merged-3.pdf') as pdf:
   for page in pdf.pages[:2]:
       text = page.extract_text(layout=True)
       print("PAGE START:")
       print('\n'.join(text.split('\n')[20:30]))

