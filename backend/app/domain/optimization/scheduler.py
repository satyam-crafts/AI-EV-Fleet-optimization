"""Smart Charging Scheduler.

Schedules electric vehicle charging sessions to minimize electricity tariffs,
respect charging power and station availability constraints, and shift load
away from peak grid windows.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import uuid

from backend.app.domain.vehicle import Vehicle
from backend.app.domain.charging import ChargingStation, ChargingStationStatus
from backend.app.domain.energy_price import EnergyPriceSchedule, TariffRateType
from backend.app.domain.optimization.models import ChargingPlan
from backend.app.domain.calculations.charging_math import (
    calculate_effective_charging_power,
    calculate_charging_duration_minutes,
    calculate_charging_cost,
    calculate_soc_after_charging,
)


class PortOccupancyTracker:
    """Tracks scheduled charging time intervals on each charger port to prevent collisions."""

    def __init__(self):
        # Maps (station_id, port_id) -> list of (start_time, end_time)
        self.reservations: Dict[Tuple[str, str], List[Tuple[datetime, datetime]]] = {}

    def is_port_available(
        self,
        station_id: str,
        port_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> bool:
        """Checks if a port is unoccupied during the proposed window."""
        key = (station_id, port_id)
        if key not in self.reservations:
            return True
        for res_start, res_end in self.reservations[key]:
            # Overlap condition: not (end <= res_start or start >= res_end)
            if not (end_time <= res_start or start_time >= res_end):
                return False
        return True

    def book_port(
        self,
        station_id: str,
        port_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        """Reserves a port window."""
        key = (station_id, port_id)
        if key not in self.reservations:
            self.reservations[key] = []
        self.reservations[key].append((start_time, end_time))


def schedule_smart_charging_session(
    vehicle: Vehicle,
    target_soc: float,
    deadline: datetime,
    available_from: datetime,
    charging_stations: List[ChargingStation],
    price_schedule: EnergyPriceSchedule,
    tracker: PortOccupancyTracker,
) -> Optional[ChargingPlan]:
    """Finds the optimal charging station, port, and time window to charge the vehicle.

    Objectives:
    1. Deliver required energy before deadline.
    2. Minimize total electricity cost by prioritizing off-peak TOU tariff hours.
    3. Shift charging away from peak hours (16:00 - 21:00) when possible.
    """
    if vehicle.battery_state.soc >= target_soc:
        return None

    effective_cap = vehicle.battery_spec.effective_capacity_kwh
    delta_soc = target_soc - vehicle.battery_state.soc
    energy_needed_kwh = round(effective_cap * (delta_soc / 100.0), 2)

    if energy_needed_kwh <= 0.0:
        return None

    best_plan: Optional[ChargingPlan] = None
    best_cost = float("inf")

    # Evaluate candidate stations and ports
    for station in charging_stations:
        for port in station.ports:
            if port.status != ChargingStationStatus.AVAILABLE:
                continue

            duration_min = calculate_charging_duration_minutes(
                energy_needed_kwh=energy_needed_kwh,
                charger_power_kw=port.max_power_kw,
                vehicle_max_power_kw=vehicle.battery_spec.max_charge_power_kw,
                efficiency=station.charging_efficiency,
            )

            # Latest possible start time so session completes by deadline
            latest_start = deadline - timedelta(minutes=duration_min)
            if latest_start < available_from:
                # Cannot complete before deadline at this power level
                continue

            # Candidate start times: scan every 30 minutes in [available_from, latest_start]
            # to find cheapest TOU window
            step = timedelta(minutes=30)
            curr = available_from
            while curr <= latest_start:
                candidate_start = curr
                candidate_end = candidate_start + timedelta(minutes=duration_min)

                if tracker.is_port_available(station.id, port.port_id, candidate_start, candidate_end):
                    effective_power = calculate_effective_charging_power(
                        port.max_power_kw,
                        vehicle.battery_spec.max_charge_power_kw,
                    )
                    cost, grid_kwh, rate_type, avg_rate = calculate_charging_cost(
                        start_time=candidate_start,
                        duration_minutes=duration_min,
                        charging_power_kw=effective_power,
                        efficiency=station.charging_efficiency,
                        price_schedule=price_schedule,
                    )

                    # Check if shifted from immediate arrival / peak window
                    shifted_from_peak = (
                        rate_type == TariffRateType.OFF_PEAK
                        and price_schedule.get_rate_type_at_hour(available_from.hour) in [
                            TariffRateType.ON_PEAK,
                            TariffRateType.MID_PEAK,
                        ]
                    )

                    if cost < best_cost:
                        best_cost = cost
                        best_plan = ChargingPlan(
                            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
                            vehicle_id=vehicle.id,
                            vehicle_name=vehicle.name,
                            station_id=station.id,
                            station_name=station.name,
                            port_id=port.port_id,
                            start_time=candidate_start,
                            end_time=candidate_end,
                            start_soc=vehicle.battery_state.soc,
                            target_soc=target_soc,
                            energy_to_charge_kwh=energy_needed_kwh,
                            charging_power_kw=effective_power,
                            estimated_cost=cost,
                            tariff_type=rate_type,
                            average_rate_per_kwh=avg_rate,
                            shifted_from_peak=shifted_from_peak,
                        )

                curr += step

    if best_plan:
        tracker.book_port(
            best_plan.station_id,
            best_plan.port_id,
            best_plan.start_time,
            best_plan.end_time,
        )

    return best_plan
