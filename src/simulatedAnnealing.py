import math
import random
import time
from copy import deepcopy

from .feasibility import InfeasibilityError, is_feasible
from src import config

from .solutionConstructor import last_resort, route_constructor
from .helpers import total_cost, shuffle
from .instances import Instance, Node

def random_customer_swap(
    routes: list[Node],
    inst: Instance
):
    #Creation of a random neighbouring solution.
    #Two customers are randomly selected and swapped.
    #Example:
        #[1, 2, 3, 4, 5] --> [1,4,3,2,5]

    neighbour = deepcopy(routes)
    customer_positions = []

    for r_idx, route in enumerate(neighbour):

        for n_idx, node in enumerate(route):

            if node.type == "c":

                customer_positions.append((r_idx, n_idx))

    if len(customer_positions) < 2:
        return neighbour
    (r1,p1), (r2,p2) = random.sample(customer_positions, 2)
    neighbour[r1][p1], neighbour[r2][p2] = neighbour[r2][p2], neighbour[r1][p1]

    return neighbour

def random_customer_relocate(
        routes: list[list[Node]],
        inst: Instance
):
    neighbour = deepcopy(routes)
    customer_positions = []

    for r_idx, route in enumerate(neighbour):

        for n_idx, node in enumerate(route):

            if node.type == "c":

                customer_positions.append((r_idx, n_idx))

    if len(customer_positions) < 2:
        return neighbour
    r1, p1 = random.choice(customer_positions)

    possible_targets = [
        (r,p)
        for r,p in customer_positions
        if (r,p) != (r1,p1)
    ]
    r2, p2 = random.choice(possible_targets)
    customer = neighbour[r1].pop(p1)
    if r1 == r2 and p2 > p1:
        p2 -= 1
    neighbour[r2].insert(p2, customer)            
    return neighbour

def random_2opt(
    routes: list[list[Node]],
    inst: Instance
):
    neighbour = deepcopy(routes)
    candidate_routes = []

    for r_idx, route in enumerate(neighbour):
        customer_positions = [
            i
            for i, node in enumerate(route)
            if node.type == "c"
        ]
        if len(customer_positions) >= 2:
            candidate_routes.append(r_idx)

    if not candidate_routes:
        return neighbour
    r_idx = random.choice(candidate_routes)
    route = neighbour[r_idx]

    customer_positions = [
        i
        for i, node in enumerate(route)
        if node.type == "c"
    ]
    i, j = sorted(random.sample(customer_positions, 2))
    if i ==j:
        return neighbour
    candidate_route = route[:]
    candidate_route[i:j + 1] = reversed(
        candidate_route[i:j + 1]
    )
    neighbour [r_idx] = candidate_route
    #now we check the complete solution
    if not is_solution_feasible (neighbour, inst):
        return routes

    return neighbour        

def random_neighbour(
        routes: list[list[Node]],
        inst: Instance
): 
    move = random.choice([
        random_customer_swap,
        random_2opt,
        random_customer_relocate,
        random_station_relocate
    ])
    return move(routes, inst)

def random_station_relocate(
    routes: list[list[Node]],
    inst: Instance
):
    neighbour = deepcopy(routes)
    station_positions = []

    for r_idx, route in enumerate(neighbour):

        for n_idx, node in enumerate(route):

            if node.type == "f":

                station_positions.append((r_idx, n_idx))

    if not station_positions:
        return routes
    
    r_idx, n_idx = random.choice(station_positions)
    route = neighbour[r_idx]

    if n_idx ==0 or n_idx == len(route) -1:
        return neighbour

    old_station = route[n_idx]

    candidate_stations = [s for s in inst.stations if s.id != old_station.id]

    random.shuffle(candidate_stations)

    for station in candidate_stations:

        candidate_route = route[:]
        candidate_route[n_idx] = station
    
        neighbour[r_idx] = candidate_route

        if not is_solution_feasible(neighbour, inst):
            continue

        return neighbour
         
    return routes     

def has_all_customers(
    routes: list[list[Node]],
    inst: Instance
):
    expected = {c.id for c in inst.customers}
    served = [c.id for r in routes for c in r if c.type == "c"]
    served_set = set(served)
    if expected != served_set:
        return False
    if len(served) != len(served_set):
        return False
    return True

def is_solution_feasible(
    routes: list[list[Node]],
    inst: Instance
):
    try:
        for route in routes:
            is_feasible(inst, route)
    except InfeasibilityError:
        return False
    return True

def accept(
    current_cost: float,
    candidate_cost: float,
    temperature: float
):
    
    #Acceptance function of Simulated Annealing.
    #Better solution:
     #   always accepted
    #Worse solution:
        #accepted with probability
        #exp(-(candidate-current)/T)


    # Candidate is better

    if candidate_cost < current_cost:

        return True

    # Candidate is worse

    if temperature <= 0:

        return False

    delta = (
        candidate_cost
        - current_cost
    )

    probability = math.exp(
        -delta / temperature
    )

    return random.random() < probability

# Temperature Update

def update_temperature(
    temperature: float
):
    """
    Cooling rule:

        T_new = alpha * T
    """

    return (
        temperature
        * config.SA_COOLING_RATE
    )


# Calculate Initial Temperature

def calculate_initial_temperature(
    initial_routes: list[list[Node]],
    inst: Instance
):
    
    # We need to determine T0 based on the cost differences of random worsening neighbours.

    current_cost = total_cost(
        initial_routes
    )

    deltas = []

    # Generate sample neighbours

    for _ in range(
        config.SA_TEMPERATURE_SAMPLES
    ):


        move = random.choice([
            random_customer_swap,
            random_2opt,
            random_customer_relocate,
            random_station_relocate
        ])

        neighbour_routes = move (
            initial_routes,
            inst
        )

        neighbour_cost = total_cost(
            neighbour_routes
        )

        delta = (
            neighbour_cost
            - current_cost
        )

        # Only worsening moves are relevant for T0
        if delta > 0:

            deltas.append(delta)

    # Fallback

    if len(deltas) == 0:

        return max(
            current_cost * 0.1,
            1.0
        )

    # Median worsening move

    deltas.sort()

    median_delta = (
        deltas[len(deltas) // 2]
    )

    # Solve:
    # p = exp(-delta/T)
    # T = -delta / ln(p)

    T0 = (
        -median_delta
        / math.log(
            config.SA_TARGET_ACCEPTANCE
        )
    )
    # print("Positivie deltas:", deltas)
    # print("Median delta:", median_delta)
    # print("Initial temperature:", T0)

    # print("\nAcceptance probabilities")

    for factor in [1.0, 0.5, 0.1, 0.01, 0.001]:
        T= T0 * factor

        if T > 0:
            p=math.exp(-median_delta / T)
        else:
            p = 0.0
        # print(
        #     f"T = {T:.6f}"
        #     f"({factor:.3f}* T0)"
        #     f"-> P = {p:.4f}"
        # )        

    return T0

# Simulated Annealing that is like the Pseudocode in the lecture slides

def simulated_annealing(
    inst: Instance,
    initial_routes: list[list[Node]],
    seed = None
):
    if seed is not None:
        random.seed(seed)

    start = time.perf_counter()

    # 1. T <- T0

    temperature = calculate_initial_temperature(
        initial_routes,
        inst
    )
    # print(f"Initial temperature: {temperature:.2f}")

    # 2. x <- buildSolution()
    # The solution comes from our construction heuristic.

    current_solution = deepcopy(
        initial_routes
    )

    current_cost = total_cost(
        current_solution
    )

    # 3. x* <- x

    best_solution = deepcopy(
        current_solution
    )

    best_cost = current_cost

    cost_history = []
    best_cost_history = []
    temperature_history = []

    iteration = 0
    no_improvement_stages = 0
    accepted_moves = 0
    rejected_moves = 0
    infeasible_moves = 0
    improving_moves = 0

    # 4. while stopping criterion not reached

    while (
        no_improvement_stages < config.SA_MAX_NO_IMPROVEMENT_STAGES
    ):
        # print(f"Temperature: {temperature:.15f}, best cost: {best_cost:.2f}")

        best_cost_before_stage = best_cost

        for _ in range(
            config.SA_ITERATIONS_PER_TEMPERATURE
        ):
            

            iteration += 1

            # 5. x' <- randomNeighbour(x)

            neighbour_solution = random_neighbour(
                current_solution,
                inst
            )

            # feasibility checks
            if not has_all_customers(
                neighbour_solution,
                inst
            ):
                infeasible_moves += 1
                continue

            if not is_solution_feasible(neighbour_solution, inst):
                infeasible_moves += 1
                continue

            # Calc z(x*), the objective value of candidate solution
            neighbour_cost = total_cost(
                neighbour_solution
            )

            if neighbour_cost < current_cost:
                improving_moves += 1

            # 6. x <- accept(x, x', T)

            if accept(
                current_cost,
                neighbour_cost,
                temperature
            ):
                accepted_moves += 1


                current_solution = (
                    neighbour_solution
                )

                current_cost = (
                    neighbour_cost
                )
            else:
                rejected_moves += 1    

            # 7. if z(x) < z(x*)

            if current_cost < best_cost:

                # print(f"New best solution found: {best_cost:.2f} -> {current_cost:.2f}")

                 # 8. x* <- x

                best_solution = deepcopy(
                    current_solution
                )

                best_cost = (
                    current_cost
                )

            cost_history.append(
                current_cost
            )

            best_cost_history.append(
                best_cost
            )

            temperature_history.append(
                temperature
            )

        if best_cost < best_cost_before_stage:

            no_improvement_stages = 0
        else:
            no_improvement_stages += 1
        
        # 9. update(T)

        temperature = update_temperature(
            temperature
        )

    elapsed_time = (
        time.perf_counter()
        - start
    )

    # print(
    #     f"SA statistics:"
    #     f"accepted moves: {accepted_moves}, "
    #     f"rejected moves: {rejected_moves}, "
    #     f"infeasible moves: {infeasible_moves}, "
    #     f"improving moves: {improving_moves}"
    # )

    convergence = {
        "cost_history": cost_history,
        "best_cost_history": best_cost_history,
        "temperature_history": temperature_history,
        "accepted_moves": accepted_moves,
        "rejected_moves": rejected_moves,
        "infeasible_moves": infeasible_moves,
        "improving_moves": improving_moves,
        "initial_temperature": temperature_history[0] if temperature_history else 0.0,
        "stages_completed": iteration // config.SA_ITERATIONS_PER_TEMPERATURE,
    }

    return (
        best_solution,
        convergence,
        elapsed_time
    )
