"""
DC OPF Simulator - Backend API
FastAPI application for DC Optimal Power Flow calculations
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import io
import os
import csv
import json
from typing import Optional
import logging

from app.models.schemas import (
    PowerSystem,
    OPFRequest,
    OPFResult,
    Bus,
    Generator,
    Line,
    Load,
    CaseData,
    ExportFormat
)
from app.parser.matpower import MatpowerParser
from app.solver.opf_solver import DCOPSolver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory for storing cases
CASES_DIR = os.path.join(os.path.dirname(__file__), "cases")

app = FastAPI(
    title="DC OPF Simulator API",
    description="Backend API for DC Optimal Power Flow calculations",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for current case
current_case: Optional[CaseData] = None
opf_result: Optional[OPFResult] = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "DC OPF Simulator API is running"}


@app.post("/case", response_model=CaseData)
async def parse_case(case: PowerSystem):
    """
    Parse a power system from JSON input
    """
    global current_case

    try:
        current_case = CaseData(
            buses=case.buses,
            generators=case.generators,
            lines=case.lines,
            loads=case.loads
        )
        logger.info(f"Parsed case with {len(current_case.buses)} buses, "
                   f"{len(current_case.generators)} generators, "
                   f"{len(current_case.lines)} lines")
        return current_case
    except Exception as e:
        logger.error(f"Error parsing case: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/case/text")
async def parse_text_case(matpower_text: str):
    """
    Parse a MATPOWER format case file from text input
    """
    global current_case

    try:
        parser = MatpowerParser()
        current_case = parser.parse_text(matpower_text)
        logger.info(f"Parsed MATPOWER case with {len(current_case.buses)} buses")
        return current_case
    except Exception as e:
        logger.error(f"Error parsing MATPOWER case: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/case", response_model=CaseData)
async def get_case():
    """
    Get the current case data
    """
    if current_case is None:
        raise HTTPException(status_code=404, detail="No case loaded")
    return current_case


@app.post("/opf", response_model=OPFResult)
async def run_opf(request: OPFRequest):
    """
    Run DC OPF optimization
    """
    global current_case, opf_result

    try:
        # Use provided case or current case
        if request.case_data:
            current_case = CaseData(
                buses=request.case_data.buses,
                generators=request.case_data.generators,
                lines=request.case_data.lines,
                loads=request.case_data.loads
            )

        if current_case is None:
            raise HTTPException(status_code=400, detail="No case data provided")

        # Run DC OPF solver
        solver = DCOPSolver()
        opf_result = solver.solve(
            current_case,
            voll=request.voll,
            enforce_line_limits=request.enforce_line_limits
        )

        logger.info(f"OPF solved successfully. Total cost: {opf_result.total_cost}")
        return opf_result

    except Exception as e:
        logger.error(f"Error running OPF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/results", response_model=OPFResult)
async def get_results():
    """
    Get the current OPF results
    """
    if opf_result is None:
        raise HTTPException(status_code=404, detail="No OPF results available")
    return opf_result


@app.get("/export/csv")
async def export_csv():
    """
    Export OPF results as CSV
    """
    if opf_result is None:
        raise HTTPException(status_code=404, detail="No OPF results to export")

    try:
        output = io.StringIO()

        # Export generator results
        writer = csv.writer(output)
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

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=opf_results.csv"}
        )

    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/export/json")
async def export_json():
    """
    Export OPF results as JSON
    """
    if opf_result is None:
        raise HTTPException(status_code=404, detail="No OPF results to export")

    try:
        result_dict = opf_result.model_dump()
        return JSONResponse(
            content=result_dict,
            headers={"Content-Disposition": "attachment; filename=opf_results.json"}
        )
    except Exception as e:
        logger.error(f"Error exporting JSON: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/example/case9")
async def get_example_case9():
    """
    Return the standard IEEE 9-bus test case
    """
    case = PowerSystem(
        buses=[
            Bus(id=1, type=3, v_mag=1.0, v_ang=0.0, base_kv=345.0, zone=1),
            Bus(id=2, type=1, v_mag=1.0, v_ang=0.0, base_kv=345.0, zone=1),
            Bus(id=3, type=1, v_mag=1.0, v_ang=0.0, base_kv=345.0, zone=1),
            Bus(id=4, type=1, v_mag=1.0, v_ang=0.0, base_kv=345.0, zone=1),
            Bus(id=5, type=1, v_mag=1.0, v_ang=0.0, base_kv=345.0, zone=1),
            Bus(id=6, type=1, v_mag=1.0, v_ang=0.0, base_kv=345.0, zone=1),
            Bus(id=7, type=1, v_mag=1.0, v_ang=0.0, base_kv=345.0, zone=1),
            Bus(id=8, type=1, v_mag=1.0, v_ang=0.0, base_kv=345.0, zone=1),
            Bus(id=9, type=1, v_mag=1.0, v_ang=0.0, base_kv=345.0, zone=1),
        ],
        generators=[
            Generator(bus=1, pg=0, qg=0, vg=1.0, mbase=100, cost=[0, 25, 0]),
            Generator(bus=2, pg=0, qg=0, vg=1.0, mbase=100, cost=[0, 30, 0]),
            Generator(bus=3, pg=0, qg=0, vg=1.0, mbase=100, cost=[0, 35, 0]),
        ],
        lines=[
            Line(from_bus=1, to_bus=4, r=0.0, x=0.0576, b=0.0, rate_a=250.0),
            Line(from_bus=4, to_bus=5, r=0.017, x=0.092, b=0.158, rate_a=250.0),
            Line(from_bus=5, to_bus=6, r=0.039, x=0.17, b=0.183, rate_a=250.0),
            Line(from_bus=3, to_bus=6, r=0.0, x=0.0586, b=0.0, rate_a=250.0),
            Line(from_bus=6, to_bus=7, r=0.0119, x=0.1008, b=0.1045, rate_a=250.0),
            Line(from_bus=7, to_bus=8, r=0.0085, x=0.072, b=0.0745, rate_a=250.0),
            Line(from_bus=8, to_bus=2, r=0.0, x=0.0625, b=0.0, rate_a=250.0),
            Line(from_bus=8, to_bus=9, r=0.032, x=0.161, b=0.153, rate_a=250.0),
            Line(from_bus=4, to_bus=9, r=0.01, x=0.085, b=0.088, rate_a=250.0),
        ],
        loads=[
            Load(bus=5, pd=125.0, qd=50.0),
            Load(bus=6, pd=90.0, qd=30.0),
            Load(bus=8, pd=100.0, qd=35.0),
        ]
    )
    return case


@app.get("/example/matpower")
async def get_matpower_example():
    """
    Return an example MATPOWER format case file
    """
    return """
function mpc = case9
%CASE9    Power flow data for 9 bus, 3 generator case
%   Based on Wood & Wollenberg, Example 6.3

mpc.version = '2';
mpc.baseMVA = 100;

% bus data
%    bus_i    type    Pd    Qd    Gs    Bs    area    Vm    Va    baseKV    zone    Vmax    Vmin
mpc.bus = [
    1    3    0    0    0    0    1    1    0    345    1    1.1    0.9;
    2    1    0    0    0    0    1    1    0    345    1    1.1    0.9;
    3    1    0    0    0    0    1    1    0    345    1    1.1    0.9;
    4    1    0    0    0    0    1    1    0    345    1    1.1    0.9;
    5    1    125    50    0    0    1    1    0    345    1    1.1    0.9;
    6    1    90    30    0    0    1    1    0    345    1    1.1    0.9;
    7    1    0    0    0    0    1    1    0    345    1    1.1    0.9;
    8    1    0    0    0    0    1    1    0    345    1    1.1    0.9;
    9    1    100    35    0    0    1    1    0    345    1    1.1    0.9;
];

% generator data
%    bus    Pg    Qg    Qmax    Qmin    Vg    mBase    status    Pmax    Pmin    Pc1    Pc2    Qc1min    Qc1max    Qc2min    Qc2max    ramp_agc    ramp_10    ramp_30    ramp_q    apf
mpc.gen = [
    1    0    0    300    -300    1    100    1    250    10    0    0    0    0    0    0    0    0    0    0    0;
    2    0    0    300    -300    1    100    1    300    10    0    0    0    0    0    0    0    0    0    0    0;
    3    0    0    300    -300    1    100    1    270    10    0    0    0    0    0    0    0    0    0    0    0;
];

% branch data
%    fbus    tbus    r    x    b    rateA    rateB    rateC    ratio    angle    status    angmin    angmax    P    Q
mpc.branch = [
    1    4    0    0.0576    0    250    250    250    0    0    1    -360    360    0    0;
    4    5    0.017    0.092    0.158    250    250    250    0    0    1    -360    360    0    0;
    5    6    0.039    0.17    0.183    250    250    250    0    0    1    -360    360    0    0;
    3    6    0    0.0586    0    250    250    250    0    0    1    -360    360    0    0;
    6    7    0.0119    0.1008    0.1045    250    250    250    0    0    1    -360    360    0    0;
    7    8    0.0085    0.072    0.0745    250    250    250    0    0    1    -360    360    0    0;
    8    2    0    0.0625    0    250    250    250    0    0    1    -360    360    0    0;
    8    9    0.032    0.161    0.153    250    250    250    0    0    1    -360    360    0    0;
    4    9    0.01    0.085    0.088    250    250    250    0    0    1    -360    360    0    0;
];

% generator cost data
%    2    startup    shutdown    n    c(n-1)    ...    c0
mpc.gencost = [
    2    0    0    3    0    25    0;
    2    0    0    3    0    30    0;
    2    0    0    3    0    35    0;
];
"""


@app.get("/cases")
async def list_cases():
    """List available cases in the cases directory"""
    if not os.path.exists(CASES_DIR):
        return []
    
    files = [f for f in os.listdir(CASES_DIR) if f.endswith('.m') or f.endswith('.json')]
    return sorted(files)


@app.post("/cases/{filename}/load", response_model=CaseData)
async def load_server_case(filename: str):
    """
    Load a specific case file from the server
    """
    global current_case
    
    # Secure filename to prevent directory traversal
    filename = os.path.basename(filename)
    file_path = os.path.join(CASES_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Case file not found")
        
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        if filename.endswith('.m'):
            parser = MatpowerParser()
            current_case = parser.parse_text(content)
        elif filename.endswith('.json'):
            # Parse JSON to dict then to CaseData
            data = json.loads(content)
            current_case = CaseData(**data)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
            
        logger.info(f"Loaded server case {filename}")
        return current_case
    except Exception as e:
        logger.error(f"Error loading case {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

