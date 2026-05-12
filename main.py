from src.helpers import  export_to_csv, total_cost
from src.instances import get_instances
from src.localSearch import local_search
from src.solutionConstructor import greedy_construction

import random
import os
import time
from statistics import mean

RUNS= 5

if __name__ == "__main__":

    # ====================================================
    # ===                 Task 1                       ===
    # ====================================================

    instance_folder ="./resources/instances/"
    instance_files = [f for f in os.listdir(instance_folder) if f.endswith(".txt")]

    results:list[tuple[str, float, float, float]]= []

    for file in instance_files:
        path= os.path.join(instance_folder, file)
        inst = get_instances(path)
        instance_name = file.replace(".txt", "")
        final_costs: list[float] = []
        total_times:list[float] = []

        print(f"\nRunning {instance_name} for {RUNS} runs...")

        for i in range(RUNS):
            #construction + local search

            start = time.perf_counter()

            routes = greedy_construction(inst, 1000, RUNS, 2)

            if routes is not None:
                routes = local_search(routes, inst)
                # cost = total_cost(routes)
                final_cost = total_cost(routes)
                final_costs.append(final_cost)
                runtime = time.perf_counter() - start
                total_times.append(runtime)

            #Skips the instance if all runs failed
        if len(final_costs) == 0:
            continue

        best_final = min (final_costs)
        avg_final = mean(final_costs)
        avg_time = mean(total_times)

        results.append((instance_name, best_final, avg_final, avg_time))   

    #Output in CSV file
    export_to_csv(results, 'results_2')