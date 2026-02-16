"""
DC Optimal Power Flow Solver
Pure Python implementation using scipy optimization
Supports both LP (linprog) and QP (SLSQP) formulations
"""

import numpy as np
from typing import List, Dict, Any
import logging

from app.models.schemas import CaseData, Bus, Generator, Line, OPFResult, \
    GeneratorResult, BusResult, LineResult

logger = logging.getLogger(__name__)


class DCOPSolver:
    """DC Optimal Power Flow solver using scipy"""

    def __init__(self):
        self.base_mva = 100.0

    def solve(self, case: CaseData, voll: float = 10000.0, enforce_line_limits: bool = True) -> OPFResult:
        """
        Solve DC OPF problem

        Minimizes generation cost subject to:
        - Power balance constraints
        - Generator capacity constraints
        - Line flow constraints via curtailment (VOLL method)
        """
        try:
            self.base_mva = case.base_mva if case.base_mva else 100.0

            # Extract system data
            buses = case.buses
            generators = case.generators
            lines = case.lines
            loads = case.loads if case.loads else []

            if not buses or not generators or not lines:
                raise ValueError("Invalid case: missing buses, generators, or lines")

            # Get slack bus
            slack_bus = self._find_slack_bus(buses)

            # Build admittance matrix (DC approximation) in per-unit
            B = self._build_susceptance_matrix(buses, lines)

            # Extract load demands in per-unit
            Pd_pu, Qd_pu = self._extract_loads(buses, loads)

            # Total load in per-unit
            total_load_pu = np.sum(Pd_pu)

            # Get real generator info in per-unit
            real_gen_costs = [g.cost for g in generators]
            real_gen_pmin = np.array([g.pmin / self.base_mva for g in generators])
            real_gen_pmax = np.array([g.pmax / self.base_mva for g in generators])

            # Map generator indices to bus indices
            bus_ids = {bus.id: i for i, bus in enumerate(buses)}
            real_gen_bus_indices = [bus_ids[g.bus] for g in generators]

            # Pre-compute line flow matrix (PTDF)
            PTDF = self._build_ptdf_matrix(B, lines, buses, bus_ids, slack_bus)

            # Get line ratings in per-unit
            line_rates = []
            for line in lines:
                rate = line.rate_a / self.base_mva if line.rate_a > 0 else 2.5
                line_rates.append(rate)
            line_rates = np.array(line_rates)

            n_buses = len(buses)
            n_real_gen = len(generators)

            # Detect if problem is LP (all quadratic cost coefficients are zero)
            is_linear = all(cost[0] == 0 for cost in real_gen_costs)

            if enforce_line_limits and len(PTDF) > 0:
                if is_linear:
                    Pg_opt_pu, fict_gen_pg, status, lmp = self._solve_lp(
                        n_real_gen, n_buses, real_gen_costs, real_gen_pmin,
                        real_gen_pmax, real_gen_bus_indices, Pd_pu,
                        total_load_pu, PTDF, line_rates, voll
                    )
                else:
                    Pg_opt_pu, fict_gen_pg, status, lmp = self._solve_qp(
                        n_real_gen, n_buses, real_gen_costs, real_gen_pmin,
                        real_gen_pmax, real_gen_bus_indices, Pd_pu,
                        total_load_pu, PTDF, line_rates, voll
                    )
            else:
                # No line constraints - simple economic dispatch
                if is_linear:
                    Pg_opt_pu, fict_gen_pg, status, lmp = self._solve_ed_lp(
                        n_real_gen, n_buses, real_gen_costs, real_gen_pmin,
                        real_gen_pmax, total_load_pu
                    )
                else:
                    Pg_opt_pu, fict_gen_pg, status, lmp = self._solve_ed_qp(
                        n_real_gen, n_buses, generators, real_gen_costs,
                        real_gen_pmin, real_gen_pmax, total_load_pu
                    )

            # Extract results
            real_gen_pg_mw = Pg_opt_pu[:n_real_gen] * self.base_mva

            # Build full Pg for power flow calc
            Pg_full_pu = np.zeros(n_buses)
            for idx, gen_idx in enumerate(real_gen_bus_indices):
                Pg_full_pu[gen_idx] += Pg_opt_pu[idx]

            # Effective load considering curtailment
            curtailment_pu = Pg_opt_pu[n_real_gen:] if n_real_gen < len(Pg_opt_pu) else np.zeros(n_buses)
            Pd_effective_pu = Pd_pu - curtailment_pu
            Pnet_opt_pu = Pg_full_pu - Pd_effective_pu

            # Calculate voltage angles
            theta = self._solve_theta(B, Pnet_opt_pu, slack_bus)

            # Calculate line flows (with LMPs for congestion rent)
            line_flows = self._calculate_line_flows(lines, buses, theta, lmp)

            # Curtailment in MW
            fict_gen_mw = fict_gen_pg
            total_curtailment_mw = float(np.sum(fict_gen_mw))

            # LMPs were computed from optimization duals by the solver
            marginal_costs = lmp

            # Calculate bus results (including curtailment)
            bus_results = self._calculate_bus_results(
                buses, theta, Pg_full_pu, Pd_pu, marginal_costs, fict_gen_mw
            )

            # Calculate generator results (real generators only)
            gen_results = self._calculate_gen_results(generators, real_gen_pg_mw)

            # Calculate total cost (real generators + curtailment penalty)
            total_cost = sum(cost[0] * real_gen_pg_mw[i]**2 + cost[1] * real_gen_pg_mw[i] + cost[2]
                           for i, cost in enumerate(real_gen_costs))
            curtailment_cost = total_curtailment_mw * voll
            total_cost_with_curtailment = total_cost + curtailment_cost

            logger.info("--- OPF DEBUG ---")
            logger.info(f"Real Gen Pmax: {real_gen_pmax * self.base_mva}")
            logger.info(f"Real Gen Costs: {real_gen_costs}")
            logger.info(f"Pg MW: {real_gen_pg_mw}")
            logger.info(f"Gen Cost: {total_cost}")
            logger.info(f"Curtailment MW: {total_curtailment_mw}")
            logger.info(f"Curtailment Cost: {curtailment_cost}")
            logger.info(f"Total Cost: {total_cost_with_curtailment}")
            logger.info("-----------------")

            logger.info(f"DC OPF solved. Cost: {total_cost:.2f} $/h, Curtailment: {total_curtailment_mw:.2f} MW")

            return OPFResult(
                status=status,
                total_cost=total_cost_with_curtailment,
                generator_results=gen_results,
                bus_results=bus_results,
                line_results=line_flows,
                objective_value=total_cost,
                total_curtailment=total_curtailment_mw,
                iterations=1
            )

        except Exception as e:
            logger.error(f"Error solving DC OPF: {str(e)}")
            raise

    # ========== LP SOLVER (linear costs) ==========

    def _solve_lp(self, n_real_gen, n_buses, real_gen_costs, real_gen_pmin,
                  real_gen_pmax, real_gen_bus_indices, Pd_pu, total_load_pu,
                  PTDF, line_rates, voll):
        """
        Solve DC OPF as Linear Program using scipy.optimize.linprog.
        Used when all quadratic cost coefficients are zero.

        Decision variables: x = [Pg_real (n_real_gen), Pg_curtail (n_buses)]
        """
        from scipy.optimize import linprog

        n_vars = n_real_gen + n_buses
        n_lines = len(PTDF)

        # === Objective: minimize c^T x ===
        # Cost in MW: cost[1] * Pg_mw = cost[1] * Pg_pu * base_mva
        c = np.zeros(n_vars)
        for i, cost in enumerate(real_gen_costs):
            c[i] = cost[1] * self.base_mva  # linear cost coefficient
        for i in range(n_buses):
            c[n_real_gen + i] = voll * self.base_mva  # VOLL penalty

        # === Equality constraint: power balance ===
        # sum(Pg_real) + sum(Pg_curtail) = total_load_pu
        # (curtailment acts as negative load, so gen + curtail = load)
        A_eq = np.zeros((1, n_vars))
        A_eq[0, :n_real_gen] = 1.0
        # Power balance: real_gen - (total_load - curtailment) = 0
        # => real_gen + curtailment = total_load
        # But curtailment reduces load, not adds generation. Correct formulation:
        # sum(Pg_real) = total_load - sum(curtailment)
        # => sum(Pg_real) + sum(curtailment) = total_load (if curtailment is subtracted from load)
        # Wait — curtailment here IS fictitious generation that offsets load at each bus
        # So: sum(Pg_real) = total_load - sum(curtailment)
        # Rearranged: sum(Pg_real) + sum(curtailment) = total_load
        # BUT the curtailment variable represents load reduction, treated as virtual gen
        # Actually in the original formulation:
        # real_pg - (total_load - curtail) = 0  =>  real_pg + curtail = total_load
        A_eq[0, n_real_gen:] = 1.0
        b_eq = np.array([total_load_pu])

        # === Inequality constraints: line flow limits ===
        # Build the injection-to-flow mapping
        # For each gen i at bus b: Pnet[b] += Pg[i]
        # For each curtail j at bus j: Pnet[j] -= (-curtail[j]) i.e. Pnet[j] += curtail[j]
        #   Actually curtail reduces demand: Pd_eff = Pd - curtail
        #   Pnet = Pg_full - Pd_eff = Pg_full - Pd + curtail
        # Flow = PTDF @ Pnet = PTDF @ (Pg_full - Pd + curtail)
        # Since Pd is constant, flow = PTDF @ Pg_full + PTDF @ curtail - PTDF @ Pd
        # We need |flow| <= line_rates
        # => PTDF @ (Pg_mapping @ x) + PTDF @ curtail_mapping @ x <= line_rates + PTDF @ Pd
        # AND -(PTDF @ (Pg_mapping @ x) + PTDF @ curtail_mapping @ x) <= line_rates - (- PTDF @ Pd)

        # Build gen-to-bus mapping matrix: M_gen (n_buses x n_real_gen)
        M_gen = np.zeros((n_buses, n_real_gen))
        for i, bus_idx in enumerate(real_gen_bus_indices):
            M_gen[bus_idx, i] += 1.0

        # Curtailment mapping: identity for bus positions
        M_curt = np.eye(n_buses)

        # Combined injection matrix: maps x -> Pnet (excluding constant Pd term)
        # Pnet = M_gen @ Pg_real + M_curt @ curtail - Pd
        # flow = PTDF @ Pnet = PTDF @ M_gen @ Pg_real + PTDF @ M_curt @ curtail - PTDF @ Pd
        H_gen = PTDF @ M_gen    # (n_lines x n_real_gen)
        H_curt = PTDF @ M_curt  # (n_lines x n_buses)
        H = np.hstack([H_gen, H_curt])  # (n_lines x n_vars)
        d = PTDF @ Pd_pu  # constant term from load

        # Constraints: -line_rates <= H @ x - d <= line_rates
        # => H @ x <= line_rates + d   AND  -H @ x <= line_rates - d
        # Rewrite as A_ub @ x <= b_ub
        A_ub = np.vstack([H, -H])
        b_ub = np.concatenate([line_rates + d, line_rates - d])

        # === Bounds ===
        bounds = []
        for i in range(n_real_gen):
            bounds.append((real_gen_pmin[i], real_gen_pmax[i]))
        for i in range(n_buses):
            bounds.append((0.0, max(0.0, Pd_pu[i])))  # can't curtail more than load

        # === Solve ===
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                         bounds=bounds, method='highs',
                         options={'maxiter': 10000, 'presolve': True})

        if result.success:
            status = "optimal"
        else:
            logger.warning(f"LP solver status: {result.message}")
            status = "suboptimal"

        Pg_opt_pu = result.x
        fict_gen_pg = result.x[n_real_gen:] * self.base_mva

        # === LMP from Lagrange multipliers ===
        bmva = self.base_mva
        n_lines = len(line_rates)
        lmp = np.zeros(n_buses)

        y_eq = result.eqlin.marginals[0]  # dual of power balance
        y_ub = result.ineqlin.marginals    # duals of line limits (non-positive)
        y_pos = y_ub[:n_lines]   # H @ x <= rate + d
        y_neg = y_ub[n_lines:]   # -H @ x <= rate - d

        # result.eqlin.marginals[0] is typically positive for sum(Pg) = Pd
        # but ineqlin.marginals (y_ub) are non-positive for Ax <= b.
        # Congestion Rent = (LMP_j - LMP_i) * Flow_ij. 
        # lambda_i = y_eq - sum(mu_k * PTDF_ki) where mu are duals of Hx <= b_ub.
        # Since mu (y_ub) are non-positive, we subtract them (or add their abs).
        for i in range(n_buses):
            congestion = np.sum((y_pos - y_neg) * PTDF[:, i])
            # y_eq is around VOLL * BMVA (positive)
            # y_pos/y_neg are non-positive. 
            # We want LMP to INCREASE if a line is congested (mu < 0).
            # So we subtract congestion if congestion is negative.
            lmp[i] = (y_eq - congestion) / bmva

        return Pg_opt_pu, fict_gen_pg, status, lmp

    def _solve_ed_lp(self, n_real_gen, n_buses, real_gen_costs, real_gen_pmin,
                     real_gen_pmax, total_load_pu):
        """Simple economic dispatch as LP (no line limits)"""
        from scipy.optimize import linprog

        # Objective: minimize sum(cost[1] * Pg_pu * base_mva)
        c = np.array([cost[1] * self.base_mva for cost in real_gen_costs])

        # Equality: sum(Pg) = total_load
        A_eq = np.ones((1, n_real_gen))
        b_eq = np.array([total_load_pu])

        bounds = list(zip(real_gen_pmin, real_gen_pmax))

        result = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds,
                         method='highs')

        if result.success:
            status = "optimal"
        else:
            logger.warning(f"ED LP solver status: {result.message}")
            status = "suboptimal"

        Pg_opt_pu = np.zeros(n_real_gen + n_buses)
        Pg_opt_pu[:n_real_gen] = result.x
        fict_gen_pg = np.zeros(n_buses)

        # LMP: uniform system lambda (no congestion)
        bmva = self.base_mva
        y_eq = result.eqlin.marginals[0]
        lmp = np.full(n_buses, y_eq / bmva)

        return Pg_opt_pu, fict_gen_pg, status, lmp

    # ========== QP SOLVER (quadratic costs) ==========

    def _solve_qp(self, n_real_gen, n_buses, real_gen_costs, real_gen_pmin,
                  real_gen_pmax, real_gen_bus_indices, Pd_pu, total_load_pu,
                  PTDF, line_rates, voll):
        """
        Solve DC OPF with quadratic costs using trust-constr (interior-point).
        Uses matrix-based constraint specification for robust convergence.
        """
        from scipy.optimize import minimize, LinearConstraint, Bounds

        n_lines = len(PTDF)
        n_vars = n_real_gen + n_buses

        # Create fictitious generators for curtailment with VOLL cost
        fict_costs = [[0, voll, 0] for _ in range(n_buses)]
        fict_min = np.zeros(n_buses)
        fict_max = Pd_pu.copy()

        all_costs = real_gen_costs + fict_costs
        all_min = np.concatenate([real_gen_pmin, fict_min])
        all_max = np.concatenate([real_gen_pmax, fict_max])

        # Pre-compute gen-to-bus mapping for vectorized operations
        M_gen = np.zeros((n_buses, n_real_gen))
        for i, bus_idx in enumerate(real_gen_bus_indices):
            M_gen[bus_idx, i] += 1.0
        M_curt = np.eye(n_buses)

        # H maps decision vars to flows: flow = H @ x - d
        H_gen = PTDF @ M_gen
        H_curt = PTDF @ M_curt
        H = np.hstack([H_gen, H_curt])
        d = PTDF @ Pd_pu

        # Cost coefficients as arrays for vectorized computation
        a_coeffs = np.array([c[0] for c in all_costs])
        b_coeffs = np.array([c[1] for c in all_costs])
        c_coeffs = np.array([c[2] for c in all_costs])
        bmva = self.base_mva

        def objective(x):
            Pg_mw = x * bmva
            return np.sum(a_coeffs * Pg_mw**2 + b_coeffs * Pg_mw + c_coeffs)

        def objective_jac(x):
            Pg_mw = x * bmva
            return (2 * a_coeffs * Pg_mw * bmva + b_coeffs * bmva)

        def objective_hess(x):
            return np.diag(2 * a_coeffs * bmva**2)

        # === Constraints using LinearConstraint objects ===

        # Power balance: sum(x) = total_load_pu
        A_eq = np.ones((1, n_vars))
        power_balance = LinearConstraint(A_eq, total_load_pu, total_load_pu)

        # Line flow limits: -line_rates <= H @ x - d <= line_rates
        # => -line_rates + d <= H @ x <= line_rates + d
        line_limits = LinearConstraint(H, -line_rates + d, line_rates + d)

        # Variable bounds
        bounds = Bounds(all_min, all_max)

        # Initial guess: economic dispatch ordering
        x0 = np.zeros(n_vars)
        x0[:n_real_gen] = self._economic_dispatch_init(
            real_gen_costs, real_gen_pmin, real_gen_pmax, total_load_pu
        )

        result = minimize(
            objective,
            x0,
            jac=objective_jac,
            hess=objective_hess,
            method='trust-constr',
            bounds=bounds,
            constraints=[power_balance, line_limits],
            options={'maxiter': 5000, 'gtol': 1e-8}
        )

        Pg_opt_pu = result.x
        fict_gen_pg = result.x[n_real_gen:] * self.base_mva
        status = "optimal" if result.success else "suboptimal"

        # Log solver info
        flows_final = H @ result.x - d
        final_viol = np.max(np.abs(flows_final) - line_rates)
        logger.info(f"QP solver: {result.message}, max violation: {final_viol*100:.4f}%")

        # === LMP from trust-constr Lagrange multipliers ===
        bmva = self.base_mva
        n_lines = len(line_rates)
        lmp = np.zeros(n_buses)

        # result.v[0] = dual of power balance, result.v[1] = duals of line limits
        # For trust-constr, eq duals are negative of marginal costs
        v_eq = -result.v[0][0]   # Flip sign for positive system lambda
        v_line = -result.v[1]    # Flip sign for line congestion duals
        
        for i in range(n_buses):
            congestion = np.sum(v_line * PTDF[:, i])
            lmp[i] = (v_eq + congestion) / bmva

        return Pg_opt_pu, fict_gen_pg, status, lmp

    def _solve_ed_qp(self, n_real_gen, n_buses, generators, real_gen_costs,
                     real_gen_pmin, real_gen_pmax, total_load_pu):
        """Simple economic dispatch with quadratic costs (no line limits)"""
        from scipy.optimize import minimize

        def objective(Pg_pu):
            Pg_mw = Pg_pu * self.base_mva
            return sum(cost[0] * Pg_mw[i]**2 + cost[1] * Pg_mw[i] + cost[2]
                      for i, cost in enumerate(real_gen_costs))

        def power_balance(Pg_pu):
            return np.sum(Pg_pu) - total_load_pu

        # Better initial guess
        Pg_init = self._economic_dispatch_init(
            real_gen_costs, real_gen_pmin, real_gen_pmax, total_load_pu
        )

        result = minimize(
            objective,
            Pg_init,
            method='SLSQP',
            bounds=list(zip(real_gen_pmin, real_gen_pmax)),
            constraints=[{'type': 'eq', 'fun': power_balance}],
            options={'maxiter': 1000, 'ftol': 1e-8}
        )

        Pg_opt_pu = np.zeros(n_real_gen + n_buses)
        Pg_opt_pu[:n_real_gen] = result.x
        fict_gen_pg = np.zeros(n_buses)
        status = "optimal" if result.success else "suboptimal"

        # LMP: uniform system lambda from marginal generator
        # At optimum, the marginal gen satisfies: 2*a*Pg_mw + b = lambda
        bmva = self.base_mva
        # Find the marginal generator (interior, not at bounds)
        system_lambda = 0.0
        for i in range(n_real_gen):
            pg_pu = result.x[i]
            a, b_coeff = real_gen_costs[i][0], real_gen_costs[i][1]
            pg_mw = pg_pu * bmva
            # Check if generator is interior (not hard against bounds)
            if pg_pu > real_gen_pmin[i] + 1e-6 and pg_pu < real_gen_pmax[i] - 1e-6:
                system_lambda = 2 * a * pg_mw + b_coeff
                break
        else:
            # All at bounds, use cheapest at max
            if n_real_gen > 0:
                pg_mw = result.x[0] * bmva
                system_lambda = 2 * real_gen_costs[0][0] * pg_mw + real_gen_costs[0][1]

        lmp = np.full(n_buses, system_lambda)

        return Pg_opt_pu, fict_gen_pg, status, lmp

    def _economic_dispatch_init(self, gen_costs, gen_pmin, gen_pmax, total_load_pu):
        """
        Compute initial guess by economic dispatch merit order.
        Dispatches cheapest generators first (by marginal cost b coefficient).
        """
        n = len(gen_costs)
        # Sort by marginal cost (linear coefficient b)
        order = sorted(range(n), key=lambda i: gen_costs[i][1])

        Pg = gen_pmin.copy()
        remaining = total_load_pu - np.sum(Pg)

        for i in order:
            available = gen_pmax[i] - Pg[i]
            dispatch = min(available, remaining)
            if dispatch > 0:
                Pg[i] += dispatch
                remaining -= dispatch
            if remaining <= 1e-10:
                break

        return Pg

    # ========== Network Building Methods ==========

    def _find_slack_bus(self, buses: List[Bus]) -> int:
        """Find the slack (reference) bus"""
        for bus in buses:
            if bus.type == 3:
                return bus.id
        return buses[0].id if buses else 1

    def _build_susceptance_matrix(self, buses: List[Bus], lines: List[Line]) -> np.ndarray:
        """Build DC susceptance matrix in per-unit"""
        n = len(buses)
        B = np.zeros((n, n))

        bus_ids = {bus.id: i for i, bus in enumerate(buses)}

        for line in lines:
            if line.from_bus in bus_ids and line.to_bus in bus_ids:
                i = bus_ids[line.from_bus]
                j = bus_ids[line.to_bus]
                x = line.x if line.x > 0 else 0.01
                b_ij = 1.0 / x

                B[i, i] += b_ij
                B[j, j] += b_ij
                B[i, j] -= b_ij
                B[j, i] -= b_ij

        return B

    def _build_ptdf_matrix(self, B: np.ndarray, lines: List[Line],
                          buses: List[Bus], bus_ids: dict, slack_bus: int) -> np.ndarray:
        """Build Power Transfer Distribution Factors (PTDF) matrix"""
        n = len(buses)
        slack_idx = bus_ids.get(slack_bus, 0)
        B_reduced = np.delete(np.delete(B, slack_idx, 0), slack_idx, 1)

        try:
            # For large systems, linalg.solve might be better for systems of eq,
            # but for PTDF we usually want the explicit inverse (B_reduced^-1).
            B_inv = np.linalg.inv(B_reduced)
        except np.linalg.LinAlgError:
            B_inv = np.linalg.pinv(B_reduced)

        # Expand B_inv back to full size (n x n) by inserting zero row/column for slack
        B_inv_full = np.zeros((n, n))
        rows = np.array([k for k in range(n) if k != slack_idx])
        B_inv_full[np.ix_(rows, rows)] = B_inv

        # Pre-allocate PTDF matrix
        PTDF = np.zeros((len(lines), n))
        
        for k, line in enumerate(lines):
            if line.from_bus in bus_ids and line.to_bus in bus_ids:
                i = bus_ids[line.from_bus]
                j = bus_ids[line.to_bus]
                x = line.x if line.x > 0 else 0.0001
                
                # PTDF_k,n = (1/x_k) * (B_inv[i, n] - B_inv[j, n])
                PTDF[k, :] = (B_inv_full[i, :] - B_inv_full[j, :]) / x

        return PTDF
    def _extract_loads(self, buses: List[Bus], loads) -> tuple:
        """Extract real and reactive power demands in per-unit"""
        n = len(buses)
        Pd = np.zeros(n)
        Qd = np.zeros(n)

        bus_ids = {bus.id: i for i, bus in enumerate(buses)}

        if loads:
            for load in loads:
                if load.bus in bus_ids:
                    i = bus_ids[load.bus]
                    Pd[i] = load.pd / self.base_mva
                    Qd[i] = load.qd / self.base_mva

        return Pd, Qd

    def _solve_theta(self, B: np.ndarray, Pnet: np.ndarray, slack_bus: int) -> np.ndarray:
        """Solve for voltage angles"""
        n = B.shape[0]
        slack_idx = slack_bus - 1 if slack_bus > 0 else 0

        B_reduced = np.delete(np.delete(B, slack_idx, 0), slack_idx, 1)
        P_reduced = np.delete(Pnet, slack_idx)

        try:
            theta_reduced = np.linalg.solve(B_reduced, P_reduced)
        except np.linalg.LinAlgError:
            theta_reduced = np.linalg.lstsq(B_reduced, P_reduced, rcond=None)[0]

        theta = np.insert(theta_reduced, slack_idx, 0)
        return theta

    def _calculate_line_flows(self, lines: List[Line], buses: List[Bus],
                              theta: np.ndarray, lmp: np.ndarray = None) -> List[LineResult]:
        """Calculate power flows on transmission lines"""
        bus_ids = {bus.id: i for i, bus in enumerate(buses)}
        line_results = []

        for line in lines:
            if line.from_bus in bus_ids and line.to_bus in bus_ids:
                i = bus_ids[line.from_bus]
                j = bus_ids[line.to_bus]
                x = line.x if line.x > 0 else 0.01
                b_ij = 1.0 / x

                flow_pu = b_ij * (theta[i] - theta[j])
                flow_mw = flow_pu * self.base_mva

                rate = line.rate_a if line.rate_a > 0 else 250.0
                loading = abs(flow_mw) / rate * 100

                # Congestion rent = (LMP_to - LMP_from) * flow_from_to
                congestion_rent = 0.0
                if lmp is not None:
                    congestion_rent = (lmp[j] - lmp[i]) * flow_mw

                line_results.append(LineResult(
                    from_bus=line.from_bus,
                    to_bus=line.to_bus,
                    flow_mw=flow_mw,
                    flow_mvar=0.0,
                    loading_percent=loading,
                    congestion_rent=congestion_rent
                ))

        return line_results

    def _calculate_bus_results(self, buses: List[Bus], theta: np.ndarray,
                               Pg: np.ndarray, Pd: np.ndarray,
                               marginal_costs: np.ndarray,
                               curtailment: np.ndarray = None) -> List[BusResult]:
        """Calculate bus-level results"""
        bus_results = []

        if curtailment is None:
            curtailment = np.zeros(len(buses))

        for i, bus in enumerate(buses):
            pl_pu = Pg[i] - Pd[i]
            pl_mw = pl_pu * self.base_mva

            bus_results.append(BusResult(
                bus=bus.id,
                va=np.degrees(theta[i]),
                vm=bus.v_mag,
                pl=pl_mw,
                ql=0.0,
                marginal_cost=marginal_costs[i],
                curtailment=curtailment[i]
            ))

        return bus_results

    # NOTE: _calculate_marginal_costs removed — LMPs are now computed
    # directly from optimization dual variables (Lagrange multipliers)
    # inside each solver method (_solve_lp, _solve_qp, _solve_ed_lp, _solve_ed_qp).

    def _calculate_gen_results(self, generators: List[Generator],
                               Pg_mw: np.ndarray) -> List[GeneratorResult]:
        """Calculate generator-level results"""
        gen_results = []

        for gen, pg_mw in zip(generators, Pg_mw):
            qg_mw = 0.0
            cost = gen.cost[0] * pg_mw**2 + gen.cost[1] * pg_mw + gen.cost[2]

            gen_results.append(GeneratorResult(
                bus=gen.bus,
                pg=pg_mw,
                qg=qg_mw,
                cost=cost
            ))

        return gen_results
