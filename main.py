from src.helpers import print_routes, route_cost
from src.instances import get_instances
from src.localSearch import local_search
from src.solutionConstructor import greedy_construction

import os
import time
import csv
from statistics import mean


OUTPUT_FILE = "results_3.csv"

def solution_cost(routes):
    return sum(route_cost(route) for route in routes)


def format_number(num):
    return f"{num:.6f}".replace(".", ",")



if __name__ == "__main__":
    #import the data from the instances file
    inst = get_instances("./resources/test-instances/rc201C10.txt" )

    instance_name = os.path.basename("./resources/test-instances/rc201C10.txt").replace(".txt", "")

    #====================================================
    #===                 Task 1                       ===
    #====================================================
    start_time = time.perf_counter()
    while True:
        routes = greedy_construction(inst)
        if routes is not None:
            print("routes constructed from greedy alorithm")
            print_routes(routes)
            routes = local_search(routes, inst)
            runtime= time.perf_counter() - start_time
            print("routes after local search")
            print_routes(routes)
            best_cost = solution_cost(routes)

            with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["", "best", "avg", "avg.time(s)"])
                writer.writerow([instance_name, format_number(best_cost), format_number(best_cost), format_number(runtime)])

            print(f"\nResults written to {OUTPUT_FILE}")
            print(f"Objective value: {format_number(best_cost)}")    
            break
        else:
            print("failed attempt")