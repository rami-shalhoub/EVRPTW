import math
import random
import time
from copy import deepcopy

from src import config

from .solutionConstructor import construct_from_order
from .helpers import total_cost
from .instances import Instance, Node

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

def random_neighbour(
    customer_order: list[Node]
):
    #Creation of a random neighbouring solution.
    #Two customers are randomly selected and swapped.
    #Example:
        #[1, 2, 3, 4, 5] --> [1,4,3,2,5]

    neighbour = customer_order[:]

    if len(neighbour) < 2:

        return neighbour

    i, j = random.sample(
        range(len(neighbour)),
        2
    )

    neighbour[i], neighbour[j] = (
        neighbour[j],
        neighbour[i]
    )

    return neighbour

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

        neighbour_order = random_neighbour(
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

    return T0

# Simulated Annealing that is like the Pseudocode in the lecture slides

def simulated_annealing(
    inst: Instance,
    initial_routes: list[list[Node]]
):

    start = time.perf_counter()

    # 1. T <- T0

    temperature = calculate_initial_temperature(
        initial_routes,
        inst
    )

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

    # 4. while stopping criterion not reached

    while (
        temperature
        > config.SA_MIN_TEMPERATURE and no_improvement_stages < config.SA_MAX_NO_IMPROVEMENT_STAGES
    ):

        best_cost_before_stage = best_cost

        for _ in range(
            config.SA_ITERATIONS_PER_TEMPERATURE
        ):

            iteration += 1

            # 5. x' <- randomNeighbour(x)

            neighbour_order = (
                random_neighbour(
                    current_order
                )
            )

            # next we build a feasible solution from the neighbour
            # customer order using the ordered construction heuristic.

            neighbour_solution = (
                construct_from_order(
                    neighbour_order,
                    inst
                )
            )

            neighbour_cost = total_cost(
                neighbour_solution
            )

            # 6. x <- accept(x, x', T)

            if accept(
                current_cost,
                neighbour_cost,
                temperature
            ):

                current_solution = (
                    neighbour_solution
                )

                current_order = (
                    neighbour_order
                )

                current_cost = (
                    neighbour_cost
                )

            # 7. if z(x) < z(x*)

            if current_cost < best_cost:

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

    return (
        best_solution,
        cost_history,
        [elapsed_time]
    )
