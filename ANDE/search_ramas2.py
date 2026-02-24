import pdfplumber
import glob

pdfs = glob.glob('*.pdf')

for f in pdfs:
    try:
        with pdfplumber.open(f) as pdf:
            found = False
            for page in pdf.pages[:5]:
                text = page.extract_text()
                if text and 'Circuito' in text:
                    for line in text.split('\n'):
                        if 'De' in line and 'Circuito' in line:
                            print(f"File {f} contains Ramas:")
                            print(repr(line))
                            found = True
                            break
                if found: break
                
    except Exception as e:
        print(f"Error on {f}: {e}")

