import pdfplumber

def search_circuits(pdf_path):
    print("Searching in", pdf_path)
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if 'Circuito' in text and 'Tap' in text and 'De' in text:
                print(f"Found on {pdf_path}")
                print("\n".join(text.split("\n")[:30]))
                return
search_circuits('1740419496_3_1_REDECA_merged-2.pdf')
search_circuits('1740419496_3_1_REDECA_merged.pdf')
