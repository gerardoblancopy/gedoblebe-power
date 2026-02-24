"""
Pydantic models for DC OPF Simulator API
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Bus(BaseModel):
    """Bus model"""
    id: int
    name: Optional[str] = Field(None, description="Bus name (display label)")
    type: int = Field(1, description="Bus type: 1=PQ, 2=PV, 3=slack")
    v_mag: float = Field(1.0, description="Voltage magnitude (pu)")
    v_ang: float = Field(0.0, description="Voltage angle (degrees)")
    g_shunt: float = Field(0.0, description="Shunt conductance (pu)")
    b_shunt: float = Field(0.0, description="Shunt susceptance (pu)")
    base_kv: float = Field(345.0, description="Base voltage (kV)")
    zone: int = Field(1, description="Zone number")


class Generator(BaseModel):
    """Generator model"""
    id: Optional[str] = Field(None, description="Unique generator ID")
    name: Optional[str] = Field(None, description="Generator name (display label)")
    bus: int = Field(..., description="Bus number where generator is connected")
    pg: float = Field(0.0, description="Real power output (MW)")
    qg: float = Field(0.0, description="Reactive power output (MVAR)")
    vg: float = Field(1.0, description="Voltage setpoint (pu)")
    mbase: float = Field(100.0, description="Machine MVA base")
    pmax: float = Field(250.0, description="Maximum real power output (MW)")
    pmin: float = Field(10.0, description="Minimum real power output (MW)")
    qmax: float = Field(300.0, description="Maximum reactive power (MVAR)")
    qmin: float = Field(-300.0, description="Minimum reactive power (MVAR)")
    cost: List[float] = Field(default_factory=lambda: [0, 25, 0],
                               description="Cost coefficients [a, b, c] in $/h")
    status: int = Field(1, description="Status (1=in service, 0=out of service)")


class Line(BaseModel):
    """Transmission line model"""
    from_bus: int = Field(..., description="From bus number")
    to_bus: int = Field(..., description="To bus number")
    r: float = Field(0.0, description="Resistance (pu)")
    x: float = Field(..., description="Reactance (pu)")
    b: float = Field(0.0, description="Susceptance (pu)")
    rate_a: float = Field(250.0, description="Long term rating (MW)")
    rate_b: float = Field(250.0, description="Short term rating (MW)")
    rate_c: float = Field(250.0, description="Emergency rating (MW)")
    status: int = Field(1, description="Status (1=in service, 0=out of service)")


class Load(BaseModel):
    """Load model"""
    bus: int = Field(..., description="Bus number where load is connected")
    pd: float = Field(..., description="Real power demand (MW)")
    qd: float = Field(0.0, description="Reactive power demand (MVAR)")


class PowerSystem(BaseModel):
    """Complete power system model"""
    buses: List[Bus] = Field(default_factory=list)
    generators: List[Generator] = Field(default_factory=list)
    lines: List[Line] = Field(default_factory=list)
    loads: List[Load] = Field(default_factory=list)
    base_mva: float = Field(100.0, description="System base MVA")


class CaseData(BaseModel):
    """Parsed case data"""
    buses: List[Bus] = Field(default_factory=list)
    generators: List[Generator] = Field(default_factory=list)
    lines: List[Line] = Field(default_factory=list)
    loads: List[Load] = Field(default_factory=list)
    base_mva: float = Field(100.0, description="System base MVA")


class OPFRequest(BaseModel):
    """OPF solve request"""
    case_data: Optional[PowerSystem] = None
    voll: float = Field(10000.0, description="Value of Lost Load ($/MWh)")
    enforce_line_limits: bool = Field(True, description="Enforce line loading constraints")
    remove_isolated: bool = Field(False, description="Automatically remove buses and components not connected to the slack bus")


class GeneratorResult(BaseModel):
    """Generator result"""
    id: Optional[str] = Field(None, description="Generator ID")
    bus: int
    pg: float = Field(..., description="Real power output (MW)")
    qg: float = Field(..., description="Reactive power output (MVAR)")
    cost: float = Field(..., description="Generation cost ($/h)")


class BusResult(BaseModel):
    """Bus result"""
    bus: int
    va: float = Field(..., description="Voltage angle (degrees)")
    vm: float = Field(1.0, description="Voltage magnitude (pu)")
    pl: float = Field(..., description="Net real power injection (MW)")
    ql: float = Field(..., description="Net reactive power injection (MVAR)")
    marginal_cost: float = Field(0.0, description="Marginal cost ($/MWh)")
    curtailment: float = Field(0.0, description="Load curtailment at this bus (MW)")


class LineResult(BaseModel):
    """Line flow result"""
    from_bus: int
    to_bus: int
    flow_mw: float = Field(..., description="Real power flow (MW)")
    flow_mvar: float = Field(0.0, description="Reactive power flow (MVAR)")
    loading_percent: float = Field(..., description="Line loading percentage")
    congestion_rent: float = Field(0.0, description="Congestion rent ($/h)")


class OPFResult(BaseModel):
    """OPF solution result"""
    status: str = Field("optimal", description="Solution status")
    total_cost: float = Field(..., description="Total generation cost ($/h)")
    generator_results: List[GeneratorResult] = Field(default_factory=list)
    bus_results: List[BusResult] = Field(default_factory=list)
    line_results: List[LineResult] = Field(default_factory=list)
    objective_value: float = Field(..., description="Objective function value")
    total_curtailment: float = Field(0.0, description="Total load curtailment (MW)")
    iterations: int = Field(0, description="Number of iterations")


class ExportFormat(str):
    """Export format options"""
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"
