"""Battery Domain Models and Validations.

Encapsulates battery specifications, physical constraints, state of charge (SOC),
and degradation state.
"""

from enum import Enum
from pydantic import BaseModel, Field, model_validator


class BatteryHealthStatus(str, Enum):
    """Battery state of health categorization."""
    EXCELLENT = "EXCELLENT"  # Degradation factor >= 0.95
    GOOD = "GOOD"            # Degradation factor 0.85 - 0.95
    ATTENTION = "ATTENTION"  # Degradation factor 0.75 - 0.85
    CRITICAL = "CRITICAL"    # Degradation factor < 0.75 (replacement advisory)


class BatterySpecification(BaseModel):
    """Immutable hardware specifications for a vehicle's battery pack."""
    capacity_kwh: float = Field(..., gt=0.0, description="Nominal battery pack capacity in kWh")
    max_charge_power_kw: float = Field(..., gt=0.0, description="Maximum DC/AC continuous charging power in kW")
    max_discharge_power_kw: float = Field(default=150.0, gt=0.0, description="Maximum discharge output power in kW")
    nominal_voltage_v: float = Field(default=400.0, gt=0.0, description="Nominal system pack voltage")
    chemistry: str = Field(default="NMC", description="Battery chemistry type (e.g., NMC, LFP)")
    degradation_factor: float = Field(
        default=1.0,
        ge=0.5,
        le=1.0,
        description="Health multiplier: actual current usable capacity = nominal * degradation_factor",
    )
    cycle_count: int = Field(default=0, ge=0, description="Cumulative equivalent full battery cycles")

    @property
    def effective_capacity_kwh(self) -> float:
        """Calculates actual usable capacity factoring in battery degradation."""
        return round(self.capacity_kwh * self.degradation_factor, 2)


class BatteryState(BaseModel):
    """Real-time operational telemetry and state of charge limits."""
    soc: float = Field(..., ge=0.0, le=100.0, description="Current State of Charge percentage (0-100%)")
    min_soc_limit: float = Field(default=15.0, ge=0.0, le=100.0, description="Minimum operational safety floor (%)")
    max_soc_limit: float = Field(default=90.0, ge=0.0, le=100.0, description="Maximum daily operational ceiling (%)")
    health_status: BatteryHealthStatus = Field(default=BatteryHealthStatus.GOOD)
    temperature_c: float = Field(default=25.0, description="Battery pack internal temperature in Celsius")

    @model_validator(mode="after")
    def validate_soc_bounds(self) -> "BatteryState":
        """Ensures minimum SOC limit is strictly less than maximum SOC limit."""
        if self.min_soc_limit >= self.max_soc_limit:
            raise ValueError(
                f"min_soc_limit ({self.min_soc_limit}%) must be strictly less than max_soc_limit ({self.max_soc_limit}%)"
            )
        return self
