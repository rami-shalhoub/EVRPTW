from dataclasses import dataclass
from pathlib import Path

from common.problem import EVRPTWInstance


@dataclass
class Solution:
    routes: list[list[int]]

def read_evrptw_solution(filepath: Path, instance: EVRPTWInstance) -> (Solution, float):
    routes_with_string_ids = list()
    with open(filepath, 'r') as f:
        line = f.readline().strip()
        while line.startswith("#"):
            line = f.readline().strip()
        # first line is the considered objective value
        objective = float(line)

        line = f.readline().strip()
        while line != "":
            if line.startswith("#"):
                continue
            routes_with_string_ids.append([entry.strip() for entry in line.split(",")])
            line = f.readline().strip()

    def string_id_to_id(string_id: str) -> int:
        for (idx, node) in enumerate(instance.nodes):
            if node.string_id == string_id:
                return idx
        raise ValueError(f"Node {string_id} not found")

    return (Solution(routes=[
        [string_id_to_id(string_id) for string_id in route_with_string_ids]
            for route_with_string_ids in routes_with_string_ids
    ]), objective)
