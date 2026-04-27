# ----------------------------
# Data structures
# ----------------------------
class Node:
    def __init__(
        self,
        id: str,
        x: float,
        y: float,
        demand: float,
        ready: float,
        due: float,
        service: float,
        is_station: bool,
    ):
        self.id = id  # unique node ID
        self.x = x  # x-coordinate
        self.y = y  # y-coordinate
        self.demand = demand  # customer demand (0 for depot/stations)
        self.ready = ready  # earliest service start time (e_i)
        self.due = due  # latest service start time (l_i)
        self.service = service  # service duration at node (s_i)
        self.is_station = is_station  # True if node is a charging station

    @classmethod
    def empty(cls):
        pass


def get_instances(path: str):
    #------------------------------------------------------------------------
    #                              Function Description                              
    '''
    This function takes the path to the instances txt file and return the data
    from type Node  
    '''
    #------------------------------------------------------------------------
    with open(path) as instances:
        customers = list()
        stations = list()
        depot = Node.empty()
        Q = float()
        C = float()
        r = float()
        g = float()
        v = float()
        for line in instances.readlines():
            data = line.split()

            # stop at the empty line
            if not data:
                continue

            match data[1]:
                case "d":
                    depot = Node(
                        data[0],
                        float(data[2]),
                        float(data[3]),
                        float(data[4]),
                        float(data[5]),
                        float(data[6]),
                        float(data[7]),
                        False,
                    )
                case "f":
                    stations.append(
                        Node(
                            data[0],
                            float(data[2]),
                            float(data[3]),
                            float(data[4]),
                            float(data[5]),
                            float(data[6]),
                            float(data[7]),
                            True,
                        )
                    )
                case "c":
                    customers.append(
                        Node(
                            data[0],
                            float(data[2]),
                            float(data[3]),
                            float(data[4]),
                            float(data[5]),
                            float(data[6]),
                            float(data[7]),
                            True,
                        )
                    )
                case "Vehicle":
                    if data[0] == "Q":
                        Q = float(data[5].strip("/"))
                    else:
                        C = float(data[4].strip("/"))
                case "fuel":
                    r = float(data[4].strip("/"))
                case "inverse":
                    g = float(data[4].strip("/"))
                case "average":
                    v = float(data[3].strip("/"))

    return depot, customers, stations, Q, C, r, g, v
