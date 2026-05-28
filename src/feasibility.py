from .helpers import charge_time, consumed_energy, travel_time
from .instances import Instance, Node


class InfeasibilityError(Exception):
    """Base exception for all infeasibility violations."""

    def __init__(self, message: str, route_index: int = -1, edge_index: int = -1):
        self.route_index = route_index
        self.edge_index = edge_index
        super().__init__(message)


class BatteryError(InfeasibilityError):
    """Raised when battery runs out mid-arc."""

    def __init__(
        self,
        current: Node,
        next: Node,
        battery: float,
        route_index: int = -1,
        edge_index: int = -1,
    ):
        self.current = current
        self.next = next
        self.battery = battery
        super().__init__(
            f"Battery exhausted: {current.id} → {next.id} "
            f"(battery {battery:.2f} < 0)",
            route_index,
            edge_index,
        )


class TimeWindowError(InfeasibilityError):
    """Raised when arrival exceeds the node's due time."""

    def __init__(self, node: Node, start: float, route_index: int = -1, edge_index: int = -1):
        self.node = node
        self.start = start
        super().__init__(
            f"Time window violated at {node.id}: "
            f"arrived {start:.2f} > due {node.due}",
            route_index,
            edge_index,
        )


class CapacityError(InfeasibilityError):
    """Raised when load exceeds vehicle capacity."""

    def __init__(
        self,
        node: Node,
        load: float,
        capacity: float,
        route_index: int = -1,
        edge_index: int = -1,
    ):
        self.node = node
        self.load = load
        self.capacity = capacity
        super().__init__(
            f"Capacity exceeded at {node.id}: "
            f"load {load:.2f} > capacity {capacity:.2f}",
            route_index,
            edge_index,
        )


def is_feasible(inst: Instance, *routes) -> None:
    """
    Simulate a route and check all EVRPTW constraints.
    Returns None if feasible, raises InfeasibilityError otherwise.
    """
    for ri, route in enumerate(routes):
        battery = inst.Q  # start fully charged
        load = 0.0  # start empty
        time = 0.0  # start at time 0

        for i in range(len(route) - 1):
            current: Node = route[i]
            next: Node = route[i + 1]

            #===============Battery charge from current node → next node ==============
            battery -= consumed_energy(current, next, inst.r)
            if battery < 0:
                raise BatteryError(current, next, battery, ri, i)

            #===============Arrive at next: time window==============
            time += travel_time(current, next, inst.v)
            start = max(time, next.ready)  # wait if arrived early

            if start > next.due:
                raise TimeWindowError(next, start, ri, i)

            #===============Node-type-specific handling==============
            if next.type == "f":
                # charging station: recharge to full, no demand
                charging_time = charge_time(battery, inst.Q, inst.g)
                time = start + charging_time
                battery = inst.Q

            else:
                # customer or depot: accrue service time and demand
                time = start + next.service
                load += next.demand

                if load > inst.C:
                    raise CapacityError(next, load, inst.C, ri, i)
