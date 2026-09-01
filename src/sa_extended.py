"""
Task 3: Enhanced Simulated Annealing
Keeps SA's core concept (temperature + Metropolis acceptance).
Enhancements: weighted neighborhoods, adaptive cooling, periodic local search,
reannealing, dynamic iterations per stage.
"""

import math
import random
import time
from copy import deepcopy

from src import config

from .helpers import customer_positions, route_customers, route_load, total_cost
from .instances import Instance, Node
from .localSearch import local_search, remove_empty_route
from .simulatedAnnealing import (
    accept,
    calculate_initial_temperature,
    has_all_customers,
    is_solution_feasible,
    random_2opt,
    random_customer_relocate,
    random_customer_swap,
    random_station_relocate,
)

# ========================================================================
#  NEW Neighborhoods for Task 3 (adapted from vns.py)
# ========================================================================

def random_cross_route_relocate(routes: list[list[Node]], inst: Instance):
    """Move a customer from one route to a different route.
    Adapted from vns.py cross_route_relocate."""
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

            for ti in targets:
                candidate = deepcopy(routes)
                node = candidate[ri].pop(ci)
                candidate[rj].insert(ti, node)
                remove_empty_route(candidate)
                if not is_solution_feasible(candidate, inst):
                    continue
                return candidate
    return None


def random_segment_exchange(routes: list[list[Node]], inst: Instance):
    """Swap a contiguous customer segment between two routes.
    Adapted from vns.py inter_route_segment_exchange."""
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

        if not is_solution_feasible(candidate, inst):
            continue
        return candidate
    return None


# ========================================================================
#  Weighted Neighborhood Selection
# ========================================================================

ALL_MOVES = [
    random_customer_swap,
    random_2opt,
    random_customer_relocate,
    random_station_relocate,
    random_cross_route_relocate,
    random_segment_exchange,
]

MOVE_NAMES = [m.__name__ for m in ALL_MOVES]


def init_move_weights():
    """Start with equal weights for all moves."""
    return {name: 1.0 for name in MOVE_NAMES}


def select_move(weights: dict):
    """Select a move proportional to its weight."""
    names = list(weights.keys())
    w = [weights[n] for n in names]
    return random.choices(names, weights=w, k=1)[0]


def get_move_fn(name: str):
    """Look up move function by name."""
    return {m.__name__: m for m in ALL_MOVES}[name]


def update_weights(weights: dict, move_name: str, accepted: bool, improved: bool):
    """Update weight based on move outcome.
    - accepted + improved: strong boost
    - accepted but not improved: slight boost (SA useful move)
    - rejected: slight decay
    - infeasible: no change (don't penalize structural infeasibility)
    """
    for name in weights:
        if name == move_name:
            if accepted and improved:
                weights[name] *= 1.10
            elif accepted:
                weights[name] *= 1.02
            else:
                weights[name] *= 0.98
        # slowly normalize other weights toward 1.0
        weights[name] = weights[name] ** 0.999
    # clamp
    for name in weights:
        weights[name] = max(0.2, min(weights[name], 5.0))


# ========================================================================
#  Temperature functions
# ========================================================================

def adaptive_update_temperature(temperature: float, acceptance_rate: float):
    """Adjust cooling rate based on acceptance rate."""
    if acceptance_rate > config.SA_ACCEPTANCE_HIGH:
        alpha = config.SA_ALPHA_FAST
    elif acceptance_rate < config.SA_ACCEPTANCE_LOW:
        alpha = config.SA_ALPHA_SLOW
    else:
        alpha = config.SA_COOLING_RATE
    return temperature * alpha


def dynamic_iterations(temperature: float, t0: float):
    """Scale iterations per stage: fewer at high T, more at low T."""
    t_min = config.SA_MIN_TEMPERATURE
    if t0 <= t_min:
        return config.SA_MAX_ITERATIONS_PER_STAGE
    frac = (temperature - t_min) / (t0 - t_min)
    frac = max(0.0, min(1.0, frac))
    low = config.SA_MIN_ITERATIONS_PER_STAGE
    high = config.SA_MAX_ITERATIONS_PER_STAGE
    return int(high - frac * (high - low))


# ========================================================================
#  Enhanced Simulated Annealing (Task 3)
# ========================================================================

def simulated_annealing_ext(
    inst: Instance,
    initial_routes: list[list[Node]],
    seed=None
):
    if seed is not None:
        random.seed(seed)

    start = time.perf_counter()

    # 1. T <- T0
    T0 = calculate_initial_temperature(initial_routes, inst)
    temperature = T0
    # print(f"Initial temperature: {temperature:.2f}")

    # 2. x <- buildSolution()
    current_solution = deepcopy(initial_routes)
    current_cost = total_cost(current_solution)

    # 3. x* <- x
    best_solution = deepcopy(current_solution)
    best_cost = current_cost

    # Tracking
    cost_history = []
    best_cost_history = []
    temperature_history = []
    move_stats = {name: {"attempts": 0, "accepted": 0} for name in MOVE_NAMES}
    weights = init_move_weights()

    iteration = 0
    no_improvement_stages = 0
    reannealing_rounds = 0
    intensification_count = 0
    stage_count = 0
    accepted_moves = 0
    rejected_moves = 0
    infeasible_moves = 0

    # 4. while stopping criterion not reached
    while (no_improvement_stages < config.SA_MAX_NO_IMPROVEMENT_STAGES
           and (time.perf_counter() - start) < config.SA_MAX_TIME):
        # print(f"Temperature: {temperature:.15f}, best cost: {best_cost:.2f}")

        best_cost_before_stage = best_cost
        stage_accepted = 0
        stage_total = 0

        # Dynamic iterations per stage
        iters = dynamic_iterations(temperature, T0)

        for _ in range(iters):
            iteration += 1

            # 5. x' <- weighted_random_neighbour(x)
            move_name = select_move(weights)
            move_fn = get_move_fn(move_name)
            neighbour_solution = move_fn(current_solution, inst)

            # feasibility checks
            if neighbour_solution is None or not has_all_customers(neighbour_solution, inst):
                infeasible_moves += 1
                continue

            if not is_solution_feasible(neighbour_solution, inst):
                infeasible_moves += 1
                continue

            neighbour_cost = total_cost(neighbour_solution)
            stage_total += 1
            move_stats[move_name]["attempts"] += 1

            # 6. x <- accept(x, x', T)
            if accept(current_cost, neighbour_cost, temperature):
                accepted_moves += 1
                stage_accepted += 1
                current_solution = neighbour_solution
                current_cost = neighbour_cost
                move_stats[move_name]["accepted"] += 1

                improved = neighbour_cost < best_cost
                update_weights(weights, move_name, True, improved)
            else:
                rejected_moves += 1
                update_weights(weights, move_name, False, False)

            # 7. if z(x) < z(x*)
            if current_cost < best_cost:
                # print(f"New best solution found: {best_cost:.2f} -> {current_cost:.2f}")
                best_solution = deepcopy(current_solution)
                best_cost = current_cost

            cost_history.append(current_cost)
            best_cost_history.append(best_cost)
            temperature_history.append(temperature)

        stage_count += 1

        # Enhancement 3: Periodic intensification via local search
        if stage_count % config.SA_INTENSIFICATION_INTERVAL == 0:
            # print(f"  Intensification: running local search on best solution ({best_cost:.2f})")
            intensification_count += 1
            ls_routes, _, _, _, _ = local_search(deepcopy(best_solution), inst)
            ls_cost = total_cost(ls_routes)
            if ls_cost < best_cost:
                # print(f"  Local search improved: {best_cost:.2f} -> {ls_cost:.2f}")
                best_solution = ls_routes
                best_cost = ls_cost
                current_solution = deepcopy(ls_routes)
                current_cost = ls_cost

        # Check improvement
        if best_cost < best_cost_before_stage:
            no_improvement_stages = 0
        else:
            no_improvement_stages += 1

        # Enhancement 4: Reannealing
        if no_improvement_stages >= config.SA_MAX_NO_IMPROVEMENT_STAGES:
            if reannealing_rounds < config.SA_REANNEALING_ROUNDS:
                # print(f"  Reannealing round {reannealing_rounds + 1}: "
                #       f"T {temperature:.4f} -> {T0 * config.SA_REANNEALING_TEMP_FRACTION:.4f}")
                temperature = T0 * config.SA_REANNEALING_TEMP_FRACTION
                current_solution = deepcopy(best_solution)
                current_cost = best_cost
                no_improvement_stages = 0
                reannealing_rounds += 1
            # else: will terminate on next loop check

        # 9. update(T) — Enhancement 2: Adaptive cooling
        acceptance_rate = stage_accepted / max(stage_total, 1)
        temperature = adaptive_update_temperature(temperature, acceptance_rate)

    elapsed_time = time.perf_counter() - start

    # print(f"\nSA statistics: accepted={accepted_moves}, rejected={rejected_moves}, "
    #       f"infeasible={infeasible_moves}")
    # print(f"Move stats: {move_stats}")
    # print(f"Weights: {weights}")
    # print(f"Reannealing rounds used: {reannealing_rounds}")

    convergence = {
        "cost_history": cost_history,
        "best_cost_history": best_cost_history,
        "temperature_history": temperature_history,
        "accepted_moves": accepted_moves,
        "rejected_moves": rejected_moves,
        "infeasible_moves": infeasible_moves,
        "initial_temperature": temperature_history[0] if temperature_history else 0.0,
        "stages_completed": stage_count,
        "move_stats": move_stats,
        "final_weights": weights,
        "reannealing_rounds": reannealing_rounds,
        "intensification_count": intensification_count,
    }

    return best_solution, convergence, elapsed_time
