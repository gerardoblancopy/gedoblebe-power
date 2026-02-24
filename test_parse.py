import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
from app.parser.matpower import MatpowerParser

try:
    with open('backend/app/cases/sistema_paraguay_brasil.m', 'r') as f:
        content = f.read()
    parser = MatpowerParser()
    case = parser.parse_text(content)
    print("SUCCESS: Loaded case with", len(case.buses), "buses")
except Exception as e:
    print("ERROR parsing:", e)
