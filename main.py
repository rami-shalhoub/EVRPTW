from src.helpers import export, total_cost
from src.instances import get_instances
from src.localSearch import local_search
from src.solutionConstructor import greedy_construction

import os
import time
import csv
from statistics import mean


OUTPUT_FILE = "results_3.csv"


if __name__ == "__main__":
    # import the data from the instances file
    inst = get_instances("./resources/instances/c103_21.txt")

    # ====================================================
    # ===                 Task 1                       ===
    # ====================================================
    routes = greedy_construction(inst, 1000, 5, 2)
    if routes is not None :
        print(f"routes constructed from greedy alorithm cost: {total_cost(routes)}")
        routes = local_search(routes, inst)
        print(f"routes improved with local search cost: {total_cost(routes)}")
        export(routes,"c103_21")
