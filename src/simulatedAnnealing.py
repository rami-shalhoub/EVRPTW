import math
import random
import time
from copy import deepcopy

from .feasibility import InfeasibilityError, is_feasible
from src import config

from .solutionConstructor import last_resort, route_constructor
from .helpers import total_cost, shuffle
from .instances import Instance, Node


def construct_from_order( 
    customer_order: list[Node],
    inst: Instance 
): 
    routes: list[list[Node]] = [] 
    failed_customers: list[Node] = [] 
    unvisited = customer_order[:]
    i = config.ITERATIONS 

    while len(unvisited) != 0:
        route = route_constructor( 
            unvisited, 
            inst 
        )

        if route[-1].type == "d": 
            routes.append(route) 
        else: 
            failed_customers += [ 
                r 
                for r in route 
                if r.type == "c" 
            ] 
        served = [r for r in route if r.type == "c"]
        if len(served) == 0 and unvisited:
            failed_customers += unvisited
            unvisited.clear()
            last_resort(
                routes, 
                failed_customers, 
                inst 
            )
            break
        
        if len(unvisited) == 0: 
            break 
        if i > 0: 
            i -= 1 
            shuffle( 
                unvisited, 
                inst 
            ) 
        else: 
            failed_customers += unvisited
            last_resort(
                routes, 
                failed_customers,
                inst 
            ) 
            break 
    expected = {c.id for c in customer_order}
    served = [
        node.id
        for route in routes
        for node in route
        if node.type == "c"
    ]
    served_set = set(served)
    missing = expected - served_set
    duplicates = [c for c in served if served.count(c) > 1]
    if missing:
        print(f"Warning: missing customers in constructed solution: {missing}")
    if duplicates:
        print(f"Warning: duplicate customers in constructed solution: {duplicates}")
    return routes

def get_customer_order(
    routes: list[list[Node]]
):
    # We extract the customer order from a solution.
    #Depots and charging stations are ignored.

    customer_order = []

    for route in routes:

        for node in route:

            if node.type == "c":

                customer_order.append(node)

    return customer_order

def random_customer_relocate(
    customer_order: list[Node]
):
    #Creation of a random neighbouring solution.
    #Two customers are randomly selected and swapped.
    #Example:
        #[1, 2, 3, 4, 5] --> [1,4,3,2,5]

    neighbour = customer_order[:]

    if len(neighbour) < 2:
        return neighbour
    
    i, j = random.sample(range(len(neighbour)), 2)
    customer = neighbour.pop(i)
    neighbour.insert(j, customer)

    return neighbour

def random_neighbour(
        routes: list[list[Node]],
        inst: Instance,
        iteration: int
): 
    if iteration % 2 == 0:
        current_Order = get_customer_order(routes)
        neighbour_order = random_customer_relocate(current_Order)
        return construct_from_order(neighbour_order, inst)
    else:
        return random_station_relocate(routes, inst)

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
    
        try:
            is_feasible(inst,candidate_route)
        except InfeasibilityError:
           continue

        neighbour[r_idx] = candidate_route
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
    
    # Determine T0 based on the cost differences of random worsening neighbours.
    # We choose T0 so that a typical worsening move has an acceptance probability of approximately 80%.

    current_order = get_customer_order(
        initial_routes
    )

    current_cost = total_cost(
        initial_routes
    )

    deltas = []

    # Generate sample neighbours

    for _ in range(
        config.SA_TEMPERATURE_SAMPLES
    ):

        neighbour_order = random_customer_relocate(
            current_order
        )

        neighbour_routes = (
            construct_from_order(
                neighbour_order,
                inst
            )
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
    print("Positivie deltas:", deltas)
    print("Median delta:", median_delta)
    print("Initial temperature:", T0)

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
    print(f"Initial temperature: {temperature:.2f}")

    # 2. x <- buildSolution()
    # The solution comes from our construction heuristic.

    current_solution = deepcopy(
        initial_routes
    )

    current_cost = total_cost(
        current_solution
    )

    # Extract the representation used by SA: the customer order
    current_order = get_customer_order(
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
        temperature
        > config.SA_MIN_TEMPERATURE and no_improvement_stages < config.SA_MAX_NO_IMPROVEMENT_STAGES
    ):
        print(f"Temperature: {temperature:.2f}, best cost: {best_cost:.2f}")

        best_cost_before_stage = best_cost

        for _ in range(
            config.SA_ITERATIONS_PER_TEMPERATURE
        ):
            

            iteration += 1

            # 5. x' <- randomNeighbour(x)

            neighbour_solution = random_neighbour(
                current_solution,
                inst,
                iteration
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

                print(f"New best solution found: {best_cost:.2f} -> {current_cost:.2f}")

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

    print(
        f"SA statistics:"
        f"accepted moves: {accepted_moves}, "
        f"rejected moves: {rejected_moves}, "
        f"infeasible moves: {infeasible_moves}, "
        f"improving moves: {improving_moves}"
    )

    return (
        best_solution,
        cost_history,
        elapsed_time
    )
