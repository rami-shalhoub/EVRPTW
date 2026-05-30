from copy import deepcopy

from . import config
from .feasibility import BatteryError, InfeasibilityError, is_feasible
from .helpers import find_best_stations, route_cost, shuffle, sweep_sort, total_cost, calculate_battery_consumption
from .instances import Instance, Node


def insert_station (route:list[Node], customer:Node, inst:Instance, last_resort:bool = False):
    """
    Station insertion \n
    - insert a station between the last customer in the route and `customer` 
    - to increase the chances of finding a station we try the best n stations until one fits, otherwise we take the fist best station
    """
    new_route :list[Node] = []
    battery, _ = calculate_battery_consumption(route, inst)
    stations = find_best_stations(route[-1], customer, inst, battery, config.STATIONS)
    if len(stations) > 0:
        best, best_cost = stations[0], float("inf")
        temp_route : list[Node] = []
        for s in stations:
            temp_route = route + [s] + [customer]
            cost = route_cost(temp_route)
            if cost < best_cost:
                best_cost, best = cost, s

        # * skip feasibility check if the station is inserted in the last resort fase
        if not last_resort:
            try:
                is_feasible(inst, route + [best] + [customer])
            except InfeasibilityError :
                pass
            else:
                route.append(best)
                route.append(customer)
        else:
            route.append(best)
            route.append(customer)
    new_route = deepcopy(route)
    return new_route

def route_constructor(unvisited: list[Node], inst: Instance):
    """
    (Greedy constructor insert) the customers from the ordered list if they are feasible
    and Insert a charging station if needed \n
    Make sure that each route starts and end with the depot \n
    """
    route: list[Node] = [inst.depot]  # starts the from the depot
    for i in range(len(unvisited)):
        try:
            is_feasible(inst, route + [unvisited[i]])
        except BatteryError:
            new_route = insert_station(route[:], unvisited[i], inst)
            route = deepcopy(new_route)
        except InfeasibilityError:
            continue  # skip this move entirely
        else:
            route.append(unvisited[i]) # add the customer to the rout
        

    # ----------------------------------------------------
    #INFO             Return to depot
    # * check if rout can end with the depot
    # ----------------------------------------------------
    try:
        is_feasible(inst, route + [inst.depot])
    except InfeasibilityError:
        pass
    else:
        route.append(inst.depot)
    finally:
        # remove visited customers
        for r in route:
            if unvisited.count(r) == 1:
                unvisited.pop(unvisited.index(r))
        return route

def last_resort(routes:list[list[Node]], failed_customers:list[Node], inst:Instance):
    """
    Last resort for unvisited customersa \n
    if the iteration finished, and there still unvisited customers \n
    then construct the shortest possible route \n
    """
    for f in failed_customers:
        try:
            is_feasible(inst, [inst.depot] + [f] + [inst.depot])
        except BatteryError:
            route = insert_station([inst.depot], f, inst, True)
            try :
                is_feasible(inst, route + [inst.depot])
            except BatteryError:
                # * if [D, S, f, D] failes try to go to a station befor returning to the depot
                new_route = insert_station(route, inst.depot, inst, True)
                # if new_route[-1] != inst.depot:
                #    # * if it failes to retun to depot show me
                #     try:
                #         is_feasible(inst, new_route + [inst.depot])
                #     except InfeasibilityError as iE:
                #         print(f"custoemr {f.id} couldn't reach the depot because \n {iE}")
                # else:
                #     routes.append(new_route)
                
                routes.append(new_route)
            else:
                routes.append(route + [inst.depot])
        else:
            routes.append([inst.depot] + [f] + [inst.depot])
    
def greedy_construction(inst: Instance):
    """
    Construct a solution using ***Sweeping algorithm*** and ***Greedy constructor*** \n
    
    :return routes: The solution is a list of routes
    :rtype: list[list[Node]]
    """
    best_routes: list[list[Node]] = list()
    best_cost:float = float("inf")
    for t in range(config.RUNS):
        routes: list[list[Node]] = list()
        failed_customers: list[Node] = list()
        unvisited:list[Node] = sweep_sort(inst.customers[:], inst)
        i = config.ITERATIONS
        while len(unvisited) != 0:
            route = route_constructor(unvisited, inst)
            if route[-1].type != 'd':
                failed_customers += [r for r in route if r.type == 'c'] # remove the stations and the depot
            else:
                routes.append(route)      
            shuffle(unvisited, inst)
            #--------------------------------------------------------------
            #INFO               Failed customers iterations                         
            # * after going through the whole unvisited customers, if any 
            # * customers couldn't be served, try inserting them after
            # * reshuffling or reshuffling and reversing the list 
            #--------------------------------------------------------------
            if len(unvisited) == 0 and len(failed_customers) > 0:
                if i == 0:
                    last_resort(routes, failed_customers, inst)
                    break
                    
                i -= 1
                unvisited = failed_customers[:]
                shuffle(unvisited, inst)
                failed_customers.clear()

        cost = total_cost(routes)
        if cost < best_cost:
            best_cost, best_routes = cost, deepcopy(routes)

    
    return best_routes