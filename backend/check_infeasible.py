import sys
import os
import json
import numpy as np

# Adjust path to import from backend
sys.path.insert(0, os.path.abspath('.'))
from app.parser.matpower import MatpowerParser
from app.solver.opf_solver import DCOPSolver
from scipy.sparse.csgraph import connected_components

try:
    import os
    case_path = os.path.join(os.path.dirname(__file__), 'app/cases/sistema_paraguay_brasil.m')
    with open(case_path, 'r') as f:
        content = f.read()

    parser = MatpowerParser()
    case = parser.parse_text(content)

    print("=== Basic Check ===")
    total_pmax = sum([g.pmax for g in case.generators])
    total_pmin = sum([g.pmin for g in case.generators])
    total_load = sum([load.pd for load in case.loads])
    
    print(f"Total Gen Pmax: {total_pmax} MW")
    print(f"Total Gen Pmin: {total_pmin} MW")
    print(f"Total Demand: {total_load} MW")
    
    print("\nGenerators with Pmin > 0:")
    for g in case.generators:
        if g.pmin > 0:
            print(f" - Bus {g.bus} (Pmin: {g.pmin}, Pmax: {g.pmax})")

    solver = DCOPSolver()
    solver.base_mva = case.base_mva
    B_sparse = solver._build_sparse_susceptance_matrix(case.buses, case.lines)
    
    print("\n=== Connectivity Check ===")
    n_components, labels = connected_components(csgraph=B_sparse, directed=False, return_labels=True)
    print(f"Number of connected components: {n_components}")
    
    if n_components > 1:
        # Check if components have generation/load balance issues
        bus_ids = {bus.id: i for i, bus in enumerate(case.buses)}
        comp_counts = np.bincount(labels)
        print("Components sizes:", comp_counts)
        
        slacks = [b.id for b in case.buses if b.type == 3]
        print(f"\nSlack buses found: {slacks}")
        for s_id in slacks:
            s_idx = bus_ids.get(s_id)
            if s_idx is not None:
                print(f" - Bus {s_id} is in Component {labels[s_idx]}")
        
        for c in range(n_components):
            comp_buses = np.where(labels == c)[0]
            comp_bus_names = [list(bus_ids.keys())[i] for i in comp_buses]
            
            comp_pd = sum([load.pd for load in case.loads if load.bus in comp_bus_names])
            comp_pmax = sum([g.pmax for g in case.generators if g.bus in comp_bus_names])
            comp_pmin = sum([g.pmin for g in case.generators if g.bus in comp_bus_names])
            
            print(f"Component {c} (size {len(comp_buses)}): Load={comp_pd}, Pmin={comp_pmin}, Pmax={comp_pmax}")
        
        largest_comp_idx = np.argmax(comp_counts)
        largest_comp_buses = np.where(labels == largest_comp_idx)[0]
        largest_comp_bus_ids = [list(bus_ids.keys())[i] for i in largest_comp_buses]
        print(f"\nLargest Component ({largest_comp_idx}): Size {len(largest_comp_buses)}")
        print(f"Buses: {largest_comp_bus_ids}")

except Exception as e:
    import traceback
    traceback.print_exc()
