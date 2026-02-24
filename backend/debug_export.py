import sys
import os
import logging
import io
import csv
import json

# Ensure app modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.parser.matpower import MatpowerParser
from app.solver.opf_solver import DCOPSolver
from app.models.schemas import OPFResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_export():
    try:
        # 1. Run OPF to get results
        case_path = os.path.join(os.path.dirname(__file__), "app", "cases", "case118.m")
        with open(case_path, 'r') as f:
            content = f.read()

        parser = MatpowerParser()
        case_data = parser.parse_text(content)
        
        logger.info("Running OPF...")
        solver = DCOPSolver()
        opf_result = solver.solve(case_data)
        
        logger.info("OPF finished. Testing CSV export...")
        
        # 2. Simulate export_csv logic from main.py
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Generator Results
        writer.writerow(["Generator Results"])
        writer.writerow(["Bus", "Pg (MW)", "Qg (MVAR)", "Cost ($/h)"])
        for gen in opf_result.generator_results:
            writer.writerow([gen.bus, gen.pg, gen.qg, gen.cost])

        writer.writerow([])
        writer.writerow(["Bus Results"])
        writer.writerow(["Bus", "Va (degrees)", "Pl (MW)", "Ql (MVAR)", "LMP ($/MWh)", "Curtailment (MW)"])
        for bus in opf_result.bus_results:
            writer.writerow([bus.bus, bus.va, bus.pl, bus.ql, bus.marginal_cost, bus.curtailment])

        writer.writerow([])
        writer.writerow(["Line Results"])
        writer.writerow(["From", "To", "Flow (MW)", "Loading (%)", "Congestion Rent ($/h)"])
        for line in opf_result.line_results:
            writer.writerow([line.from_bus, line.to_bus, line.flow_mw,
                           line.loading_percent, line.congestion_rent])

        writer.writerow([])
        writer.writerow(["Total Cost", f"{opf_result.total_cost} $/h"])
        writer.writerow(["Total Curtailment", f"{opf_result.total_curtailment} MW"])
        
        csv_content = output.getvalue()
        logger.info(f"CSV Export successful! Length: {len(csv_content)}")
        
        # 3. Simulate export_json logic
        logger.info("Testing JSON export...")
        json_dict = opf_result.model_dump()
        json_content = json.dumps(json_dict)
        logger.info(f"JSON Export successful! Length: {len(json_content)}")

    except Exception as e:
        logger.error("Export Failed")
        logger.exception(e)

if __name__ == "__main__":
    test_export()
