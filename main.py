from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
import multiprocessing
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
from src.simulatedAnnealing import simulated_annealing
from src.sa_extended import simulated_annealing_ext
from src.vns import vns


def solution_metrics(routes):
    """Compute solution structure metrics from routes."""
    routes_count = len(routes)
    customers_served = sum(1 for r in routes for n in r if n.type == "c")
    stations_used = sum(1 for r in routes for n in r if n.type == "f")
    return routes_count, customers_served, stations_used


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
@click.option(
    "--workers",
    default=0,
    help="Number of parallel workers (0 = run all instances in parallel)",
)

# ====================================================
# ===                 Task 1                       ===
# ====================================================
def Task(iter: int, run: int, station: int, workers: int):
    config.ITERATIONS = iter
    config.RUNS = run
    config.STATIONS = station

    instance_folder = "./resources/instances/"
    instance_files = [f for f in os.listdir(instance_folder) if f.endswith(".txt")]

    max_workers = workers if workers > 0 else len(instance_files)

    run_data: list[dict] = []
    convergence_data: list[dict] = []
    run_metadata: list[dict] = []

    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=max_workers, mp_context=ctx) as executor:
        futures = {
            executor.submit(process_instance, file, instance_folder, iter, run, station): file
            for file in instance_files
        }
        for future in as_completed(futures):
            file = futures[future]
            result = future.result()
            print(f"  {file} done")
            run_data.extend(result["run_data"])
            convergence_data.extend(result["convergence_data"])
            run_metadata.extend(result["run_metadata"])

    export_to_csv(run_data, "algo_run_data")
    export_to_csv(convergence_data, "convergence_data")
    export_to_csv(run_metadata, "algo_run_metadata")
    export_summary_csv()


def process_instance(file, instance_folder, iter_val, run_val, station_val):
    config.ITERATIONS = iter_val
    config.RUNS = run_val
    config.STATIONS = station_val

    path = os.path.join(instance_folder, file)
    inst = get_instances(path)
    instance_name = file.replace(".txt", "")

    print(f"\n{instance_name} – running greedy + local search + simulated annealing + simulated annealing extended")

    run_data: list[dict] = []
    convergence_data: list[dict] = []
    run_metadata: list[dict] = []

    #Greedy construction
    greedy_routes, greedy_costs, greedy_times, greedy_conv = greedy_construction(inst)
    greedy_cost = total_cost(greedy_routes)
    export_to_txt(greedy_routes, f"{instance_name}_g", greedy_cost)

    # Log greedy convergence data (per-iteration within each mode)
    for mode_idx, mode_conv in enumerate(greedy_conv):
        for rec in mode_conv:
            convergence_data.append({
                "instance": instance_name,
                "algorithm": "greedy",
                "run": mode_idx,
                "iteration": rec["iteration"],
                "cost": rec["cost"],
                "best_cost": 0,
                "temperature": 0,
                "routes_count": rec["routes_count"],
                "customers_served": rec["customers_served"],
                "unvisited_count": rec["unvisited_count"],
                "failed_count": rec["failed_count"],
            })

    #Local search
    ls_routes, ls_costs, ls_times, ls_meta, ls_conv = local_search(deepcopy(greedy_routes), inst)
    ls_cost = total_cost(ls_routes)
    export_to_txt(ls_routes, f"{instance_name}_ls", ls_cost)

    # Log LS convergence data (per-run, per-improvement)
    for run_idx, run_conv in enumerate(ls_conv):
        for rec in run_conv:
            convergence_data.append({
                "instance": instance_name,
                "algorithm": "ls",
                "run": run_idx,
                "iteration": rec["iteration"],
                "cost": rec["cost"],
                "best_cost": 0,
                "temperature": 0,
                "routes_count": rec["routes_count"],
                "customers_served": rec["customers_served"],
                "unvisited_count": 0,
                "failed_count": 0,
            })

    #Simulated annealing
    print("simulated annealing:")
    sa_costs = []
    sa_times = []

    best_sa_cost = float("inf")
    best_sa_routes = None

    for run_idx in range (config.RUNS):
        seed = config.SA_RANDOM_SEED + run_idx
        sa_routes, sa_conv, sa_time = simulated_annealing(inst, deepcopy(greedy_routes), seed=seed)
        sa_cost = total_cost(sa_routes)
        sa_costs.append(sa_cost)
        sa_times.append(sa_time)
        if sa_cost < best_sa_cost:
            best_sa_cost = sa_cost
            best_sa_routes = deepcopy(sa_routes)

        # Log SA convergence data (per-iteration)
        for i in range(len(sa_conv["cost_history"])):
            convergence_data.append({
                "instance": instance_name,
                "algorithm": "sa",
                "run": run_idx,
                "iteration": i + 1,
                "cost": sa_conv["cost_history"][i],
                "best_cost": sa_conv["best_cost_history"][i],
                "temperature": sa_conv["temperature_history"][i],
                "routes_count": 0,
                "customers_served": 0,
                "unvisited_count": 0,
                "failed_count": 0,
            })

        # Log SA per-run metadata
        sa_routes_count, sa_cust_served, sa_stations = solution_metrics(sa_routes)
        run_metadata.append({
            "instance": instance_name,
            "algorithm": "sa",
            "run": run_idx,
            "cost": sa_cost,
            "time": sa_time,
            "routes_count": sa_routes_count,
            "customers_served": sa_cust_served,
            "stations_used": sa_stations,
            "accepted_moves": sa_conv["accepted_moves"],
            "rejected_moves": sa_conv["rejected_moves"],
            "infeasible_moves": sa_conv["infeasible_moves"],
            "improving_moves": sa_conv["improving_moves"],
            "stages_completed": sa_conv["stages_completed"],
            "initial_temperature": sa_conv["initial_temperature"],
            "improvements_made": 0,
            "ejected_customers": 0,
        })

    export_to_txt(best_sa_routes, f"{instance_name}_sa", best_sa_cost)

    #Enhanced Simulated Annealing (Task 3)
    print("simulated annealing extended:")
    sa_ext_costs = []
    sa_ext_times = []

    best_sa_ext_cost = float("inf")
    best_sa_ext_routes = None

    for run_idx in range(config.RUNS):
        seed = config.SA_RANDOM_SEED + run_idx
        sa_ext_routes, sa_ext_conv, sa_ext_time = simulated_annealing_ext(
            inst, deepcopy(greedy_routes), seed=seed
        )
        sa_ext_cost = total_cost(sa_ext_routes)
        sa_ext_costs.append(sa_ext_cost)
        sa_ext_times.append(sa_ext_time)
        if sa_ext_cost < best_sa_ext_cost:
            best_sa_ext_cost = sa_ext_cost
            best_sa_ext_routes = deepcopy(sa_ext_routes)

        # Log SA_ext convergence data (per-iteration)
        for i in range(len(sa_ext_conv["cost_history"])):
            convergence_data.append({
                "instance": instance_name,
                "algorithm": "sa_ext",
                "run": run_idx,
                "iteration": i + 1,
                "cost": sa_ext_conv["cost_history"][i],
                "best_cost": sa_ext_conv["best_cost_history"][i],
                "temperature": sa_ext_conv["temperature_history"][i],
                "routes_count": 0,
                "customers_served": 0,
                "unvisited_count": 0,
                "failed_count": 0,
            })

        # Log SA_ext per-run metadata
        sa_ext_routes_count, sa_ext_cust_served, sa_ext_stations = solution_metrics(sa_ext_routes)
        run_metadata.append({
            "instance": instance_name,
            "algorithm": "sa_ext",
            "run": run_idx,
            "cost": sa_ext_cost,
            "time": sa_ext_time,
            "routes_count": sa_ext_routes_count,
            "customers_served": sa_ext_cust_served,
            "stations_used": sa_ext_stations,
            "accepted_moves": sa_ext_conv["accepted_moves"],
            "rejected_moves": sa_ext_conv["rejected_moves"],
            "infeasible_moves": sa_ext_conv["infeasible_moves"],
            "improving_moves": 0,
            "stages_completed": sa_ext_conv["stages_completed"],
            "initial_temperature": sa_ext_conv["initial_temperature"],
            "improvements_made": 0,
            "ejected_customers": 0,
            "reannealing_rounds": sa_ext_conv["reannealing_rounds"],
            "intensification_count": sa_ext_conv["intensification_count"],
        })

    export_to_txt(best_sa_ext_routes, f"{instance_name}_sa_ext", best_sa_ext_cost)

    #VNS
    # vns_routes, vns_cost, vns_time = vns(deepcopy(greedy_routes), inst)
    # export_to_txt(vns_routes, f"{instance_name}_vns", vns_cost)

    # Greedy run_data (3 modes as runs)
    for i, (c, t) in enumerate(zip(greedy_costs, greedy_times)):
        run_data.append({
            "instance": instance_name,
            "algorithm": "greedy",
            "run": i,
            "cost": c,
            "time": t,
        })

    # Greedy per-run metadata
    greedy_routes_count, greedy_cust_served, greedy_stations = solution_metrics(greedy_routes)
    for i, (c, t) in enumerate(zip(greedy_costs, greedy_times)):
        run_metadata.append({
            "instance": instance_name,
            "algorithm": "greedy",
            "run": i,
            "cost": c,
            "time": t,
            "routes_count": greedy_routes_count,
            "customers_served": greedy_cust_served,
            "stations_used": greedy_stations,
            "accepted_moves": 0,
            "rejected_moves": 0,
            "infeasible_moves": 0,
            "improving_moves": 0,
            "stages_completed": 0,
            "initial_temperature": 0,
            "improvements_made": 0,
            "ejected_customers": 0,
        })

    for i, (c, t) in enumerate(zip(ls_costs, ls_times)):
        run_data.append({
            "instance": instance_name,
            "algorithm": "ls",
            "run": i,
            "cost": c,
            "time": t,
        })

    # LS per-run metadata
    ls_routes_count, ls_cust_served, ls_stations = solution_metrics(ls_routes)
    for i, (c, t) in enumerate(zip(ls_costs, ls_times)):
        meta = ls_meta[i] if i < len(ls_meta) else {"improvements_made": 0, "ejected_customers": 0}
        run_metadata.append({
            "instance": instance_name,
            "algorithm": "ls",
            "run": i,
            "cost": c,
            "time": t,
            "routes_count": ls_routes_count,
            "customers_served": ls_cust_served,
            "stations_used": ls_stations,
            "accepted_moves": 0,
            "rejected_moves": 0,
            "infeasible_moves": 0,
            "improving_moves": 0,
            "stages_completed": 0,
            "initial_temperature": 0,
            "improvements_made": meta["improvements_made"],
            "ejected_customers": meta["ejected_customers"],
        })

    for i, (c, t) in enumerate( zip( sa_costs, sa_times )):
        run_data.append({
            "instance": instance_name,
            "algorithm": "sa",
            "run": i,
            "cost": c,
            "time": t,
        })

    for i, (c, t) in enumerate(zip(sa_ext_costs, sa_ext_times)):
        run_data.append({
            "instance": instance_name,
            "algorithm": "sa_ext",
            "run": i,
            "cost": c,
            "time": t,
        })

    # run_data.append({
    #     "instance": instance_name,
    #     "algorithm": "vns",
    #     "run": 0,
    #     "cost": vns_cost,
    #     "time": vns_time,
    # })

    return {
        "run_data": run_data,
        "convergence_data": convergence_data,
        "run_metadata": run_metadata,
    }


if __name__ == "__main__":
    Task(standalone_mode=False)
