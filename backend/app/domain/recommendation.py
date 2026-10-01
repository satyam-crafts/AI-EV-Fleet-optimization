"""Recommendation and Structured Reasoning Domain Models.

Defines the structure for auditable recommendations, including quantitative decisions,
mathematical reasons, verified constraints, and operational warnings.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RecommendationType(str, Enum):
    """Categorization of fleet recommendations."""
    CHARGE_SCHEDULE = "CHARGE_SCHEDULE"
    ROUTE_ASSIGNMENT = "ROUTE_ASSIGNMENT"
    LOAD_SHIFT = "LOAD_SHIFT"
    BATTERY_HEALTH_ACTION = "BATTERY_HEALTH_ACTION"
    INFEASIBILITY_ALERT = "INFEASIBILITY_ALERT"


class StructuredReasoning(BaseModel):
    """Auditable mathematical and operational justification for a decision.

    Guarantees full transparency without relying on opaque LLM hallucinations.
    """
    decision: str = Field(..., description="The concrete operational action recommended")
    reason: str = Field(..., description="Deterministic mathematical justification")
    inputs_considered: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key numerical inputs evaluated (e.g. current SOC, route energy, tariff)",
    )
    constraints_satisfied: List[str] = Field(
        default_factory=list,
        description="List of hard constraints verified as satisfied",
    )
    estimated_energy_kwh: float = Field(default=0.0, description="Energy involved in this decision")
    estimated_cost: float = Field(default=0.0, description="Financial cost ($) for this action")
    assumptions: List[str] = Field(
        default_factory=list,
        description="Operational assumptions made (e.g. charger efficiency 92%)",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal operational flags (e.g. turnaround buffer < 45m)",
    )


class Recommendation(BaseModel):
    """Top-level recommendation entity provided to fleet operators."""
    id: str = Field(..., description="Unique recommendation ID")
    recommendation_type: RecommendationType
    vehicle_id: Optional[str] = Field(default=None)
    route_id: Optional[str] = Field(default=None)
    station_id: Optional[str] = Field(default=None)
    title: str = Field(..., description="Concise human-readable title")
    summary: str = Field(..., description="Short executive summary")
    reasoning: StructuredReasoning
    priority: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="1.0 for deterministic proof")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
