from src.instances import get_instances
from src.solutionConstructor import greedy_construction

if __name__ == "__main__":
    #import the data from the instances file
    inst = get_instances("./resources/test-instances/rc201C10.txt" )

    #====================================================
    #===                 Task 1                       ===
    #====================================================
    routes = greedy_construction(inst)
    if routes is not None:
        for route in routes:
            print("[", end='')
            for r in route:
                print(r.id, end=',')
            print("]")