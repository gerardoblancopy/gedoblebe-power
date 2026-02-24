import os
import sys

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.parser.matpower import MatpowerParser
from app.solver.opf_solver import DCOPSolver

def test_case14():
    print("Testing case14.m...")
    case_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "cases", "case14.m")
    
    with open(case_path, 'r') as f:
        content = f.read()
        
    parser = MatpowerParser()
    case_data = parser.parse_text(content)
    
    solver = DCOPSolver()
    
    try:
        results = solver.solve(case_data, enforce_line_limits=True, voll=10000.0, remove_isolated=True)
        print("Success! Total cost:", results.total_cost)
    except Exception as e:
        print("Error during solve:", str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_case14()
