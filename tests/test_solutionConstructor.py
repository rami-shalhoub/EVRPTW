import os
import sys
import unittest
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import config

from src.solutionConstructor import (
    insert_station,
    route_constructor,
    last_resort,
    greedy_construction,
)

from src.feasibility import is_feasible
from src.instances import Node, Instance


class TestSolutionConstructor(unittest.TestCase):
    def setUp(self):

        config.RUNS = 1
        config.ITERATIONS = 1
        config.STATIONS = 5

        random.seed(0)

        self.depot = Node(
            id="D",
            x=0,
            y=0,
            type="d",
            demand=0,
            ready=0,
            due=100,
            service=0,
        )

        self.customer1 = Node(
            id="C1",
            x=3,
            y=4,
            type="c",
            demand=1,
            ready=0,
            due=100,
            service=0,
        )

        self.customer_far = Node(
            id="C2",
            x=20,
            y=0,
            type="c",
            demand=1,
            ready=0,
            due=100,
            service=0,
        )

        self.station = Node(
            id="F1",
            x=5,
            y=0,
            type="f",
            demand=0,
            ready=0,
            due=100,
            service=0,
        )

    def create_instance(self):

        return Instance(
            depot=self.depot,
            customers=[self.customer1, self.customer_far],
            stations=[self.station],
            Q=50,
            C=10,
            r=1,
            v=1,
            g=1,
        )

    def test_insert_station_adds_station(self):

        inst = self.create_instance()

        route = [self.depot]

        result = insert_station(route, self.customer_far, inst)

        self.assertIn(self.customer_far, result)

        stations = [n for n in result if n.type == "f"]

        self.assertGreaterEqual(len(stations), 1)

    def test_insert_station_returns_new_route(self):

        inst = self.create_instance()

        route = [self.depot]

        result = insert_station(route, self.customer1, inst)

        # Rückgabe ist eine neue Liste
        self.assertIsNot(route, result)

        # Ergebnis enthält den Kunden
        self.assertIn(self.customer1, result)

    def test_route_constructor_adds_customer(self):

        inst = self.create_instance()

        customers = [self.customer1]

        route = route_constructor(customers, inst)

        self.assertIn(self.customer1, route)

    def test_route_constructor_returns_feasible_route(self):

        inst = self.create_instance()

        customers = [self.customer1]

        route = route_constructor(customers, inst)

        is_feasible(inst, route)

    def test_route_constructor_removes_customer(self):

        inst = self.create_instance()

        customers = [self.customer1]

        route_constructor(customers, inst)

        self.assertEqual(len(customers), 0)

    def test_last_resort_adds_customer(self):

        inst = self.create_instance()

        routes = []

        failed_customers = [self.customer1]

        last_resort(routes, failed_customers, inst)

        self.assertEqual(len(routes), 1)

        self.assertIn(self.customer1, routes[0])


if __name__ == "__main__":
    unittest.main()
