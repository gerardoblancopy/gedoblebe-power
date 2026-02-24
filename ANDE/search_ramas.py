import pdfplumber
import glob

pdfs = glob.glob('*REDECA*.pdf')

for f in pdfs:
    try:
        with pdfplumber.open(f) as pdf:
            # check first 5 pages, see if it has columns for De / Para / Circuito, etc.
            found = False
            for page in pdf.pages[:5]:
                text = page.extract_text(layout=True)
                if 'De' in text and 'Para' in text and 'Circuito' in text:
                    for line in text.split('\n'):
                        if 'De' in line and 'Para' in line and 'Circuito' in line:
                            print(f"File {f} contains Ramas headers:")
                            print(repr(line))
                            found = True
                            break
                if found: break
                
    except Exception as e:
        print(f"Error on {f}: {e}")

