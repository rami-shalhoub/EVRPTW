from src.instances  import get_instances
from src.solver import greedy_construction, local_search, print_solution

if __name__ == "__main__":
    #import the data from the instances file
    depot, customers, stations, Q, C, r, g, v = get_instances(
        "./resources/test-instances/c101C10.txt"
    )

    #====================================================
    #===                 Task 1                      ===
    #====================================================
    routes = greedy_construction(depot, customers, stations, Q, C, r, g)
    print("solution from greedy algorithm:")
    print_solution(routes)

    routes = local_search(routes, Q, C, r, g)
    print("solution after local search")
    print_solution(routes)
