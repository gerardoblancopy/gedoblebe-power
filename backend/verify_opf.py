import os
import sys
import numpy as np

# Ensure app modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.schemas import Bus, Generator, Line, Load, CaseData
from app.solver.opf_solver import DCOPSolver


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def check_slack_noncontig_ids() -> None:
    """Validate slack angle with non-contiguous bus IDs."""
    buses = [
        Bus(id=101, type=1),
        Bus(id=205, type=3),  # slack
        Bus(id=330, type=1),
    ]
    generators = [
        Generator(bus=101, pmin=0.0, pmax=120.0, cost=[0.01, 10.0, 0.0]),
        Generator(bus=330, pmin=0.0, pmax=80.0, cost=[0.02, 8.0, 0.0]),
    ]
    lines = [
        Line(from_bus=101, to_bus=205, x=0.1, rate_a=100.0),
        Line(from_bus=205, to_bus=330, x=0.1, rate_a=100.0),
    ]
    loads = [
        Load(bus=205, pd=50.0),
        Load(bus=330, pd=30.0),
    ]

    case = CaseData(
        buses=buses,
        generators=generators,
        lines=lines,
        loads=loads,
        base_mva=100.0,
    )

    solver = DCOPSolver()
    result = solver.solve(case)

    slack_bus_id = 205
    slack_res = next((b for b in result.bus_results if b.bus == slack_bus_id), None)
    if slack_res is None:
        fail("Slack bus result not found.")

    if abs(slack_res.va) > 1e-4:
        fail(f"Slack bus angle not ~0 deg: {slack_res.va}")

    print("OK: slack angle with non-contiguous IDs")


def check_ed_qp_lmp_bounds() -> None:
    """Validate LMP fallback when all generators are at bounds."""
    buses = [
        Bus(id=1, type=3),
        Bus(id=2, type=1),
    ]
    generators = [
        Generator(bus=1, pmin=60.0, pmax=60.0, cost=[0.01, 5.0, 0.0]),
        Generator(bus=2, pmin=40.0, pmax=40.0, cost=[0.02, 4.0, 0.0]),
    ]
    lines = [
        Line(from_bus=1, to_bus=2, x=0.1, rate_a=999.0),
    ]
    loads = [
        Load(bus=2, pd=100.0),
    ]

    case = CaseData(
        buses=buses,
        generators=generators,
        lines=lines,
        loads=loads,
        base_mva=100.0,
    )

    solver = DCOPSolver()
    result = solver.solve(case, enforce_line_limits=False)

    if not result.bus_results:
        fail("No bus results returned.")
    lmp = result.bus_results[0].marginal_cost

    # KKT bounds for lambda when all gens are at bounds
    tol = 1e-4
    active_lower = []
    active_upper = []
    for gen in generators:
        pg_mw = gen.pmax
        mc = 2 * gen.cost[0] * pg_mw + gen.cost[1]
        # pmin == pmax, so both bounds are active
        active_lower.append(mc)
        active_upper.append(mc)

    lambda_lower = max(active_upper) if active_upper else None
    lambda_upper = min(active_lower) if active_lower else None

    if lambda_lower is not None and lambda_upper is not None and lambda_lower > lambda_upper:
        expected = 0.5 * (lambda_lower + lambda_upper)
        if abs(lmp - expected) > tol:
            fail(f"LMP not matching fallback average: {lmp} != {expected}")
    else:
        if lambda_lower is not None and lmp < lambda_lower - tol:
            fail(f"LMP below KKT lower bound: {lmp} < {lambda_lower}")
        if lambda_upper is not None and lmp > lambda_upper + tol:
            fail(f"LMP above KKT upper bound: {lmp} > {lambda_upper}")

    print("OK: LMP bounds in ED QP degeneracy")


if __name__ == "__main__":
    check_slack_noncontig_ids()
    check_ed_qp_lmp_bounds()
    print("All checks passed.")
