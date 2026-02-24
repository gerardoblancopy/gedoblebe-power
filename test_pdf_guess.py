import pdfplumber
import glob

pdfs = glob.glob("ANDE/*.pdf")
for pdf_file in pdfs:
    print(f"\n--- Checking {pdf_file} ---")
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = pdf.pages[0].extract_text()
            lines = text.split('\n')
            for i in range(min(15, len(lines))):
                print(lines[i])
    except Exception as e:
        print(f"Error: {e}")
