"""
MATPOWER case file parser
"""

import re
import numpy as np
from typing import List
import logging

from app.models.schemas import Bus, Generator, Line, Load, CaseData

logger = logging.getLogger(__name__)


class MatpowerParser:
    """Parser for MATPOWER format case files"""

    def __init__(self):
        self.base_mva = 100.0

    def parse_text(self, text: str) -> CaseData:
        """Parse MATPOWER format case file from text"""
        try:
            # Remove comments
            lines = []
            for line in text.split('\n'):
                # Remove MATLAB comments
                if '%' in line:
                    line = line.split('%')[0]
                lines.append(line)
            text = '\n'.join(lines)

            # Extract base MVA
            base_mva_match = re.search(r'(?:mpc\.)?baseMVA\s*=\s*([\d.]+)', text)
            if base_mva_match:
                self.base_mva = float(base_mva_match.group(1))

            # Parse bus and load data
            buses, loads = self._parse_bus_data(text)

            # Parse generator data
            generators = self._parse_gen_data(text)

            # Parse branch data
            lines_data = self._parse_branch_data(text)

            logger.info(f"Parsed {len(buses)} buses, {len(generators)} generators, "
                       f"{len(lines_data)} lines, {len(loads)} loads")

            return CaseData(
                buses=buses,
                generators=generators,
                lines=lines_data,
                loads=loads,
                base_mva=self.base_mva
            )

        except Exception as e:
            logger.error(f"Error parsing MATPOWER file: {str(e)}")
            raise ValueError(f"Failed to parse MATPOWER file: {str(e)}")

    def _parse_bus_data(self, text: str) -> tuple[List[Bus], List[Load]]:
        """Extract bus and load data from MATPOWER format"""
        buses = []
        loads = []

        # Find bus matrix
        bus_match = re.search(
            r'(?:mpc\.)?bus\s*=\s*\[(.*?)\]\s*;?',
            text,
            re.DOTALL | re.IGNORECASE
        )

        if not bus_match:
            logger.warning("No bus matrix found in MATPOWER text")
            return buses, loads

        bus_text = bus_match.group(1)
        rows = self._parse_matrix_rows(bus_text)

        for row in rows:
            if len(row) >= 2:
                bus_id = int(row[0])
                bus_type = int(row[1]) if len(row) > 1 else 1
                pd = float(row[2]) if len(row) > 2 and row[2] else 0.0
                qd = float(row[3]) if len(row) > 3 and row[3] else 0.0
                vm = float(row[7]) if len(row) > 7 and row[7] else 1.0
                va = float(row[8]) if len(row) > 8 and row[8] else 0.0
                base_kv = float(row[9]) if len(row) > 9 and row[9] else 345.0

                buses.append(Bus(
                    id=bus_id,
                    type=bus_type,
                    v_mag=vm,
                    v_ang=va,
                    base_kv=base_kv,
                    zone=1
                ))

                # Extract load if present
                if pd > 0 or qd != 0:
                    loads.append(Load(
                        bus=bus_id,
                        pd=pd,
                        qd=qd
                    ))

        return buses, loads

    def _parse_gen_data(self, text: str) -> List[Generator]:
        """Extract generator data from MATPOWER format"""
        generators = []

        # Find generator matrix
        gen_match = re.search(
            r'(?:mpc\.)?gen\s*=\s*\[(.*?)\]\s*;?',
            text,
            re.DOTALL | re.IGNORECASE
        )

        if not gen_match:
            return generators

        gen_text = gen_match.group(1)
        rows = self._parse_matrix_rows(gen_text)

        for idx, row in enumerate(rows):
            if len(row) >= 2:
                bus = int(row[0])
                pg = float(row[1]) if row[1] else 0.0
                qg = float(row[2]) if row[2] else 0.0
                qmax = float(row[3]) if len(row) > 3 and row[3] else 300.0
                qmin = float(row[4]) if len(row) > 4 and row[4] else -300.0
                vg = float(row[5]) if len(row) > 5 and row[5] else 1.0
                mbase = float(row[6]) if len(row) > 6 and row[6] else 100.0
                pmax = float(row[8]) if len(row) > 8 and row[8] else 250.0
                pmin = float(row[9]) if len(row) > 9 and row[9] else 0.0

                status = int(float(row[7])) if len(row) > 7 and row[7] else 1

                # Generate unique ID: G-{bus}-{sequence_count_at_bus}
                bus_gen_count = len([g for g in generators if g.bus == bus])
                gen_id = f"G-{bus}-{bus_gen_count + 1}"

                generators.append(Generator(
                    id=gen_id,
                    bus=bus,
                    pg=pg,
                    qg=qg,
                    vg=vg,
                    mbase=mbase,
                    pmax=pmax,
                    pmin=pmin,
                    qmax=qmax,
                    qmin=qmin,
                    status=status,
                    cost=[0, 25, 0]  # Default cost, will be overridden by gencost
                ))

        # Parse generator costs
        try:
            gencost = self._parse_gencost(text)
            if not gencost:
                logger.warning("No gencost data found, using default linear cost [0, 25, 0]")
                gencost = [[0, 25, 0]] * len(generators)
            
            for i, cost in enumerate(gencost):
                if i < len(generators):
                    generators[i].cost = cost
        except Exception as e:
            logger.warning(f"Failed to parse gencost, using defaults: {e}")
            # Keep default costs assigned in Generator constructor


        return generators

    def _parse_gencost(self, text: str) -> List[List[float]]:
        """Extract generator cost data"""
        costs = []

        # Find gencost matrix
        cost_match = re.search(
            r'(?:mpc\.)?gencost\s*=\s*\[(.*?)\]\s*;?',
            text,
            re.DOTALL | re.IGNORECASE
        )

        if not cost_match:
            return [[0, 25, 0]] * 10  # Default costs

        cost_text = cost_match.group(1)
        rows = self._parse_matrix_rows(cost_text)

        for row in rows:
            if len(row) >= 5:
                model = int(row[0])
                if model == 2:  # Polynomial cost
                    n = int(row[3])
                    if len(row) >= 4 + n:
                        # Cost coefficients in decreasing order: c_{n-1}, ..., c0
                        # We want exactly [c2, c1, c0]
                        raw_coeffs = [float(x) for x in row[4:4+n]]
                        
                        # Pad with leading zeros to make it at least 3 elements
                        coeffs = [0.0] * max(0, 3 - n) + raw_coeffs
                        
                        # Use only the last 3 (c2, c1, c0) or first 3? 
                        # MATPOWER n=3 means [c2, c1, c0]. 
                        # If n > 3, we take the last 3 for simplicity (quadratic approx)
                        costs.append(coeffs[-3:])

        return costs if costs else [[0, 25, 0]] * len(rows)

    def _parse_branch_data(self, text: str) -> List[Line]:
        """Extract branch data from MATPOWER format"""
        lines = []

        # Find branch matrix
        branch_match = re.search(
            r'(?:mpc\.)?branch\s*=\s*\[(.*?)\]\s*;?',
            text,
            re.DOTALL | re.IGNORECASE
        )

        if not branch_match:
            return lines

        branch_text = branch_match.group(1)
        rows = self._parse_matrix_rows(branch_text)

        for row in rows:
            if len(row) >= 4:
                from_bus = int(row[0])
                to_bus = int(row[1])
                r = float(row[2]) if row[2] else 0.0
                x = float(row[3]) if row[3] else 0.01
                b = float(row[4]) if len(row) > 4 and row[4] else 0.0
                rate_a = float(row[5]) if len(row) > 5 and row[5] else 250.0

                status = int(float(row[10])) if len(row) > 10 and row[10] else 1

                lines.append(Line(
                    from_bus=from_bus,
                    to_bus=to_bus,
                    r=r,
                    x=x,
                    b=b,
                    rate_a=rate_a,
                    status=status
                ))

        return lines



    def _parse_matrix_rows(self, text: str) -> List[List[str]]:
        """Parse matrix rows from MATPOWER text"""
        rows = []
        
        # Split by semicolons OR newlines
        # This handles both [ 1 2 ; 3 4 ] and [ 1 2 \n 3 4 ]
        raw_rows = re.split(r'[;\n]', text)

        for row_str in raw_rows:
            row_str = row_str.strip()
            if not row_str:
                continue
                
            # Split by whitespace (spaces or tabs)
            values = row_str.split()
            # Filter out empty strings
            values = [v for v in values if v]
            if values:
                rows.append(values)

        return rows

