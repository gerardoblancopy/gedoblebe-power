import os
import sys

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.parser.matpower import MatpowerParser

def test_case4gs():
    parser = MatpowerParser()
    
    case_path = os.path.join(os.path.dirname(__file__), "app/cases/case4gs.m")
    with open(case_path, 'r') as f:
        content = f.read()
        
    try:
        case = parser.parse_text(content)
        print(f"Successfully parsed case4gs.m")
        print(f"Buses: {len(case.buses)}")
        print(f"Generators: {len(case.generators)}")
        print(f"Lines: {len(case.lines)}")
        print(f"Base MVA: {case.base_mva}")
        
        # Verify specific values from case4gs.m
        # bus 1: type 3, Pd 50, Qd 30.99
        bus1 = next(b for b in case.buses if b.id == 1)
        assert bus1.type == 3
        # In the file: 1	3	50	30.99
        # The parser logic: pd = float(row[2])
        # So bus1.pd should be close to 50 needed to check if Load was created from it
        
        # Verify line count (should be 4)
        assert len(case.lines) == 4
        
        # Verify generator count (should be 2)
        assert len(case.generators) == 2
        
        # Verify cost data exists (should be [0, 25, 0] and [0, 30, 0] based on file)
        # The parser stores cost as [a, b, c]
        # File has:
        # 2 0 0 3 0 25 0 -> linear cost 25
        # 2 0 0 3 0 30 0 -> linear cost 30
        # MatpowerParser._parse_gencost converts this to quadratic coeffs
        
        gen1 = case.generators[0] 
        # The order depends on how they are listed.
        # File gen order: bus 4 (318MW), bus 1 (0MW)
        # File cost order: row 1 matches gen 1? Usually yes.
        # Let's just check that costs are NOT the default [0, 25, 0] for ALL of them if they differ.
        # Wait, the first one IS 25. The second is 30.
        
        costs = [g.cost for g in case.generators]
        print(f"Generator costs: {costs}")
        assert any(c[1] == 30 for c in costs), "Expected a generator with linear cost 30"

        
    except Exception as e:
        print(f"Failed to parse case4gs.m: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_case4gs()
