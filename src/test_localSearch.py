import unittest
import random

from src import config

from src.localSearch import (
    best_move,
    remove_empty_route,
    local_search,
)

from src.feasibility import is_feasible
from src.helpers import route_cost
from src.instances import Node, Instance


class TestLocalSearch(unittest.TestCase):

    def setUp(self):
        
        config.RUNS = 1
        config.MAX_LOCAL_IMPROVEMENTS = 3

        random.seed(0)

        self.depot = Node(
            id="D",
            type="d",
            x=0,
            y=0,
            demand=0,
            ready=0,
            due=100,
            service=0,
        )

        self.customer1 = Node(
            id="C1",
            type="c",
            x=2,
            y=0,
            demand=1,
            ready=0,
            due=100,
            service=0,
        )

        self.customer2 = Node(
            id="C2",
            type="c",
            x=4,
            y=0,
            demand=1,
            ready=0,
            due=100,
            service=0,
        )

        self.station = Node(
            id="F1",
            type="f",
            x=3,
            y=0,
            demand=0,
            ready=0,
            due=100,
            service=0,
        )


    def create_instance(self):

        return Instance(
            depot=self.depot,
            customers=[
                self.customer1,
                self.customer2
            ],
            stations=[
                self.station
            ],
            Q=50,
            C=10,
            r=1,
            v=1,
            g=1
        )

    def test_remove_empty_route(self):

        routes = [
            [
                self.depot,
                self.depot
            ],
            [
                self.depot,
                self.customer1,
                self.depot
            ]
        ]

        remove_empty_route(routes)

        self.assertEqual(
            len(routes),
            1
        )

    def test_best_move_returns_route(self):

        inst = self.create_instance()

        route = [
            self.depot,
            self.customer2,
            self.customer1,
            self.depot
        ]

        result = best_move(
            route,
            self.customer1,
            inst,
            len(route),
            ci=2
        )

        self.assertIsNotNone(
            result
        )


    def test_best_move_keeps_feasibility(self):

        inst = self.create_instance()

        route = [
            self.depot,
            self.customer2,
            self.customer1,
            self.depot
        ]

        result = best_move(
            route,
            self.customer1,
            inst,
            len(route),
            ci=2
        )

        is_feasible(
            inst,
            result
        )

    def test_local_search_returns_solution(self):

        inst = self.create_instance()

        routes = [
            [
                self.depot,
                self.customer2,
                self.customer1,
                self.depot
            ]
        ]

        result, costs, times = local_search(
            routes,
            inst
        )

        self.assertIsNotNone(
            result
        )

        self.assertGreater(
            len(costs),
            0
        )

        self.assertGreater(
            len(times),
            0
        )


    def test_local_search_solution_feasible(self):

        inst = self.create_instance()

        routes = [
            [
                self.depot,
                self.customer1,
                self.customer2,
                self.depot
            ]
        ]

        result, _, _ = local_search(
            routes,
            inst
        )

        for route in result:

            is_feasible(
                inst,
                route
            )


    def test_local_search_doesnt_make_cost_worse(self):

        inst = self.create_instance()

        routes = [
            [
                self.depot,
                self.customer2,
                self.customer1,
                self.depot
            ]
        ]

        old_cost = sum(
            route_cost(route)
            for route in routes
        )

        result, _, _ = local_search(
            routes,
            inst
        )

        new_cost = sum(
            route_cost(route)
            for route in result
        )

        self.assertLessEqual(
            new_cost,
            old_cost
        )


if __name__ == "__main__":
    unittest.main()