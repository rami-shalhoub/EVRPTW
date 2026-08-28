import random
import time
from copy import deepcopy

from src import config
from src.feasibility import InfeasibilityError, is_feasible
from src.helpers import customer_positions, route_customers, route_load, total_cost
from src.instances import Instance, Node
from src.localSearch import local_search, remove_empty_route

#=========================Shaking Operators=========================
def is_feasible_all(routes, inst):
    """Check every non-empty route for feasibility. Returns True if all pass."""
    try:
        for route in routes:
            if any(n.type == "c" for n in route):
                is_feasible(inst, route)
    except InfeasibilityError:
        return False
    return True


def intra_route_relocate(routes, inst):
    """k=1: move a customer to a different position within the same route."""
    positions = customer_positions(routes)
    random.shuffle(positions)

    for ri, ci in positions:
        route = routes[ri]
        cust = route[ci]
        cust_indices = route_customers(routes, ri)
        targets = [t for t in cust_indices if t != ci]
        random.shuffle(targets)

        for ti in targets[:config.VNS_SHAKING_TRIALS]:
            candidate = deepcopy(routes)
            node = candidate[ri].pop(ci)
            insert_at = ti if ti < ci else ti
            candidate[ri].insert(insert_at, node)

            try:
                is_feasible(inst, candidate[ri])
                return candidate
            except InfeasibilityError:
                continue
    return None


def cross_route_relocate(routes, inst):
    """k=2: move a customer from one route to a different route."""
    positions = customer_positions(routes)
    if len(positions) < 2:
        return None
    random.shuffle(positions)

    for ri, ci in positions:
        cust = routes[ri][ci]
        other_routes = [r for r in range(len(routes)) if r != ri]
        random.shuffle(other_routes)

        for rj in other_routes:
            target_route = routes[rj]
            if route_load(target_route) + cust.demand > inst.C:
                continue
            cust_in_target = route_customers(routes, rj)
            targets = cust_in_target + [len(target_route) - 1]
            random.shuffle(targets)

            for ti in targets[:config.VNS_SHAKING_TRIALS]:
                candidate = deepcopy(routes)
                node = candidate[ri].pop(ci)
                candidate[rj].insert(ti, node)
                remove_empty_route(candidate)

                if not is_feasible_all(candidate, inst):
                    continue
                return candidate
    return None


def cross_route_swap(routes, inst):
    """k=3: swap two customers between different routes."""
    positions = customer_positions(routes)
    if len(positions) < 2:
        return None
    random.shuffle(positions)

    for i, (ri, ci) in enumerate(positions):
        for rj, cj in positions[i + 1:]:
            if ri == rj:
                continue
            candidate = deepcopy(routes)
            candidate[ri][ci], candidate[rj][cj] = candidate[rj][cj], candidate[ri][ci]

            if not is_feasible_all(candidate, inst):
                continue
            return candidate
    return None


def inter_route_segment_exchange(routes, inst):
    """k=4: swap a contiguous customer segment between two routes."""
    multi_routes = [
        ri for ri in range(len(routes))
        if len(route_customers(routes, ri)) >= 2
    ]
    if len(multi_routes) < 2:
        return None
    random.shuffle(multi_routes)

    for ri, rj in [(multi_routes[a], multi_routes[b])
                   for a in range(len(multi_routes))
                   for b in range(a + 1, len(multi_routes))]:
        ci_custs = route_customers(routes, ri)
        cj_custs = route_customers(routes, rj)

        for _ in range(config.VNS_SHAKING_TRIALS):
            si = random.randint(0, len(ci_custs) - 2)
            ei = random.randint(si + 1, len(ci_custs) - 1)
            sj = random.randint(0, len(cj_custs) - 2)
            ej = random.randint(sj + 1, len(cj_custs) - 1)

            seg_a_idx = set(ci_custs[si:ei + 1])
            seg_b_idx = set(cj_custs[sj:ej + 1])
            seg_b_customers = [routes[rj][cj_custs[k]] for k in range(sj, ej + 1)]
            seg_a_customers = [routes[ri][ci_custs[k]] for k in range(si, ei + 1)]

            candidate = deepcopy(routes)

            new_a, inserted_b = [], False
            for idx, node in enumerate(candidate[ri]):
                if idx in seg_a_idx:
                    if not inserted_b:
                        new_a.extend(seg_b_customers)
                        inserted_b = True
                else:
                    new_a.append(node)

            new_b, inserted_a = [], False
            for idx, node in enumerate(candidate[rj]):
                if idx in seg_b_idx:
                    if not inserted_a:
                        new_b.extend(seg_a_customers)
                        inserted_a = True
                else:
                    new_b.append(node)

            candidate[ri] = new_a
            candidate[rj] = new_b
            remove_empty_route(candidate)

            if not is_feasible_all(candidate, inst):
                continue
            return candidate
    return None


#=========================Shaking Dispatcher=========================
SHAKING_OPERATORS = [
    intra_route_relocate,
    cross_route_relocate,
    cross_route_swap,
    inter_route_segment_exchange,
]

def shaking(routes, k, inst):
    """
    Generate a feasible neighbor using neighborhood k (1-indexed).
    Tries up to VNS_SHAKING_TRIALS times. Returns None if no feasible neighbor found.
    """
    operator = SHAKING_OPERATORS[k - 1]
    for _ in range(config.VNS_SHAKING_TRIALS):
        candidate = operator(deepcopy(routes), inst)
        if candidate is not None:
            return candidate
    return None


#=========================VNS Main Loop=========================
def vns(routes: list[list[Node]], inst: Instance):
    """
    Variable Neighborhood Search.

    Args:
        routes: already-improved solution (e.g. greedy + LS output)
        inst: problem instance

    Returns:
        (best_routes, best_cost, elapsed_time)
    """
    start = time.perf_counter()
    random.seed(config.VNS_RANDOM_SEED)

    best = deepcopy(routes)
    best_cost = total_cost(best)
    x = deepcopy(routes)

    k = 1
    no_improve = 0

    while (no_improve < config.VNS_MAX_NO_IMPROVE
           and (time.perf_counter() - start) < config.VNS_MAX_TIME):

        x_prime = shaking(x, k, inst)
        if x_prime is None:
            k = (k % config.VNS_K_MAX) + 1
            continue

        x_ls, _, _ = local_search(x_prime, inst)
        cost_new = total_cost(x_ls)

        if cost_new < best_cost:
            best = deepcopy(x_ls)
            best_cost = cost_new
            x = deepcopy(x_ls)
            k = 1
            no_improve = 0
        else:
            k = (k % config.VNS_K_MAX) + 1
            if k == 1:
                no_improve += 1

    elapsed = time.perf_counter() - start
    return best, best_cost, elapsed
