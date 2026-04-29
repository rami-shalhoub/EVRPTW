import math
import random
from .helpers import  sweep_angle, find_best_station, update_battery
from .feasibility import is_feasible
from .instances import Instance, Node

def greedy_construction(inst: Instance):
    """
    Construct a solution using ***Sweeping algorithm*** and ***Greedy constructor*** \n
    The solution is a list of routes \n
    • Make sure that each route starts and end with the depot \n
    
    • The Sweeping algorithm uses a random reference point to order a list of customers \n
    • The Greedy constructor insert the customers from the ordered list if they are feasible \n
        · Insert a charging station if needed
    """
    # ----------------------------------------------------
    #                   Sorting
    # sort customers by polar angle (Sweep heuristic)
    # ----------------------------------------------------
    ref_angle: float = random.uniform(0, 2 * math.pi)
    unvisited: list[Node] = inst.customers[:]
    unvisited.sort(key=lambda n: sweep_angle(inst.depot, n, ref_angle))

    routes:list[list[Node]] = list()
    while len(unvisited) != 0 :
        route:list[Node] = [inst.depot]     # starts the from the depot
        battery = inst.Q             # start with a full battery
        for i in range(len(unvisited)):
            #--------------------------------------------------------------
            #                         Insert a customer                         
            # check if it is feasible to insert a customer, otherwise
            # check if it is feasible to go to a charging station before
            #--------------------------------------------------------------
            if is_feasible(route + [unvisited[i]], inst):
                battery = update_battery(route[::-1][0], unvisited[i], inst.r, battery)
                route.append(unvisited[i])   # add the customer to the rout
            else :
                station = find_best_station(route[::-1][0], unvisited[i], inst, battery)
                if station is not None and is_feasible(route+[station]+ [unvisited[i]],inst):
                        battery = update_battery(station, unvisited[i], inst.r, inst.Q) # the battery consumption from the station to the customer
                        route.append(station)
                        route.append(unvisited[i])
        
        #----------------------------------------------------
        #                 Return to depot                    
        # check if rout can end with the depot, if not
        # exit the function ad the current solution is not possible
        #----------------------------------------------------               
        if is_feasible(route+[inst.depot], inst):
            route.append(inst.depot)
            routes.append(route)
            # remove visited customers
            for r in route:
                if unvisited.count(r) > 0:
                    unvisited.pop(unvisited.index(r))
        else:
            return 
                

    return routes
