from dataclasses import dataclass
from enum import Enum
from typing import Set

from common.problem import EVRPTWInstance, NodeKind
from common.solution import Solution


class ValidationStatus(Enum):
    FEASIBLE = 0
    INFEASIBLE = 1

@dataclass
class Visit:
    node: int
    sum_distance_traveled_until_arrival: float
    sum_energy_consumed_until_arrival: float
    arrival: float
    waiting_time: float
    departure: float
    soc_on_arrival: float
    amount_recharged: float
    energy_feasible: bool
    time_feasible: bool

@dataclass
class ValidatedRoute:
    """Thoroughly checked route with details on constraint violations (not intended for heavy computation)"""
    status: ValidationStatus
    objective: float
    itinerary: list[Visit]
    distance: float
    start_end_depot_feasible: bool


@dataclass
class ValidatedSolution:
    """Thoroughly checked solution with details on constraint violations (not intended for heavy computation)"""
    status: ValidationStatus
    routes: list[ValidatedRoute]
    objective: float
    unassigned_customers: Set[int]


def validate_route(instance: EVRPTWInstance, route: list[int]) -> ValidatedRoute:
    itinerary = [
        Visit(
            node=route[0],
            sum_distance_traveled_until_arrival=0.0,
            sum_energy_consumed_until_arrival=0.0,
            arrival=0.0,
            waiting_time=0.0,
            departure=0.0,
            soc_on_arrival=instance.vehicle_energy_capacity,
            amount_recharged=0.0,
            energy_feasible=True,
            time_feasible=True,
        )
    ]
    for (u,v) in zip(route, route[1:]):
        distance = instance.distance(u, v)
        energy_consumption = instance.energy_consumption(u, v)
        travel_time = instance.travel_time(u, v)

        arrival = itinerary[-1].departure + travel_time
        waiting_time = min(0.0, instance.ready(v) - arrival)
        start_of_service = max(instance.ready(v), arrival)
        time_feasible = start_of_service <= instance.due(v)
        if not time_feasible:
            print(f"> time window constraint violated: arrival at node {instance.nodes[v].string_id} later than due time {instance.nodes[v].due} ({arrival} > {instance.nodes[v].due}) | route: {route}")
        departure = start_of_service + instance.service_time(v)

        soc_on_arrival = itinerary[-1].soc_on_arrival + itinerary[-1].amount_recharged - energy_consumption
        energy_feasible = soc_on_arrival > 0.0
        if not energy_feasible:
            print(f"> energy constraint violated: state of charge when arriving at node {instance.nodes[v].string_id} below zero. ({soc_on_arrival} < 0) | route: {route}" )

        amount_recharged = 0.0
        if instance.is_station(v):
            # recharge to full
            amount_recharged = instance.vehicle_energy_capacity - max(0.0, soc_on_arrival)

        itinerary.append(Visit(
            node=v,
            sum_distance_traveled_until_arrival=itinerary[-1].sum_distance_traveled_until_arrival + distance,
            sum_energy_consumed_until_arrival=itinerary[-1].sum_energy_consumed_until_arrival + energy_consumption,
            arrival=arrival,
            waiting_time=waiting_time,
            departure=departure,
            soc_on_arrival=soc_on_arrival,
            amount_recharged=amount_recharged,
            energy_feasible=energy_feasible,
            time_feasible=time_feasible,
        ))

    start_end_depot_feasible = route[0] == route[-1] and instance.is_depot(route[0])
    if not start_end_depot_feasible:
        print(f"route does not start and/or end in a depot / the same depot! (first: {instance.nodes[route[0]].string_id}, last: {instance.nodes[route[-1]].string_id} | route: {route}")

    return ValidatedRoute(
        status=ValidationStatus.INFEASIBLE if any(not v.time_feasible or not v.energy_feasible for v in itinerary) else ValidationStatus.FEASIBLE,
        itinerary=itinerary,
        objective=itinerary[-1].sum_distance_traveled_until_arrival,
        distance=itinerary[-1].sum_distance_traveled_until_arrival,
        start_end_depot_feasible=start_end_depot_feasible
    )

def compute_unassigned_customers(instance: EVRPTWInstance, routes: list[ValidatedRoute]) -> Set[int]:
    unserved_customers = set()
    for (idx, _) in enumerate(instance.nodes):
        if instance.nodes[idx].kind == NodeKind.Customer:
            unserved_customers.add(idx)
    for route in routes:
        for visit in route.itinerary:
            if instance.nodes[visit.node].kind == NodeKind.Customer:
                unserved_customers.remove(visit.node)
    for unserved_customer in unserved_customers:
        print(f"> customer {instance.nodes[unserved_customer].string_id} is not served by any route")
    return unserved_customers


def validate(instance: EVRPTWInstance, solution: Solution) -> ValidatedSolution:
    routes = [validate_route(instance, route) for route in solution.routes]

    unassigned_customers = compute_unassigned_customers(instance, routes)
    all_customers_served = len(unassigned_customers) == 0
    status = ValidationStatus.INFEASIBLE if not all_customers_served or any(route.status == ValidationStatus.INFEASIBLE for route in routes) else ValidationStatus.FEASIBLE

    return ValidatedSolution(
        status=status,
        routes=routes,
        objective=sum(route.objective for route in routes),
        unassigned_customers=unassigned_customers,
    )
