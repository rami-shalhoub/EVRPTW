from solver import Node

def create_test_instance():
    depot = Node(0, 0, 0)

    customers = [
        Node(1, 2, 3, demand=1, ready=0, due=50, service=1),
        Node(2, 5, 2, demand=1, ready=0, due=50, service=1),
        Node(3, -3, 4, demand=1, ready=0, due=50, service=1),
        Node(4, -4, -2, demand=1, ready=0, due=50, service=1),
        Node(5, 3, -3, demand=1, ready=0, due=50, service=1),
    ]

    stations = [
        Node(100, 1, 1, is_station=True),
        Node(101, -2, 1, is_station=True),
    ]

    return depot, customers, stations