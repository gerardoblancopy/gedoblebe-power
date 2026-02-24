import pdfplumber
import glob

pdfs = glob.glob('*REDECA*.pdf')

for f in pdfs:
    print(f"Searching in {f}")
    try:
        with pdfplumber.open(f) as pdf:
            for page in pdf.pages:
                text = page.extract_text(layout=True)
                if 'De' in text and 'Para' in text:
                    for line in text.split('\n'):
                        if 'De' in line and 'Para' in line and len(line.split()) > 5:
                            print(f"Found on {f}")
                            print(repr(line))
                            break
    except Exception as e:
        print("Error", e)
