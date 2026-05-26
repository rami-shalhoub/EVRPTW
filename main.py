import os
import time
from statistics import mean

import click

from src.helpers import export_to_csv, export_to_txt, total_cost
from src.instances import get_instances
from src.localSearch import local_search
from src.solutionConstructor import greedy_construction


@click.command()
@click.option(
    "--iter",
    default=1000,
    prompt="iteration",
    help="the number of iteration perormed in the constructor algorithm",
)
@click.option(
    "--run",
    default=3,
    prompt="run",
    help="the number of times the algorithms will run to improve performance",
)
@click.option(
    "--station",
    default=3,
    prompt="stations",
    help="the number of station to consoder trying in the constructor algorithm",
)

# ====================================================
# ===                 Task 1                       ===
# ====================================================
def Task1(iter: int, run: int, station: int):

    instance_folder = "./resources/instances/"
    instance_files = [f for f in os.listdir(instance_folder) if f.endswith(".txt")]

    results: list[tuple[str, float, float, float]] = []
    for file in instance_files:
        path = os.path.join(instance_folder, file)
        inst = get_instances(path)
        instance_name = file.replace(".txt", "")
        final_costs: list[float] = []
        total_times: list[float] = []

        print(f"\nRunning {instance_name} for {run} runs...")

        # construction + local search

        start = time.perf_counter()

        routes = greedy_construction(inst, iter, run, station)

        if routes is not None:
            routes = local_search(routes, inst, run)
            # cost = total_cost(routes)
            final_cost = total_cost(routes)
            final_costs.append(final_cost)
            runtime = time.perf_counter() - start
            total_times.append(runtime)

            # Skips the instance if all runs failed
            if len(final_costs) == 0:
                continue

            best_final = min(final_costs)
            avg_final = mean(final_costs)
            avg_time = mean(total_times)

            results.append((instance_name, best_final, avg_final, avg_time))

            # export solution
            export_to_txt(routes, instance_name, best_final)

    return results


if __name__ == "__main__":
    results = Task1()
    # Output in CSV file
    # export_to_csv(results, "results_10")
