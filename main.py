import os

import click

from src import config
from src.helpers import (
    export_to_txt,
    export_to_csv,
    export_summary_csv,
    total_cost,
)
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

    run_data: list[dict] = []

    for file in instance_files:
        path = os.path.join(instance_folder, file)
        inst = get_instances(path)
        instance_name = file.replace(".txt", "")

        print(f"\n{instance_name} – running greedy + local search...")

        routes, greedy_costs, greedy_times = greedy_construction(inst)
        cost = total_cost(routes)
        export_to_txt(routes, f"{instance_name}_g", cost)
        
        routes, ls_costs, ls_times = local_search(routes, inst)
        cost = total_cost(routes)
        export_to_txt(routes, f"{instance_name}_ls", cost)

        for i, (c, t) in enumerate(zip(greedy_costs, greedy_times)):
            run_data.append({
                "instance": instance_name,
                "algorithm": "greedy",
                "run": i,
                "cost": c,
                "time": t,
            })

        for i, (c, t) in enumerate(zip(ls_costs, ls_times)):
            run_data.append({
                "instance": instance_name,
                "algorithm": "ls",
                "run": i,
                "cost": c,
                "time": t,
            })

    export_to_csv(run_data, "algo_run_data")
    export_summary_csv ()


if __name__ == "__main__":
    Task1(standalone_mode=False)