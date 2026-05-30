from copy import deepcopy
import os
import time
from statistics import mean

import click

from src import config
from src.helpers import export_to_csv, export_to_txt, total_cost
from src.instances import get_instances
from src.localSearch1 import local_search as ls1
from src.localSearch2 import local_search as ls2
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
    config.ITERATIONS = iter
    config.RUNS = run
    config.STATIONS = station
    
    instance_folder = "./resources/instances/"
    instance_files = [f for f in os.listdir(instance_folder) if f.endswith(".txt")]

    results: list[tuple[str, float, float, float]] = []
    for file in instance_files:
        path = os.path.join(instance_folder, file)
        inst = get_instances(path)
        instance_name = file.replace(".txt", "")
        # final_costs: list[float] = []
        # total_times: list[float] = []

        print(f"\nRunning {instance_name} for {run} runs...")

        # construction + local search

        # start = time.perf_counter()

        routes = greedy_construction(inst)

        if routes is not None:
            #export greedy result
            final_cost = total_cost(routes)
            export_to_txt(routes, instance_name+'_g', final_cost)

            
            # export local search 1
            routes1 = deepcopy(routes)
            routes1= ls1(routes, inst)
            cost = total_cost(routes1)
            export_to_txt(routes1, instance_name+'_ls1', cost)

            # export local search 2
            routes2 = deepcopy(routes)
            routes2= ls2(routes, inst, run)
            cost = total_cost(routes2)


            # export solution
            export_to_txt(routes2, instance_name+'_ls2', cost)

    return results


if __name__ == "__main__":
    results = Task1(standalone_mode=False)
    # Output in CSV file
    # export_to_csv(results, "results_10")
