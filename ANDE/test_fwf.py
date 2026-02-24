import pdfplumber
import io

# We capture the layout text from all pages
text_all = ""
with pdfplumber.open('1740419496_2_1_REDECA_merged.pdf') as pdf:
    for page in pdf.pages:
        text_all += page.extract_text(layout=True) + "\n"

# The header line is:
# "  Número Tipo     Base (kV) Nome Barra Limite Tensão (p.u.) Operativo Visualização (p.u.) (kV) (graus) (MW) (Mvar) (Mvar) (Mvar) (MW) (Mvar) (Mvar) Área (p.u.)"
# Let's just find lines that start with a number.
lines = text_all.split('\n')
valid_lines = [line for line in lines if line.strip() and line.strip().split()[0].isdigit()]

print("Valid lines:", len(valid_lines))
print(valid_lines[0])
print(valid_lines[1])
# Print the characters with an index ruler below it to see exact column numbers
ruler1 = "0" * 10 + "1" * 10 + "2" * 10 + "3" * 10 + "4" * 10 + "5" * 10 + "6" * 10 + "7" * 10 + "8" * 10 + "9" * 10 + "0" * 10 + "1" * 10 + "2" * 10 + "3" * 10 + "4"*10
ruler2 = "0123456789" * 14
print(valid_lines[0])
print(ruler1[:len(valid_lines[0])])
print(ruler2[:len(valid_lines[0])])

