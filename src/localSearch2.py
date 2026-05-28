from copy import deepcopy

from src.feasibility import is_feasible
from src.helpers import route_cost, shuffle, total_cost
from src.instances import Instance, Node


def best_swap(route:list[Node], customer:Node , cj:int, inst:Instance, steps: int ):
    new_route : list[Node] = []
    temp_route = route[:]
    temp_route.remove(customer)
    for step in range(0, steps):
        temp_route.insert(cj+ step, customer)
        if is_feasible (inst, temp_route):
            if route_cost(temp_route) < route_cost(route):
                new_route = temp_route[:]
        temp_route.remove(customer)
    if not new_route:
        return route
    else:
        return new_route

def best_move(route_b:list[Node], customer: Node, index:int, inst:Instance):
    new_route_b :list[Node] = []
    for step in range(0,index):
        temp_route = route_b[:]
        temp_route.insert(step, customer)
        if is_feasible(inst, temp_route):
            if route_cost(temp_route) < route_cost (route_b):
                new_route_b = temp_route[:]

    if not new_route_b:
        return route_b
    else:
        return new_route_b

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
        if len(route) == 2:
            routes.remove(route)


    

def local_search(routes: list[list[Node]], inst: Instance, tries:int) -> list[list[Node]]:
    best_routes : list[list[Node]] = routes [:]
    best_cost = float("inf")
    for _ in range(tries):
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

                            # if the same route perform a swap
                            if i == j:
                                # pass if it is the same customer
                                if ci == cj:
                                    continue

                                new_route = best_swap(routes[i],routes[i][ci] , cj, inst, len(routes[j])- cj)
                                if new_route is not  routes[i]:
                                    routes[i] = new_route[:]
                                    improved = True

                            else:
                                customer = routes[i][ci]
                                new_route_b = best_move(routes[j], customer, len(routes[j]), inst)

                                if new_route_b is not routes[j]:
                                    new_route_a = routes[i][:ci] + routes[i][ci + 1 :]
                                    
                                    old_cost = route_cost(routes[i]) + route_cost(routes[j])
                                    new_cost = route_cost(new_route_a) + route_cost(new_route_b)
    
                                    if new_cost < old_cost:
                                        routes[i] = new_route_a [:]
                                        routes[j] = new_route_b [:]
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
        pertubate(routes, inst)

    return best_routes
