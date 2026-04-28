from .helpers import charge_time, consumed_energy, travel_time
from .instances import Instance, Node


def is_feasible(route: list[Node], inst: Instance) -> bool:
    """
    Simulate a route and check all EVRPTW constraints.
    route must start and end with the depot: [depot, ..., depot]
    Returns True if feasible, False otherwise.
    """
    battery = inst.Q  # start fully charged
    load = 0.0  # start empty
    time = 0.0  # start at time 0

    for i in range(len(route) - 1):
        current:Node = route[i]
        next:Node = route[i + 1]

        #===============Travel along arc current → next ==============
        battery -= consumed_energy(current, next, inst.r)
        time += travel_time(current, next, inst.v)

        if battery < 0:
            return False  # ran out of battery mid-arc

        #===============Arrive at next: time window==============
        start = max(time, next.ready)  # wait if arrived early

        if start > next.due:
            return False  # arrived too late

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
                return False  # vehicle overloaded

    return True
