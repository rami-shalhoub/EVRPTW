from src.feasibility import is_feasible
from src.helpers import route_cost
from src.instances import Instance, Node


def local_search(routes: list[list[Node]], inst: Instance) -> list[list[Node]]:
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
                        # skip trivial same-position moves
                        if i == j:
                            continue
                        # skip stations as insertion points
                        if routes[j][cj].type in ("d", "f"):
                            continue

                        customer = routes[i][ci]

                        new_route_a = routes[i][:ci] + routes[i][ci + 1 :]
                        new_route_b = routes[j][:cj] + [customer] + routes[j][cj:]

                        if not is_feasible(inst,new_route_a) or not is_feasible(inst, new_route_b):
                            continue

                        old_cost = route_cost(routes[i]) + route_cost(routes[j])
                        new_cost = route_cost(new_route_a) + route_cost(new_route_b)

                        if new_cost < old_cost:
                            # write back using indices — this actually updates routes
                            # remove empty route [depot, depot]
                            if len(new_route_a) == 2:
                                routes.pop(i)
                            else:
                                routes[i] = new_route_a
                            routes[j] = new_route_b
                            improved = True


                            # break out of all inner loops
                            break
                    if improved:
                        break
                if improved:
                    break
            if improved:
                break

    return routes
