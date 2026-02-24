import sys
import os
import logging
import numpy as np

# Ensure app modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.parser.matpower import MatpowerParser
from app.solver.opf_solver import DCOPSolver

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    try:
        case_path = os.path.join(os.path.dirname(__file__), "app", "cases", "case118.m")
        if not os.path.exists(case_path):
            logger.error(f"File not found: {case_path}")
            return

        with open(case_path, 'r') as f:
            content = f.read()

        logger.info(f"Parsing {case_path}...")
        parser = MatpowerParser()
        case_data = parser.parse_text(content)
        
        logger.info(f"Running OPF on {len(case_data.buses)} buses...")
        solver = DCOPSolver()
        # Force nodal formulation by ensuring > 50 buses (which case118 has)
        result = solver.solve(case_data)
        
        logger.info("OPF Success!")
        logger.info(f"Total Cost: {result.total_cost}")
        logger.info(f"Status: {result.status}")
        
        # Basic validation
        if result.status != "optimal":
            logger.warning(f"Solver status is {result.status}")

    except Exception as e:
        logger.error("OPF Failed")
        logger.exception(e)

if __name__ == "__main__":
    main()
