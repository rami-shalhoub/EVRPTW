import unittest

from .feasibility import (
    is_feasible,
    BatteryError,
    TimeWindowError,
    CapacityError,
)

from .instances import Node, Instance


class TestFeasibility(unittest.TestCase):

    def setUp(self):

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

        self.customer = Node(
            id="C1",
            x=3,
            y=4,
            type="c",
            demand=5,
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


    def create_instance(self, Q=100, C=20):

        return Instance(
            depot=self.depot,
            customers=[self.customer],
            stations=[self.station],
            Q=Q,
            C=C,
            r=1,
            v=1,
            g=1,
        )

    def test_feasible_route(self):

        inst = self.create_instance()

        route = [
            self.depot,
            self.customer,
            self.depot,
        ]

        result = is_feasible(inst, route)

        self.assertIsNone(result)

    def test_battery_error(self):

        # Distanz Depot -> Kunde = 5
        # Batterie nur 4 -> Fehler

        inst = self.create_instance(Q=4)

        route = [
            self.depot,
            self.customer,
        ]

        with self.assertRaises(BatteryError) as error:

            is_feasible(inst, route)


        self.assertEqual(
            error.exception.current,
            self.depot
        )

        self.assertEqual(
            error.exception.next,
            self.customer
        )

        self.assertEqual(
            error.exception.route_index,
            0
        )

        self.assertEqual(
            error.exception.edge_index,
            0
        )

    def test_time_window_error(self):

        late_customer = Node(
            id="late",
            x=10,
            y=0,
            type="c",
            demand=1,
            ready=0,
            due=5,
            service=0,
        )

        inst = self.create_instance()

        route = [
            self.depot,
            late_customer,
        ]


        with self.assertRaises(TimeWindowError) as error:

            is_feasible(inst, route)


        self.assertEqual(
            error.exception.node,
            late_customer
        )

        self.assertEqual(
            error.exception.route_index,
            0
        )

        self.assertEqual(
            error.exception.edge_index,
            0
        )

    def test_capacity_error(self):

        heavy_customer = Node(
            id="heavy",
            x=1,
            y=0,
            type="c",
            demand=50,
            ready=0,
            due=100,
            service=0,
        )


        inst = self.create_instance(C=10)

        route = [
            self.depot,
            heavy_customer,
        ]


        with self.assertRaises(CapacityError) as error:

            is_feasible(inst, route)


        self.assertEqual(
            error.exception.node,
            heavy_customer
        )

        self.assertEqual(
            error.exception.load,
            50
        )

        self.assertEqual(
            error.exception.capacity,
            10
        )

    def test_charging_station_resets_battery(self):

        inst = self.create_instance(Q=10)


        customer2 = Node(
            id="C2",
            x=8,
            y=0,
            type="c",
            demand=1,
            ready=0,
            due=100,
            service=0,
        )


        route = [
            self.depot,
            self.customer,
            self.station,
            customer2,
        ]

        result = is_feasible(inst, route)

        self.assertIsNone(result)


    def test_multiple_routes(self):

        inst = self.create_instance()

        route1 = [
            self.depot,
            self.customer,
            self.depot,
        ]

        route2 = [
            self.depot,
            self.customer,
            self.depot,
        ]


        result = is_feasible(
            inst,
            route1,
            route2
        )


        self.assertIsNone(result)



if __name__ == "__main__":
    unittest.main()