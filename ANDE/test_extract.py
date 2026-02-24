import fitz
import re

doc = fitz.open('1740419496_2_1_REDECA_merged.pdf')
barras = []
# The format looks like:
# 48 1- PV
# F
# 13,8 CSI B1  13.8
# F
# 0,900-1,100
# Ligado
# 0 - Normal
# 1,025
# 14,1
# 4,12
# 0
# -545
# -9900
# 9900
# 15
# 1,03
# Note: sometimes they might be on the same line if read differently, let's see.

lines = []
for page in doc:
    lines.extend(page.get_text().splitlines())

# Count how many lines start with an integer
count = 0
for line in lines:
    if re.match(r'^\s*\d+\s', line) or line.strip().isdigit():
        pass
        
print("Lines that look like starts of buses:", len([l for l in lines if re.match(r'^\d+\s+\d', l)]))
