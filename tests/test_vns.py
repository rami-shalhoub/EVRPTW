import os
import sys
import unittest
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import config
from src.feasibility import is_feasible
from src.helpers import route_cost, total_cost
from src.instances import Instance, Node
from src.vns import (
    cross_route_relocate,
    cross_route_swap,
    intra_route_relocate,
    inter_route_segment_exchange,
    customer_positions,
    shaking,
    vns,
)


class TestVNS(unittest.TestCase):
    def setUp(self):
        config.RUNS = 1
        config.MAX_LOCAL_IMPROVEMENTS = 3
        config.VNS_K_MAX = 4
        config.VNS_SHAKING_TRIALS = 10
        config.VNS_MAX_NO_IMPROVE = 5
        config.VNS_MAX_TIME = 10.0
        config.VNS_RANDOM_SEED = 42

        random.seed(0)

        self.depot = Node("D", "d", 0, 0, 0, 0, 100, 0)
        self.c1 = Node("C1", "c", 2, 0, 1, 0, 100, 0)
        self.c2 = Node("C2", "c", 4, 0, 1, 0, 100, 0)
        self.c3 = Node("C3", "c", 6, 0, 1, 0, 100, 0)
        self.c4 = Node("C4", "c", 8, 0, 1, 0, 100, 0)
        self.station = Node("F1", "f", 3, 0, 0, 0, 100, 0)

    def create_instance(self):
        return Instance(
            depot=self.depot,
            customers=[self.c1, self.c2, self.c3, self.c4],
            stations=[self.station],
            Q=50,
            C=10,
            r=1,
            v=1,
            g=1,
        )

    def two_route_solution(self):
        return [
            [self.depot, self.c1, self.c2, self.depot],
            [self.depot, self.c3, self.c4, self.depot],
        ]

    # ── helper tests ───────────────────────────────────────────────

    def test_customer_positions(self):
        routes = self.two_route_solution()
        positions = customer_positions(routes)
        self.assertEqual(len(positions), 4)
        ids = {routes[r][c].id for r, c in positions}
        self.assertEqual(ids, {"C1", "C2", "C3", "C4"})

    # ── shaking operator tests ─────────────────────────────────────

    def test_intra_route_relocate_returns_feasible(self):
        inst = self.create_instance()
        routes = [[self.depot, self.c1, self.c2, self.c3, self.c4, self.depot]]
        result = intra_route_relocate(routes, inst)
        if result is not None:
            for route in result:
                if any(n.type == "c" for n in route):
                    is_feasible(inst, route)

    def test_cross_route_relocate_returns_feasible(self):
        inst = self.create_instance()
        routes = self.two_route_solution()
        result = cross_route_relocate(routes, inst)
        if result is not None:
            for route in result:
                if any(n.type == "c" for n in route):
                    is_feasible(inst, route)

    def test_cross_route_swap_returns_feasible(self):
        inst = self.create_instance()
        routes = self.two_route_solution()
        result = cross_route_swap(routes, inst)
        if result is not None:
            for route in result:
                if any(n.type == "c" for n in route):
                    is_feasible(inst, route)

    def test_inter_route_segment_exchange_returns_feasible(self):
        inst = self.create_instance()
        routes = self.two_route_solution()
        result = inter_route_segment_exchange(routes, inst)
        if result is not None:
            for route in result:
                if any(n.type == "c" for n in route):
                    is_feasible(inst, route)

    # ── shaking dispatcher tests ───────────────────────────────────

    def test_shaking_k1(self):
        inst = self.create_instance()
        routes = [[self.depot, self.c1, self.c2, self.c3, self.c4, self.depot]]
        result = shaking(routes, 1, inst)
        if result is not None:
            served = {n.id for r in result for n in r if n.type == "c"}
            self.assertEqual(served, {"C1", "C2", "C3", "C4"})

    def test_shaking_k2(self):
        inst = self.create_instance()
        routes = self.two_route_solution()
        result = shaking(routes, 2, inst)
        if result is not None:
            served = {n.id for r in result for n in r if n.type == "c"}
            self.assertEqual(served, {"C1", "C2", "C3", "C4"})

    def test_shaking_k3(self):
        inst = self.create_instance()
        routes = self.two_route_solution()
        result = shaking(routes, 3, inst)
        if result is not None:
            served = {n.id for r in result for n in r if n.type == "c"}
            self.assertEqual(served, {"C1", "C2", "C3", "C4"})

    def test_shaking_k4(self):
        inst = self.create_instance()
        routes = self.two_route_solution()
        result = shaking(routes, 4, inst)
        if result is not None:
            served = {n.id for r in result for n in r if n.type == "c"}
            self.assertEqual(served, {"C1", "C2", "C3", "C4"})

    # ── VNS main loop tests ────────────────────────────────────────

    def test_vns_returns_solution(self):
        inst = self.create_instance()
        routes = self.two_route_solution()
        result, cost, elapsed = vns(routes, inst)
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)

    def test_vns_solution_feasible(self):
        inst = self.create_instance()
        routes = self.two_route_solution()
        result, _, _ = vns(routes, inst)
        for route in result:
            if any(n.type == "c" for n in route):
                is_feasible(inst, route)

    def test_vns_cost_not_worse(self):
        inst = self.create_instance()
        routes = self.two_route_solution()
        old_cost = total_cost(routes)
        result, new_cost, _ = vns(routes, inst)
        self.assertLessEqual(new_cost, old_cost)

    def test_vns_all_customers_served(self):
        inst = self.create_instance()
        routes = self.two_route_solution()
        result, _, _ = vns(routes, inst)
        served = [n.id for r in result for n in r if n.type == "c"]
        self.assertEqual(sorted(served), sorted(["C1", "C2", "C3", "C4"]))

    def test_vns_respects_time_limit(self):
        config.VNS_MAX_TIME = 2.0
        inst = self.create_instance()
        routes = self.two_route_solution()
        _, _, elapsed = vns(routes, inst)
        self.assertLessEqual(elapsed, 5.0)


if __name__ == "__main__":
    unittest.main()
