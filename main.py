import os
import time
from statistics import mean

import click

from src import config
from src.helpers import export_to_csv, export_to_txt, total_cost, plot_history
from src.instances import get_instances
from src.localSearch import local_search
from src.solutionConstructor import greedy_construction


@click.command()
@click.option(
    "--iter",
    default=100,
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
    config.ITERATIONS = iter
    config.RUNS = run
    config.STATIONS = station
    
    instance_folder = "./resources/instances/"
    instance_files = [f for f in os.listdir(instance_folder) if f.endswith(".txt")]

    results: list[tuple[str, float, float, float]] = []
    results_history = []

    for file in instance_files:
        path = os.path.join(instance_folder, file)
        inst = get_instances(path)
        instance_name = file.replace(".txt", "")
        final_costs: list[float] = []
        total_times: list[float] = []

        print(f"\nRunning {instance_name} for {run} runs...")

        best_cost = float("inf")
        best_routes = None
        best_history = None

        for r in range(run):
            print(f"{instance_name} | run {r+1}/{run}")

            start = time.perf_counter()

            
            routes, history = greedy_construction(inst)

            routes, history = local_search(routes, inst)
            cost = total_cost(routes)
            final_costs.append(cost)
            total_times.append(time.perf_counter() - start)

            if cost < best_cost:
                best_cost = cost
                best_routes = routes
                best_history = history


        best_final = min(final_costs)
        avg_final = mean(final_costs)
        avg_time = mean(total_times)

        results.append((instance_name, best_final, avg_final, avg_time))
        results_history.append((instance_name, best_history))

        if best_routes is not None:
            export_to_txt(best_routes, instance_name, best_cost)

    best = min(results_history, key=lambda x: x[1][-1])
    worst = max(results_history, key=lambda x: x[1][-1])

    plot_history(best[1], f"Best instance: {best[0]}")
    plot_history(worst[1], f"Worst instance: {worst[0]}")

    return results


if __name__ == "__main__":
    results = Task1(standalone_mode=False)
    if results:
        export_to_csv(results, "results_10")
