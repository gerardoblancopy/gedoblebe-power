import pdfplumber
import pandas as pd
import sys
import glob
import os

def pdf_to_csv(pdf_path, output_csv):
    print(f"Procesando: {pdf_path}")
    all_data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            # Extraer texto preservando el layout (espacios visuales = espacios de texto)
            text = page.extract_text(layout=True)
            if not text:
                continue
                
            for line in text.split('\n'):
                # Ignorar líneas muy cortas o vacías
                if len(line.strip()) < 5:
                    continue
                
                # Para ANAREDE, muchas filas de datos comienzan con números.
                # También queremos las cabeceras.
                # Como las columnas no tienen bordes, dividimos por 2 o más espacios.
                import re
                row = re.split(r'\s{2,}', line.strip())
                all_data.append(row)
                
    if all_data:
        # Encontrar la longitud máxima de fila para cuadrar el DataFrame
        max_cols = max(len(row) for row in all_data)
        
        # Rellenar filas más cortas para que todas tengan la misma longitud
        padded_data = [row + [''] * (max_cols - len(row)) for row in all_data]
        
        df = pd.DataFrame(padded_data)
        df.to_csv(output_csv, index=False, header=False, sep=';', encoding='utf-8-sig')
        print(f"Guardado exitosamente: {output_csv}")
    else:
        print(f"No se encontró texto extraíble en {pdf_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Convierte PDFs de ANAREDE a CSV')
    parser.add_argument('--input', type=str, help='Ruta a un PDF específico (opcional)')
    parser.add_argument('--dir', type=str, default='ANDE', help='Directorio con PDFs (default: ANDE)')
    
    args = parser.parse_args()
    
    if args.input:
        if os.path.exists(args.input):
            base_name = os.path.splitext(os.path.basename(args.input))[0]
            output_csv = f"{base_name}.csv"
            pdf_to_csv(args.input, output_csv)
        else:
            print(f"Error: No se encontró el archivo {args.input}")
    else:
        # Buscar todos los PDFs en el directorio
        pdfs = glob.glob(os.path.join(args.dir, "*.pdf"))
        print(f"Encontrados {len(pdfs)} archivos PDF en el directorio '{args.dir}'")
        
        for pdf in pdfs:
            base_name = os.path.splitext(os.path.basename(pdf))[0]
            output_csv = os.path.join(args.dir, f"{base_name}.csv")
            pdf_to_csv(pdf, output_csv)

if __name__ == "__main__":
    main()
