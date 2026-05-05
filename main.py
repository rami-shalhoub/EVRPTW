from src.helpers import print_routes
from src.instances import get_instances
from src.localSearch import local_search
from src.solutionConstructor import greedy_construction

if __name__ == "__main__":
    #import the data from the instances file
    inst = get_instances("./resources/test-instances/rc201C10.txt" )

    #====================================================
    #===                 Task 1                       ===
    #====================================================
    while True:
        routes = greedy_construction(inst)
        if routes is not None:
            print("routes constructed from greedy alorithm")
            print_routes(routes)
            routes = local_search(routes, inst)
            print("routes after local search")
            print_routes(routes)
            break
        else:
            print("failed attempt")