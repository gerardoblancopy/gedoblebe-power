import urllib.request
import json

def test_multi_gen():
    url = "http://localhost:8000/opf"
    
    # 2-bus system, 2 generators at Bus 1
    case_data = {
        "buses": [
            {"id": 1, "type": 3, "base_kv": 345, "v_mag": 1.0, "v_ang": 0.0},
            {"id": 2, "type": 1, "base_kv": 345, "v_mag": 1.0, "v_ang": 0.0}
        ],
        "generators": [
            {
                "id": "G-1-1",
                "bus": 1,
                "pmax": 100,
                "pmin": 0,
                "cost": [0, 20, 0], # Cheaper
                "status": 1
            },
            {
                "id": "G-1-2",
                "bus": 1,
                "pmax": 100,
                "pmin": 0,
                "cost": [0, 50, 0], # More expensive
                "status": 1
            }
        ],
        "lines": [
            {"from_bus": 1, "to_bus": 2, "x": 0.1, "rate_a": 250, "status": 1}
        ],
        "loads": [
            {"bus": 2, "pd": 150, "qd": 0}
        ],
        "base_mva": 100.0
    }
    
    data = json.dumps({"case_data": case_data}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"Status: {result['status']}")
            print(f"Total Cost: {result['total_cost']}")
            for gen in result['generator_results']:
                # The backend should now return the 'id'
                print(f"Gen {gen.get('id', 'N/A')} at Bus {gen['bus']}: {gen['pg']} MW, Cost: {gen['cost']}")
            
            # Expectation: Gen G-1-1 should provide 100 MW (maxed), Gen G-1-2 should provide 50 MW
            pg1 = next(g['pg'] for g in result['generator_results'] if g.get('id') == 'G-1-1')
            pg2 = next(g['pg'] for g in result['generator_results'] if g.get('id') == 'G-1-2')
            
            if abs(pg1 - 100) < 0.1 and abs(pg2 - 50) < 0.1:
                print("\nSUCCESS: Multiple generators handled correctly and dispatched by cost!")
            else:
                print("\nFAILURE: Dispatch doesn't match expected cost optimization.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_multi_gen()
