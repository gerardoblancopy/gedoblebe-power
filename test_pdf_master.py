import pdfplumber
archivo = "ANDE/1740419496_1_RespuestaSolicitudN89549.pdf"

print("Checking master PDF pages...")
try:
    with pdfplumber.open(archivo) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and ("CIRCUITOS" in text or "RAMAS" in text or "LINHAS" in text or "Equipamento" in text):
                print(f"Found keyword on page {i+1}")
                print(text[:200])
except Exception as e:
    print(f"Error: {e}")
