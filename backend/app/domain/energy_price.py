"""Energy Pricing and Time-of-Use (TOU) Tariff Domain Models.

Defines hourly electricity prices, peak, mid-peak, and off-peak rate tiers.
"""

from enum import Enum
from typing import List
from pydantic import BaseModel, Field, model_validator


class TariffRateType(str, Enum):
    """Tariff tier classification."""
    OFF_PEAK = "OFF_PEAK"
    MID_PEAK = "MID_PEAK"
    ON_PEAK = "ON_PEAK"
    CRITICAL_PEAK = "CRITICAL_PEAK"


class TimeOfUseWindow(BaseModel):
    """A scheduled tariff interval across a 24-hour day."""
    start_hour: int = Field(..., ge=0, le=23, description="Starting hour of interval (0-23)")
    end_hour: int = Field(..., ge=1, le=24, description="Ending hour of interval (1-24)")
    rate_per_kwh: float = Field(..., gt=0.0, description="Electricity price per kWh in USD")
    rate_type: TariffRateType = Field(default=TariffRateType.OFF_PEAK)
    label: str = Field(default="Standard Rate")

    @model_validator(mode="after")
    def validate_hours(self) -> "TimeOfUseWindow":
        """Ensures start hour is strictly earlier than end hour."""
        if self.start_hour >= self.end_hour:
            raise ValueError(f"start_hour ({self.start_hour}) must be strictly less than end_hour ({self.end_hour})")
        return self


class EnergyPriceSchedule(BaseModel):
    """24-Hour Electricity Tariff Schedule."""
    schedule_id: str = Field(default="default_tou", description="Schedule identifier")
    name: str = Field(default="Commercial Fleet TOU Tariff")
    currency: str = Field(default="USD")
    windows: List[TimeOfUseWindow] = Field(..., min_length=1)

    def get_rate_at_hour(self, hour: int) -> float:
        """Retrieves rate ($/kWh) for a specific hour of day (0-23)."""
        normalized_hour = hour % 24
        for w in self.windows:
            if w.start_hour <= normalized_hour < w.end_hour:
                return w.rate_per_kwh
        # Fallback to first window rate if gap in configuration
        return self.windows[0].rate_per_kwh

    def get_rate_type_at_hour(self, hour: int) -> TariffRateType:
        """Retrieves rate tier classification for a specific hour of day (0-23)."""
        normalized_hour = hour % 24
        for w in self.windows:
            if w.start_hour <= normalized_hour < w.end_hour:
                return w.rate_type
        return TariffRateType.MID_PEAK

    @property
    def off_peak_rate(self) -> float:
        """Lowest off-peak rate in the schedule."""
        rates = [w.rate_per_kwh for w in self.windows if w.rate_type == TariffRateType.OFF_PEAK]
        return min(rates) if rates else min(w.rate_per_kwh for w in self.windows)

    @property
    def peak_rate(self) -> float:
        """Highest peak rate in the schedule."""
        rates = [w.rate_per_kwh for w in self.windows if w.rate_type == TariffRateType.ON_PEAK]
        return max(rates) if rates else max(w.rate_per_kwh for w in self.windows)
