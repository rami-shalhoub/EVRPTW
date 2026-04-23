from solver import *
from instances import create_test_instance

if __name__ == "__main__":
    depot, customers, stations = create_test_instance()

    Q = 15
    C = 3
    r = 1
    g = 0.2

    routes = greedy_construction(depot, customers, stations, Q, C, r, g)
    routes = local_search(routes, Q, C, r, g)

    print_solution(routes)