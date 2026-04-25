from pathlib import Path

import click

from common.problem import read_evrptw_instance
from common.solution import Solution, read_evrptw_solution
from validator import validate, ValidationStatus

@click.command()
@click.option('--instance', help='Path to the instance file.')
@click.option('--solution', help='Path to the solution file.')
def run_validation(instance, solution):
    instance_path = Path(instance)
    solution_path = Path(solution)

    print(f"Reading EVRPTW instance from {instance_path}")
    instance = read_evrptw_instance(instance_path)

    print(f"Reading EVRPTW solution from {solution_path}")
    solution, solution_objective = read_evrptw_solution(solution_path, instance)

    print(f"Validate solution ...")
    result = validate(instance, solution)

    print(f"\nValidation result: {result.status}")
    if result.status == ValidationStatus.INFEASIBLE:
        if len(result.unassigned_customers) > 0:
            print(f"\tUnserved Customers: {", ".join(map(lambda i: instance.nodes[i].string_id, result.unassigned_customers))}")
        for validated_route, original_route in zip(result.routes, solution.routes):
            if validated_route.status == ValidationStatus.INFEASIBLE:
                print(f"\t{original_route}: {validated_route.status}")
                print(f"\t\tstart-end-depot: {validated_route.start_end_depot_feasible}")
                for visit in validated_route.itinerary:
                    print(f"\t\t{visit.node} ({instance.nodes[visit.node].string_id})\t| Time feasible: {visit.time_feasible}\t| Energy feasible: {visit.energy_feasible}")
    print(f"- Objective: {result.objective}")
    if abs(result.objective - solution_objective) > 0.00001:
        print(f"Warning: Objective read from solution file {solution_objective} does not match validated solution {result.objective}")


if __name__ == '__main__':
    run_validation()
