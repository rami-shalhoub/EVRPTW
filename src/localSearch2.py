from copy import deepcopy

from src import config
from src.feasibility import BatteryError, InfeasibilityError, is_feasible
from src.helpers import calculate_battery_consumption, route_cost, shuffle, total_cost
from src.instances import Instance, Node
from src.solutionConstructor import insert_station


def best_move(route:list[Node], customer:Node , inst:Instance, route_length: int , ci:int = -1):
    """
    Find he best move for a customer 
    - check for route feasibility after a swap and try to insert a station if needed
    """
    best_route : list[Node] = deepcopy(route) 
    best_route_cost = route_cost(route)
    
    for i in range(1, route_length): # skip the depots
        # skip the original customer location (when performing the move in the same route)
        if ci == i :
            continue

        new_route : list[Node] = []
        temp_route = deepcopy(route)
        temp_route.remove(customer)    # remove the customer
        temp_route.insert(i, customer) # insert it is the new place
        try:
            is_feasible (inst, temp_route)
        except BatteryError:
            _, failed_node = calculate_battery_consumption(temp_route, inst) # find which node caused the battery to fail
            index = temp_route.index(failed_node)
            temp_route_b = insert_station(temp_route[:index], failed_node, inst)
            new_route = temp_route_b + temp_route[index+1:]

            # if still not feasible skip
            try:
                is_feasible(inst, new_route)
            except InfeasibilityError:
                continue
                
        except InfeasibilityError:
            continue
        else :
            new_route = deepcopy(temp_route)
        
        new_route_cost = route_cost(new_route)
        if new_route_cost < best_route_cost:
            best_route = deepcopy(new_route)
            best_route_cost = new_route_cost

    return best_route


def insert_failed_customers(routes:list[list[Node]], inst:Instance):
    # check if any routes are invalid (might happen in the construction faze)
    failed_customer: list[Node] = []
    for route in routes:
        if route[-1].type != 'd':
            customer = next(c for c in route if c.type == 'c')
            failed_customer.append(customer)
            
    # try to find a route to insert failed customers
    if failed_customer:
        for customer in failed_customer:
            for i in range(len(routes)):
                for _ in range(len(routes[i])):
                    new_route = best_move(routes[i], customer, inst, len(routes[i]))
                    if new_route is not routes[i]:
                        routes[i] = deepcopy(new_route)


def pertubate (routes:list[list[Node]], inst:Instance):
    for route in routes:
        customers = [n for n in route if n.type == "c"]
        shuffle(customers, inst)
        idx = 0
        for i, n in enumerate(route):
            if n.type == "c":
                route[i] = customers[idx]
                idx += 1

            
def remove_empty_route(routes:list[list[Node]]):
    for route in routes[:]:
        if next((c for c in route if c.type == "c"), None) is None:
            routes.remove(route)
    

def local_search(routes: list[list[Node]], inst: Instance) -> list[list[Node]]:
    best_routes : list[list[Node]] = deepcopy(routes)
    best_cost = float("inf")
    for _ in range(config.RUNS+5):
        insert_failed_customers(routes, inst)
        improved = True
        while improved:
            improved = False
            for i in range(len(routes)):
                for ci in range(len(routes[i])):
                    
                    # only relocate customers
                    if routes[i][ci].type in ("d", "f"):
                        continue

                    for j in range(len(routes)):
                        for cj in range(len(routes[j])):
                            
                            # skip stations as insertion points
                            if routes[j][cj].type in ("d", "f"):
                                continue
                                
                            customer = routes[i][ci]
                            
                            # same route move
                            if i == j:
                                # pass if it is the same customer
                                if ci == cj:
                                    continue

                                new_route = best_move(routes[j],customer, inst, len(routes[j]), ci)
                                if new_route is not  routes[i]:
                                    routes[i] = deepcopy(new_route)
                                    improved = True

                            else:
                                new_route_a = best_move(routes[j], customer, inst, len(routes[j]))

                                if new_route_a is not routes[j]:
                                    new_route_b = routes[i][:ci] + routes[i][ci + 1 :]
                                    old_cost = route_cost(routes[i]) + route_cost(routes[j])
                                    new_cost = route_cost(new_route_b) + route_cost(new_route_a)
    
                                    if new_cost < old_cost:
                                        routes[j] = deepcopy(new_route_a)
                                        routes[i] = deepcopy(new_route_b)
                                        improved = True




                                    # break out of all inner loops
                                    break
                        if improved:
                            break
                    if improved:
                        break
                if improved:
                    break
                    

        cost = total_cost(routes)
        if cost < best_cost:
            best_cost, best_routes = cost, deepcopy(routes)
            
        remove_empty_route(routes)
        # pertubate(routes, inst)

    return best_routes
