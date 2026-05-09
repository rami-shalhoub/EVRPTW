import math
import random

from .feasibility import is_feasible
from .helpers import find_best_station, sweep_angle, update_battery
from .instances import Instance, Node


def route_constructor(unvisited: list[Node], inst: Instance):
    """
    Greedy constructor insert the customers from the ordered list if they are feasible
    and Insert a charging station if needed
    Make sure that each route starts and end with the depot \n
    """
    route: list[Node] = [inst.depot]  # starts the from the depot
    battery = inst.Q  # start with a full battery
    for i in range(len(unvisited)):
        # --------------------------------------------------------------
        #                         Insert a customer
        # check if it is feasible to insert a customer, otherwise
        # check if it is feasible to go to a charging station before
        # --------------------------------------------------------------
        if is_feasible(route + [unvisited[i]], inst):
            battery = update_battery(route[::-1][0], unvisited[i], inst.r, battery)
            route.append(unvisited[i])  # add the customer to the rout
        else:
            station = find_best_station(route[::-1][0], unvisited[i], inst, battery)
            if station is not None and is_feasible(
                route + [station] + [unvisited[i]], inst
            ):
                battery = update_battery(
                    station, unvisited[i], inst.r, inst.Q
                )  # the battery consumption from the station to the customer
                route.append(station)
                route.append(unvisited[i])

    # ----------------------------------------------------
    #                 Return to depot
    # check if rout can end with the depot, if not
    # exit the function ad the current solution is not possible
    # ----------------------------------------------------
    if is_feasible(route + [inst.depot], inst):
        route.append(inst.depot)
        # remove visited customers
        for r in route:
            if unvisited.count(r) > 0:
                unvisited.pop(unvisited.index(r))

        return route
    else:
        return route 

def shuffle (unvisited: list[Node], inst:Instance):
    """sort customers by polar angle using a random reference point (Sweep heuristic)"""
    ref_angle: float = random.uniform(0, 2 * math.pi) 
    unvisited.sort(key=lambda n: sweep_angle(inst.depot, n, ref_angle))
    return unvisited

def greedy_construction(inst: Instance):
    """
    Construct a solution using ***Sweeping algorithm*** and ***Greedy constructor*** \n
    The solution is a list of routes \n
    
    """
    routes: list[list[Node]] = list()
    unvisited:list[Node] = shuffle(inst.customers[:], inst)
    print(f"total customers {len(unvisited)}")
    while len(unvisited) != 0:
        route = route_constructor(unvisited, inst)
        if route is None:
            unvisited = shuffle(unvisited, inst)
            continue
        print(f"remaining customers {len(unvisited)}")
        routes.append(route)
    return routes