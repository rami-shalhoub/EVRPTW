from dataclasses import dataclass


# ----------------------------
# Data structures
# ----------------------------
@dataclass()
class Node:
    id: str
    type : str
    x: float
    y: float
    demand: float
    ready: float
    due: float
    service: float
    
    @classmethod
    def empty(cls):
        return cls("", "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

@dataclass
class Instance:
    depot: Node
    customers: list[Node]
    stations: list[Node]
    Q: float   # battery capacity
    C: float   # load capacity
    r: float   # energy consumption rate
    g: float   # inverse refueling rate
    v: float   # velocity


#==============================Extract Instances==============================
def get_instances(path: str):
    #------------------------------------------------------------------------
    #                              Function Description                              
    '''
    Return the data from an instances txt file parsed into: \n
    • depot \n
    • list of customers \n
    • list of charging stations \n
    • Q = Vehicle fuel tank capacity \n
    • C = Vehicle load capacity \n
    • r = fuel consumption rate \n 
    • g = inverse refueling rate \n
    • v = average Velocity \n

    '''
    #------------------------------------------------------------------------
    with open(path) as instances:
        customers:list[Node] = list()
        stations:list[Node] = list()
        depot:Node  = Node.empty()
        Q = C = r = g = v = float()
        for line in instances.readlines():
            data = line.split()

            # stop at the empty line
            if not data:
                continue

            match data[1]:
                case "d":
                    depot = Node(
                        data[0],
                        data[1],
                        float(data[2]),
                        float(data[3]),
                        float(data[4]),
                        float(data[5]),
                        float(data[6]),
                        float(data[7]),
                    )
                case "f":
                    stations.append(
                        Node(
                            data[0],
                            data[1],
                            float(data[2]),
                            float(data[3]),
                            float(data[4]),
                            float(data[5]),
                            float(data[6]),
                            float(data[7]),
                        )
                    )
                case "c":
                    customers.append(
                        Node(
                            data[0],
                            data[1],
                            float(data[2]),
                            float(data[3]),
                            float(data[4]),
                            float(data[5]),
                            float(data[6]),
                            float(data[7]),
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

    return Instance(depot, customers, stations, Q, C, r, g, v)
