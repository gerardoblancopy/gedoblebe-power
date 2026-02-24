import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.parser.matpower import MatpowerParser
from app.solver.opf_solver import DCOPSolver

def main():
    case_path = "../ANDE/case_ANDE.m"
    if not os.path.exists(case_path):
        print(f"File not found: {case_path}")
        return

    with open(case_path, 'r') as f:
        content = f.read()

    print(f"Parsing {case_path}...")
    parser = MatpowerParser()
    case_data = parser.parse_text(content)
    
    solver = DCOPSolver()
    
    print("Testing OPF with default parameters (remove isolated...)")
    try:
        result = solver.solve(case_data, remove_isolated=True)
        print("Success! remove_isolated=True")
        print(f"Status: {result.status}")
        print(f"Objective: {result.total_cost}")
        print(f"Buses: {len(result.bus_results)}")
        print(f"Lines: {len(result.line_results)}")
        print(f"Generators: {len(result.generator_results)}")
        
        # also test without remove_isolated
        try:
            r2 = solver.solve(case_data, remove_isolated=False)
            print(f"Without isolated removal, status: {r2.status}")
        except Exception as e:
            print(f"Without isolated removal failed: {e}")
    except Exception as e:
        print(f"OPF Failed entirely: {e}")

if __name__ == "__main__":
    main()
