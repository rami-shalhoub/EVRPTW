from copy import deepcopy

from src import config
from src.feasibility import BatteryError, InfeasibilityError, is_feasible
from src.helpers import route_cost, shuffle, total_cost
from src.instances import Instance, Node
from src.solutionConstructor import insert_station


def best_move(route:list[Node], customer:Node , inst:Instance, route_length: int , ci:int = -1):
    """
    Find he best move for a customer 
    - check for route feasibility after a swap and try to insert a station if needed
    """
    best_route = None
    # same-route: compare against original cost; cross-route: accept any feasible
    best_route_cost = route_cost(route) if ci != -1 else float("inf")
    
    temp_route = deepcopy(route)
    if ci != -1:
        temp_route.remove(customer)    # remove the customer (same-route move)
        
    for i in range(1, len(temp_route)): # skip the depots
        new_route = None
        if ci != -1:
            # skip the original customer location (when performing the move in the same route)
            if ci == i :
                continue
            
        try:
            temp_route.insert(i, customer)
            is_feasible(inst, temp_route)
        except BatteryError as e:
            failed_index = e.edge_index + 1
            failes_node = e.next
            handled = False
            while not handled:
                temp_route_b = insert_station(temp_route[:failed_index], failes_node, inst)
                if len(temp_route_b) == failed_index:
                    temp_route.remove(customer)
                    break
                new_route = temp_route_b + temp_route[failed_index+1:]
                try:
                    is_feasible(inst, new_route)
                except BatteryError as e:
                    failed_index = e.edge_index + 1
                    failes_node = e.next
                except InfeasibilityError:
                    temp_route.remove(customer)
                    break
                else:
                    handled = True
            if not handled:
                continue
        except InfeasibilityError:
            temp_route.remove(customer)
            continue
        else:
            new_route = deepcopy(temp_route)

        if new_route is not None:
            new_route_cost = route_cost(new_route)
            if new_route_cost < best_route_cost:
                best_route = deepcopy(new_route)
                best_route_cost = new_route_cost
            
        if customer in temp_route:    
            temp_route.remove(customer)

    return best_route if best_route is not None else route



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
    

def local_search(routes: list[list[Node]], inst: Instance) -> tuple[list[list[Node]], list[float]]:
    best_routes = routes
    best_cost = float("inf")
    history: list[float] = []
    for _ in range(config.RUNS):
        improved = True
        improvements = 0
        while improved and improvements < config.MAX_LOCAL_IMPROVEMENTS:
            remove_empty_route(routes)
            improved = False
            for i in range(len(routes)):
                for ci in range(len(routes[i])):
                    
                    # only relocate customers
                    if routes[i][ci].type in ("d", "f"):
                        continue

                    customer = routes[i][ci]
                    
                    for j in range(len(routes)):
                        # cross-route: skip if target lacks capacity
                        if i != j:
                            route_load = sum(n.demand for n in routes[j] if n.type == "c")
                            if route_load + customer.demand > inst.C:
                                continue
                        
                        for cj in range(len(routes[j])):
                            if routes[j][cj].type in ("d", "f"):
                                continue

                            if i == j:
                                if ci == cj:
                                    continue
                                new_route = best_move(routes[j], customer, inst, len(routes[j]), ci)
                                if new_route is not routes[i]:
                                    routes[i] = deepcopy(new_route)
                                    improved = True
                                    improvements += 1
                                    break
                            else:
                                new_route_a = best_move(routes[j], customer, inst, len(routes[j]))

                                if new_route_a is not routes[j]:
                                    new_route_b = routes[i][:ci] + routes[i][ci + 1:]
                                    old_cost = route_cost(routes[i]) + route_cost(routes[j])
                                    new_cost = route_cost(new_route_b) + route_cost(new_route_a)

                                    if new_cost < old_cost:
                                        routes[j] = deepcopy(new_route_a)
                                        routes[i] = deepcopy(new_route_b)
                                        improved = True
                                        improvements += 1

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
            history.append(best_cost)
            
        remove_empty_route(routes)
        pertubate(routes, inst)

    best_routes = best_routes if best_routes is not None else routes
    return best_routes, history
