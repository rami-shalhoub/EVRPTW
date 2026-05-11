from src.helpers import export, total_cost, route_cost, format_number
from src.instances import get_instances
from src.localSearch import local_search
from src.solutionConstructor import greedy_construction

import os
import time
import csv
from statistics import mean


if __name__ == "__main__":
    # import the data from the instances file
    inst = get_instances("./resources/instances/rc203_21.txt")

    # ====================================================
    # ===                 Task 1                       ===
    # ====================================================
    routes = greedy_construction(inst, 1000, 5, 2)
    if routes is not None :
        print(f"routes constructed from greedy alorithm cost: {total_cost(routes)}")
        routes = local_search(routes, inst)
        print(f"routes improved with local search cost: {total_cost(routes)}")
        export(routes,"c103_21")

    #Output in CSV file
    with open('results_3.csv', mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(["", "best", "avg", "avg.time(s)"])
        writer.writerow(['rc203_21', format_number(total_cost(routes)), format_number(total_cost(routes)), format_number(time.time())]) 
