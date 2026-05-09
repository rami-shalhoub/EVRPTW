from src.helpers import export, print_routes
from src.instances import get_instances
from src.localSearch import local_search
from src.solutionConstructor import greedy_construction

if __name__ == "__main__":
    # import the data from the instances file
    inst = get_instances("./resources/test-instances/c101C10.txt")
    # inst = get_instances("./resources/instances/c103_21.txt")

    # ====================================================
    # ===                 Task 1                       ===
    # ====================================================
    for i in range(50):
        routes = greedy_construction(inst, 50)
        
        if routes is not None :
            print_routes(routes, "routes constructed from greedy alorithm: ")
            routes = local_search(routes, inst)
            print_routes(routes, "routes constructed from greedy alorithm: ")
            export(routes,"c101C10")
            break
