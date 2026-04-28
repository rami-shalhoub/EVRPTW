import math
import random
from .helpers import  sweep_angle, find_best_station, update_battery
from .feasibility import is_feasible
from .instances import Instance, Node

class RoutException(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)
        


#------------------------------------------------------------------------
#INFO                          More Testing                              
# * the function is almost readybut it needs more testing 
# * more testing after adding the last part to add the depot to the end
# * possible improvement: regenerate the ref_angle to get a new solution
#------------------------------------------------------------------------

def greedy_construction(inst: Instance):
    # ----------------------------------------------------
    #                   Sorting
    # sort customers by polar angle (Sweep heuristic)
    # ----------------------------------------------------
    ref_angle: float = random.uniform(0, 2 * math.pi)
    unvisited: list = inst.customers
    unvisited.sort(key=lambda n: sweep_angle(inst.depot, n, ref_angle))

    routes:list[list[Node]] = list()
    battery = inst.Q
    while len(unvisited) != 0 :
        route:list[Node] = [inst.depot]
        for i in range(len(unvisited)):
            if is_feasible(route + [unvisited[i]], inst):
                battery = update_battery(route[::-1][0], unvisited[i], inst.r, battery)
                route.append(unvisited[i])   # add the customer to the rout
                # unvisited.pop(i)
            else :
                station = find_best_station(route[::-1][0], unvisited[i], inst, battery)
                if station is not None and is_feasible(route+[station]+ [unvisited[i]],inst):
                        battery = update_battery(station, unvisited[i], inst.r, inst.Q) # the battery consumption from the station to the customer
                        route.append(station)
                        route.append(unvisited[i])
        
        # add the depot at the end of the rout                
        if battery > 0 and (route+[inst.depot], inst):
            route.append(inst.depot)
            routes.append(route)
            # remove visited customers
            for r in route:
                if unvisited.count(r) > 0:
                    unvisited.pop(unvisited.index(r))
        else:
            raise RoutException("can't return to depot")
                

    return routes
