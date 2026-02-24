import os
import sys
import json
import urllib.request

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.parser.matpower import MatpowerParser

def test_api_case14():
    print("Testing case14.m via API...")
    case_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "cases", "case14.m")
    
    with open(case_path, 'r') as f:
        content = f.read()
        
    parser = MatpowerParser()
    case_data = parser.parse_text(content)
    
    # Serialize to JSON payload
    payload = {
        "case_data": case_data.dict(),
        "enforce_line_limits": True,
        "voll": 10000.0,
        "remove_isolated": True
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8000/opf", data=data, headers={'Content-Type': 'application/json'}, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            print("Status code:", response.status)
            print("API Success!")
    except urllib.error.HTTPError as e:
        print("HTTP Error:", e.code)
        print("Response:", e.read().decode('utf-8'))
    except Exception as e:
        print("Error during API request:", str(e))

if __name__ == "__main__":
    test_api_case14()
