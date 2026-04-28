import math

from .instances import Instance, Node


def dist(a: Node, b: Node):
    """Euclidean distance between two nodes"""
    return math.hypot(a.x - b.x, a.y - b.y)


def travel_time(a: Node, b: Node, v: float):
    """Time to travel from a to b at velocity v"""
    return dist(a, b) / v


def consumed_energy(a: Node, b: Node, r: float):
    """Battery consumed travelling from a to b"""
    return r * dist(a, b)


def charge_time(current_battery: float, Q: float, g: float):
    """Time to recharge from current_battery to full Q"""
    return g * (Q - current_battery)


def sweep_angle(depot: Node, node: Node, ref_angle: float):
    """
    Polar angle of node relative to depot, offset by ref_angle.
    Result is in [0, 2π].
    """
    cust_angle = math.atan2(node.y - depot.y, node.x - depot.x)
    return (cust_angle - ref_angle) % (2 * math.pi)


def update_battery(a:Node, b:Node, r:float, current_battry:float):
    return current_battry - consumed_energy(a,b,r)

def find_best_station(cur_customer: Node, nxt_customer: Node, inst: Instance, current_battery:float):
    """Find the closest charging station between the current and next customer"""
    best, best_detour = None, float("inf")
    for s in inst.stations:
        if inst.r * dist(cur_customer, s) <= current_battery:  # can reach s
            if inst.r * dist(s, nxt_customer) <= inst.Q:  # can reach v after full charge
                detour = (
                    dist(cur_customer, s)
                    + dist(s, nxt_customer)
                    - dist(cur_customer, nxt_customer)
                )
                if detour < best_detour:
                    best_detour, best = detour, s
    return best
