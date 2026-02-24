import pdfplumber

with pdfplumber.open('1740419496_1_RespuestaSolicitudN89549.pdf') as pdf:
    for page in pdf.pages:
        print(page.extract_text()[:100])
