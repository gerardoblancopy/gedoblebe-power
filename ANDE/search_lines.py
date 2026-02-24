import pdfplumber

with pdfplumber.open('1740419496_3_1_REDECA_merged-2.pdf') as pdf:
    for page in pdf.pages[20:25]:
        text = page.extract_text(layout=True)
        lines = text.split('\n')
        # Print lines that look like a table row: numbers and names
        for line in lines[20:30]:
            print(repr(line))

