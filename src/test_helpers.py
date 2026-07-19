import unittest
from src.helpers import dist, travel_time, consumed_energy, update_battery, calculate_battery_consumption, charge_time, route_cost, total_cost

class TestHelpers(unittest.TestCase):
    def setUp(self):
        # Create some sample nodes for testing
        self.node_a = type('Node', (object,), {'x': 0, 'y': 0, 'type': 'c'})()
        self.node_b = type('Node', (object,), {'x': 3, 'y': 4, 'type': 'c'})()
        self.node_c = type('Node', (object,), {'x': 6, 'y': 8, 'type': 'f'})()
        self.instance = type('Instance', (object,), {'Q': 100, 'r': 1})()

    def test_dist(self):
        self.assertAlmostEqual(dist(self.node_a, self.node_b), 5.0)

    def test_travel_time(self):
        self.assertAlmostEqual(travel_time(self.node_a, self.node_b, 1), 5.0)

    def test_consumed_energy(self):
        self.assertAlmostEqual(consumed_energy(self.node_a, self.node_b, 1), 5.0)

    def test_update_battery(self):
        current_battery = 10
        new_battery = update_battery(self.node_a, self.node_b, 1, current_battery)
        self.assertAlmostEqual(new_battery, 5.0)

    def test_calculate_battery_consumption(self):
        route = [self.node_a, self.node_b]
        battery_consumption = calculate_battery_consumption(route, self.instance)
        self.assertAlmostEqual(battery_consumption, 95.0)  # Battery should reset at node_c

    def test_charge_time(self):
        current_battery = 50
        charge_time_value = charge_time(current_battery, self.instance.Q, 2)
        self.assertAlmostEqual(charge_time_value, 100.0)  # Time to charge from 50 to full at rate g=2

    def test_route_cost(self):
        route = [self.node_a, self.node_b]
        cost = route_cost(route)
        self.assertAlmostEqual(cost, 5.0)

    def test_total_cost(self):
        routes = [[self.node_a, self.node_b], [self.node_b, self.node_c]]
        total_cost_value = total_cost(routes)
        expected_cost = dist(self.node_a, self.node_b) + dist(self.node_b, self.node_c)
        self.assertAlmostEqual(total_cost_value, expected_cost)