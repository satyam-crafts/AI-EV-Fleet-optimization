"""Route Domain Models.

Defines delivery routes, waypoints, operational schedules, distance,
and required energy profiles.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class RouteWaypoint(BaseModel):
    """Waypoint or stop along a commercial delivery route."""
    name: str = Field(..., description="Stop or hub name")
    lat: Optional[float] = Field(default=None, description="Latitude")
    lng: Optional[float] = Field(default=None, description="Longitude")
    stop_duration_minutes: int = Field(default=15, ge=0, description="Dwell time at stop in minutes")


class Route(BaseModel):
    """A scheduled delivery route with energy and schedule constraints."""
    id: str = Field(..., description="Unique route identifier (e.g. R-01)")
    name: str = Field(..., description="Route name / description")
    origin: str = Field(..., description="Starting depot or location")
    destination: str = Field(..., description="Final depot or destination")
    distance_km: float = Field(..., gt=0.0, description="Total route distance in km")
    estimated_duration_minutes: int = Field(..., gt=0, description="Expected total drive time in minutes")
    required_energy_kwh: float = Field(..., gt=0.0, description="Estimated energy required to complete the route")
    departure_time: datetime = Field(..., description="Mandatory departure timestamp")
    required_arrival_time: datetime = Field(..., description="Mandatory completion deadline")
    elevation_gain_m: float = Field(default=0.0, ge=0.0, description="Cumulative elevation ascent in meters")
    cargo_weight_kg: float = Field(default=500.0, ge=0.0, description="Payload weight in kg")
    assigned_vehicle_id: Optional[str] = Field(default=None, description="Vehicle ID assigned to this route")
    priority: int = Field(default=1, ge=1, le=3, description="1=Normal, 2=High, 3=Critical")
    waypoints: List[RouteWaypoint] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_schedule(self) -> "Route":
        """Ensures route departure occurs strictly prior to required arrival."""
        if self.departure_time >= self.required_arrival_time:
            raise ValueError(
                f"departure_time ({self.departure_time}) must be earlier than required_arrival_time ({self.required_arrival_time})"
            )
        return self

    @property
    def total_scheduled_duration_minutes(self) -> int:
        """Scheduled duration window from departure to required arrival."""
        diff = self.required_arrival_time - self.departure_time
        return int(diff.total_seconds() / 60)
