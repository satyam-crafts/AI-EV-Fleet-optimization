"""Vehicle Domain Models.

Represents electric vehicles in the commercial fleet, their battery configuration,
operational status, telemetry, and energy consumption metrics.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from backend.app.domain.battery import BatterySpecification, BatteryState


class VehicleStatus(str, Enum):
    """Operational status of a fleet vehicle."""
    IDLE = "IDLE"
    EN_ROUTE = "EN_ROUTE"
    CHARGING = "CHARGING"
    MAINTENANCE = "MAINTENANCE"


class Vehicle(BaseModel):
    """Core domain model representing a commercial electric fleet vehicle."""
    id: str = Field(..., description="Unique vehicle identifier (e.g. EV-01)")
    name: str = Field(..., description="Human-readable fleet vehicle name")
    make: str = Field(..., description="Manufacturer (e.g. Rivian, Ford, BrightDrop)")
    model: str = Field(..., description="Vehicle model name")
    battery_spec: BatterySpecification
    battery_state: BatteryState
    consumption_rate_kwh_per_km: float = Field(
        ...,
        gt=0.0,
        description="Average nominal energy consumption rate in kWh per km",
    )
    current_status: VehicleStatus = Field(default=VehicleStatus.IDLE)
    current_location: str = Field(default="Central Depot", description="Depot or route location")
    assigned_route_id: Optional[str] = Field(default=None, description="Currently active route ID if assigned")
    charging_station_id: Optional[str] = Field(default=None, description="Station ID if currently charging")
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def current_energy_kwh(self) -> float:
        """Total energy currently stored in the battery (kWh)."""
        return round(self.battery_spec.effective_capacity_kwh * (self.battery_state.soc / 100.0), 2)

    @property
    def usable_energy_kwh(self) -> float:
        """Usable energy remaining above the minimum SOC safety reserve (kWh)."""
        usable_soc = max(0.0, self.battery_state.soc - self.battery_state.min_soc_limit)
        return round(self.battery_spec.effective_capacity_kwh * (usable_soc / 100.0), 2)

    @property
    def estimated_range_km(self) -> float:
        """Estimated drivable range (km) down to minimum safety reserve."""
        if self.consumption_rate_kwh_per_km <= 0:
            return 0.0
        return round(self.usable_energy_kwh / self.consumption_rate_kwh_per_km, 1)

    @property
    def total_nominal_range_km(self) -> float:
        """Estimated range from 100% down to 0% at nominal capacity."""
        return round(self.battery_spec.effective_capacity_kwh / self.consumption_rate_kwh_per_km, 1)
