import math
import os
import random
import pandas as pd
from .instances import Instance, Node

#========================================================================
#===                 General helper function                          ===
#========================================================================
def dist(a: Node, b: Node):
    """Euclidean distance between two nodes"""
    return math.hypot(a.x - b.x, a.y - b.y)


def travel_time(a: Node, b: Node, v: float):
    """Time to travel from a to b at velocity v"""
    return dist(a, b) / v


def consumed_energy(a: Node, b: Node, r: float):
    """Battery consumed travelling from a to b"""
    return r * dist(a, b)

def update_battery(a:Node, b:Node, r:float, current_battry:float):
    """Update the battery charge after passing a distance"""
    return current_battry - consumed_energy(a,b,r)

def calculate_battery_consumption (route:list[Node], inst:Instance):
    """
    Calculate the battery consumption throughout the route
    if the battery ends at a note it return is node
    """
    battery = inst.Q
    for i in range(len(route) - 1):
        battery -= consumed_energy(route[i], route[i+1], inst.r)
        if route[i+1].type == "f":
            battery = inst.Q
        if battery < 0:
            return battery, route[i+1]
    return battery, inst.depot

def charge_time(current_battery: float, Q: float, g: float):
    """Time to recharge from current_battery to full Q"""
    return g * (Q - current_battery)

def route_cost(route: list[Node]) -> float:
    """sum of distances along a route"""
    return sum(dist(route[i], route[i + 1]) for i in range(len(route) - 1))

def total_cost(routes:list[list[Node]]):
    cost:float = 0.0
    for route in routes:
        cost += route_cost(route)
    return round(cost, 3)

def print_routes(routes:list[list[Node]], msg: str = ""):
    print(msg)
    print(f"total cost: {total_cost(routes)}")
    for route in routes:
       print(", ".join(node.id for node in route))

def export_to_txt(routes: list[list[Node]], name: str, total_cost:float):
    # Ensure the directory exists
    file_path = f"./solution/{name}_solution.txt"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w') as file:
        file.write(f"# solution for {name}\n")
        file.write(f"{total_cost}\n")
        for route in routes:
            file.write(", ".join(node.id for node in route) + "\n")
            
def export_to_csv(results:list[tuple[str, float, float, float]], file_name: str ):
    data = pd.DataFrame(results, columns = ["instance", "best", "avg", "avg.time(s)"])
    data.to_csv(f"{file_name}.csv", index = False, float_format="%.2f")
   
#========================================================================
#===                Greedy algorithm helper functions                ===
#========================================================================
def sweep_angle(depot: Node, node: Node, ref_angle: float):
    """
    Polar angle of node relative to depot, offset by ref_angle.
    Result is in [0, 2π].
    """
    cust_angle = math.atan2(node.y - depot.y, node.x - depot.x)
    return (cust_angle - ref_angle) % (2 * math.pi)

def find_best_stations(cur_customer: Node, next_customer: Node, inst: Instance, current_battery:float, iterations: int):
    """Find the closest charging station between the current and next customer"""
    best_stations: list[Node] = list()
    stations = inst.stations[:]
    for _ in range(iterations):
        best, best_detour = None, float("inf")
        for s in stations:
            # can reach the station and the next customer after full charge
            if (inst.r * dist(cur_customer, s) <= current_battery 
                and  inst.r * dist(s, next_customer) <= inst.Q):  
                detour = dist(cur_customer, s) + dist(s, next_customer) - dist(cur_customer, next_customer)
                if detour < best_detour:
                    best_detour, best = detour, s
        if best is not None:
            best_stations.append(stations.pop(stations.index(best)))
    return best_stations

def sweep_sort (unvisited: list[Node], inst:Instance):
    """(Sweep heuristic) sort customers by polar angle using a random reference point"""
    ref_angle: float = random.uniform(0, 2 * math.pi) 
    unvisited.sort(key=lambda n: sweep_angle(inst.depot, n, ref_angle))
    return unvisited

def order_customers_by_distance(unvisited: list[Node]) -> list[Node]:
    """Order customers by distance from the first customer"""
    if not unvisited:
        return []
    return [unvisited[0]] + sorted(unvisited[1:], key=lambda c: dist(unvisited[0], c))
    
def shuffle(customers: list[Node], inst: Instance):
    luck = random.randint(1, 4)
    match luck:
        case 1:
            customers = sweep_sort(customers, inst)
        case 2:
            customers = sweep_sort(customers, inst)
            customers.reverse()
        case 3:
            customers = sweep_sort(customers, inst)
            mid = len(customers) // 2
            customers[:] = customers[mid:] + customers[:mid]
        case 4:
            customers = sweep_sort(customers, inst)
            customers[:] = order_customers_by_distance(customers)
