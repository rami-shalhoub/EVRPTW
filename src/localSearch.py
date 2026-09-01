import time
from copy import deepcopy

from src import config
from src.feasibility import BatteryError, InfeasibilityError, is_feasible
from src.helpers import route_cost, total_cost
from src.instances import Instance, Node
from src.solutionConstructor import insert_station, last_resort


def _repair(candidate: list[Node], failed_index: int, failed_node: Node, inst: Instance) -> list[Node] | None:
    """
    Splice charging stations into `candidate` until it is feasible \n
    - returns the repaired route, or None when no station placement works
    """
    working = candidate
    while True:
        patched = insert_station(working[:failed_index], failed_node, inst)
        if len(patched) == failed_index:
            return None
        working = patched + working[failed_index + 1:]
        try:
            is_feasible(inst, working)
        except BatteryError as e:
            failed_index, failed_node = e.edge_index + 1, e.next
        except InfeasibilityError:
            return None
        else:
            return working


def best_move(route: list[Node], customer: Node, inst: Instance, ci: int = -1):
    """
    Find the best move for a customer
    - check for route feasibility after the move and try to insert a station if needed
    - stations are stripped upfront and re-inserted by the repair step
    - same-route (ci != -1): only returns routes cheaper than the current one
    - cross-route (ci == -1): returns the cheapest feasible insertion
    Returns the passed-in `route` object when nothing better is feasible
    """
    best_route = None
    # same-route: compare against original cost; cross-route: accept any feasible
    best_route_cost = route_cost(route) if ci != -1 else float("inf")

    # station-free skeleton: depots + customers only, customer lifted out on same-route moves
    base = [n for n in route if n.type != "f"]
    if ci != -1:
        base.remove(customer)

    # the customer's original slot expressed in `base` indices (stations shift positions)
    skip = sum(1 for n in route[:ci] if n.type != "f") if ci != -1 else -1

    for i in range(1, len(base)):  # skip the depots
        if i == skip:
            continue

        candidate = base[:i] + [customer] + base[i:]
        try:
            is_feasible(inst, candidate)
        except BatteryError as e:
            candidate = _repair(candidate, e.edge_index + 1, e.next, inst)
            if candidate is None:
                continue
        except InfeasibilityError:
            continue

        new_route_cost = route_cost(candidate)
        if new_route_cost < best_route_cost:
            best_route, best_route_cost = candidate, new_route_cost

    return best_route if best_route is not None else route


def route_sig(route: list[Node]) -> tuple:
    """Hashable fingerprint of a route, used as cache key"""
    return tuple(n.id for n in route)


def solo_route(customer: Node, inst: Instance) -> list[Node] | None:
    """
    Build a standalone route for a single customer using the constructor's
    last-resort escalation (depot -> customer -> depot, stations added as needed) \n
    returns None when the customer cannot be served alone
    """
    tmp: list[list[Node]] = []
    last_resort(tmp, [customer], inst)
    if tmp and any(n is customer for n in tmp[0]):
        return tmp[0]
    return None


def eject_costly_customers(routes: list[list[Node]], inst: Instance, k: int) -> int:
    """
    Move the top-k most costly customers into their own solo routes \n
    - a customer is costly when removing it shrinks its route's cost (removal savings)
    - the split only happens when the solo route costs less than the savings,
      i.e. the move is strictly net-positive
    - returns the number of customers actually ejected
    """
    if k <= 0:
        return 0

    savings: list[tuple[float, int, Node]] = []
    for ri, route in enumerate(routes):
        for ni, node in enumerate(route):
            if node.type != "c":
                continue
            rest = route[:ni] + route[ni + 1:]
            gain = route_cost(route) - route_cost(rest)
            if gain > 0:
                savings.append((gain, ri, node))
    savings.sort(key=lambda s: s[0], reverse=True)

    ejected = 0
    for _, ri, node in savings[:k]:
        route = routes[ri]
        idx = next((p for p, x in enumerate(route) if x is node), None)
        if idx is None:
            continue
        solo = solo_route(node, inst)
        if solo is None:
            continue
        rest = route[:idx] + route[idx + 1:]
        if route_cost(route) - route_cost(rest) <= route_cost(solo):
            continue
        routes[ri] = rest
        routes.append(solo)
        ejected += 1
    return ejected


def remove_empty_route(routes: list[list[Node]]):
    for route in routes[:]:
        if next((c for c in route if c.type == "c"), None) is None:
            routes.remove(route)


def local_search(routes: list[list[Node]], inst: Instance) -> tuple[list[list[Node]], list[float], list[float], list[dict], list[list[dict]]]:
    best_routes = None
    best_cost = float("inf")
    cost_history: list[float] = []
    time_history: list[float] = []
    run_metadata: list[dict] = []
    convergence_data: list[list[dict]] = []
    for run in range(config.RUNS):
        start = time.perf_counter()
        ejected_count = 0
        # diversify between chunks: split off the costliest customers (run 0 untouched)
        if run > 0:
            ejected_count = eject_costly_customers(routes, inst, config.EJECT_K)

        # memoized best_move results; keys embed the target route's content,
        # so stale entries become unreachable as soon as the route changes
        cache: dict[tuple, list[Node] | None] = {}
        improved = True
        improvements = 0
        run_conv: list[dict] = []
        while improved and improvements < config.MAX_LOCAL_IMPROVEMENTS:
            remove_empty_route(routes)
            improved = False
            loads = [sum(n.demand for n in r if n.type == "c") for r in routes]
            for i in range(len(routes)):
                for ci in range(len(routes[i])):

                    # only relocate customers
                    if routes[i][ci].type in ("d", "f"):
                        continue

                    customer = routes[i][ci]

                    for j in range(len(routes)):
                        if i == j:
                            key = (customer.id, route_sig(routes[i]))
                            if key in cache:
                                res = cache[key]
                            else:
                                moved = best_move(routes[i], customer, inst, ci)
                                res = moved if moved is not routes[i] else None
                                cache[key] = res
                            if res is not None:
                                routes[i] = res
                                improved = True
                                improvements += 1
                        else:
                            # cross-route: skip if target lacks capacity
                            if loads[j] + customer.demand > inst.C:
                                continue

                            key = (customer.id, route_sig(routes[j]))
                            if key in cache:
                                res = cache[key]
                            else:
                                moved = best_move(routes[j], customer, inst)
                                res = moved if moved is not routes[j] else None
                                cache[key] = res
                            if res is None:
                                continue

                            new_route_b = routes[i][:ci] + routes[i][ci + 1:]
                            old_cost = route_cost(routes[i]) + route_cost(routes[j])
                            new_cost = route_cost(new_route_b) + route_cost(res)

                            if new_cost < old_cost:
                                routes[j] = res
                                routes[i] = new_route_b
                                improved = True
                                improvements += 1

                        if improved:
                            break
                    if improved:
                        break
                if improved:
                    break

            routes_count = len(routes)
            customers_served = sum(1 for r in routes for n in r if n.type == "c")
            run_conv.append({
                "iteration": improvements,
                "cost": total_cost(routes),
                "routes_count": routes_count,
                "customers_served": customers_served,
            })

        cost = total_cost(routes)
        elapsed = time.perf_counter() - start
        cost_history.append(cost)
        time_history.append(elapsed)
        run_metadata.append({
            "improvements_made": improvements,
            "ejected_customers": ejected_count,
            "converged": improvements >= config.MAX_LOCAL_IMPROVEMENTS,
        })
        convergence_data.append(run_conv)
        if cost < best_cost:
            best_cost, best_routes = cost, deepcopy(routes)

        remove_empty_route(routes)

    best_routes = best_routes if best_routes is not None else routes
    return best_routes, cost_history, time_history, run_metadata, convergence_data
