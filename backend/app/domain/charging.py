"""Charging Infrastructure Domain Models.

Represents charging stations, ports, power capacities, connector standards,
and charging sessions.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ConnectorType(str, Enum):
    """EV Charging Connector Standards."""
    CCS2 = "CCS2"
    TYPE_2 = "TYPE_2"
    CHADEMO = "CHADEMO"
    TESLA_NACS = "TESLA_NACS"


class ChargingStationStatus(str, Enum):
    """Operational status of a charging station/port."""
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"


class ChargingPort(BaseModel):
    """An individual plug/connector on a charging station."""
    port_id: str = Field(..., description="Port identifier (e.g. P-1)")
    connector_type: ConnectorType = Field(default=ConnectorType.CCS2)
    max_power_kw: float = Field(..., gt=0.0, description="Max power output in kW")
    status: ChargingStationStatus = Field(default=ChargingStationStatus.AVAILABLE)
    current_vehicle_id: Optional[str] = Field(default=None)


class ChargingStation(BaseModel):
    """Depot or en-route charging station entity."""
    id: str = Field(..., description="Unique station ID (e.g. CS-01)")
    name: str = Field(..., description="Human-readable station name")
    location: str = Field(default="Depot Charging Bay")
    total_power_capacity_kw: float = Field(..., gt=0.0, description="Grid connection or transformer capacity in kW")
    charging_efficiency: float = Field(
        default=0.92,
        ge=0.70,
        le=1.0,
        description="Charger-to-battery efficiency factor (e.g. 0.92 for 92%)",
    )
    ports: List[ChargingPort] = Field(..., min_length=1)
    base_cost_per_kwh: float = Field(default=0.0, ge=0.0, description="Base service fee per kWh if applicable")

    @property
    def available_ports_count(self) -> int:
        """Count of currently unoccupied and available ports."""
        return sum(1 for p in self.ports if p.status == ChargingStationStatus.AVAILABLE)

    @property
    def max_port_power_kw(self) -> float:
        """Maximum power achievable across any individual port."""
        return max(p.max_power_kw for p in self.ports)


class ChargingSession(BaseModel):
    """A planned or recorded charging event."""
    session_id: str = Field(..., description="Unique session ID")
    vehicle_id: str = Field(..., description="Vehicle being charged")
    station_id: str = Field(..., description="Charging station used")
    port_id: str = Field(..., description="Port ID used")
    start_time: datetime
    end_time: datetime
    start_soc: float = Field(..., ge=0.0, le=100.0)
    target_soc: float = Field(..., ge=0.0, le=100.0)
    energy_delivered_kwh: float = Field(..., ge=0.0)
    charging_power_kw: float = Field(..., gt=0.0)
    estimated_cost: float = Field(..., ge=0.0)
    status: str = Field(default="PLANNED", description="PLANNED, IN_PROGRESS, COMPLETED")
