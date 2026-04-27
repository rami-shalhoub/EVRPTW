import math  # provides mathematical functions (used here for distance calculation)





# ----------------------------
# Distance & Travel Time
# ----------------------------

def distance(a, b):
    # compute Euclidean distance between two nodes
    return math.hypot(a.x - b.x, a.y - b.y)

#------------------------------------------
#FIXME          travle distance update               
# ! the travel time should be updates
#------------------------------------------
def travel_time(a, b):
    # travel time between nodes (currently equal to distance)
    return distance(a, b)


# ----------------------------
# Sweep angle (for greedy construction)
# ----------------------------

def compute_angle(depot, node):
    # compute polar angle of a node relative to the depot
    # used for sweep-based clustering
    return math.atan2(node.y - depot.y, node.x - depot.x)


# ----------------------------
# Feasibility check (EVRPTW)
# ----------------------------

def check_feasible(route, Q, C, r, g):
    battery = Q   # vehicle starts with full battery
    load = 0      # current vehicle load
    time = 0      # current time

    # iterate over all edges in the route
    for i in range(len(route) - 1):
        current = route[i]       # current node
        nxt = route[i + 1]       # next node

        dist = distance(current, nxt)      # travel distance
        ttime = travel_time(current, nxt)  # travel time

        # ----------------------------
        # Battery constraint
        # ----------------------------
        battery -= r * dist      # energy consumption
        if battery < 0:          # battery must not go below zero
            return False

        # ----------------------------
        # Time window constraint
        # ----------------------------
        arrival = time + ttime   # arrival time at next node

        # service can only start after ready time
        start_service = max(arrival, nxt.ready)

        # service must start within time window
        if start_service > nxt.due:
            return False

        # update time after service
        time = start_service + nxt.service

        # ----------------------------
        # Capacity constraint
        # ----------------------------
        if not nxt.is_station:       # only customers affect load
            load += nxt.demand
            if load > C:             # capacity exceeded
                return False

        # ----------------------------
        # Charging at station
        # ----------------------------
        if nxt.is_station:
            # time required to fully recharge
            charging_time = g * (Q - battery)

            # add charging time
            time += charging_time

            # reset battery to full
            battery = Q

    return True  # route is feasible if all constraints are satisfied


# ----------------------------
# Nearest charging station
# ----------------------------

def insert_station(current, stations):
    best = None                 # best station found
    best_dist = float('inf')    # initialize with large value

    # iterate over all stations
    for s in stations:
        d = distance(current, s)   # distance to station

        # update if closer station found
        if d < best_dist:
            best_dist = d
            best = s

    return best  # return nearest station


# ----------------------------
# Greedy construction (Sweep-based)
# ----------------------------

def greedy_construction(depot, customers, stations, Q, C, r, g):
    unvisited = customers[:]   # copy list of customers

    # sort customers by polar angle (Sweep heuristic)
    unvisited.sort(key=lambda n: compute_angle(depot, n))

    routes = []  # list of routes

    # continue until all customers are served
    while unvisited:
        route = [depot]   # start route at depot
        current = depot   # current position

        i = 0
        # iterate over unvisited customers
        while i < len(unvisited):
            cust = unvisited[i]

            trial = route + [cust]  # attempt to add customer

            # check feasibility of route including return to depot
            if check_feasible(trial + [depot], Q, C, r, g):
                route.append(cust)       # add customer
                current = cust           # update position
                unvisited.pop(i)         # remove from list
            else:
                # try inserting a charging station
                station = insert_station(current, stations)

                if station:
                    trial = route + [station, cust]

                    # check feasibility with station included
                    if check_feasible(trial + [depot], Q, C, r, g):
                        route.append(station)   # add station
                        route.append(cust)      # add customer
                        current = cust
                        unvisited.pop(i)
                        continue  # re-evaluate same index

                i += 1  # try next customer

        route.append(depot)   # return to depot
        routes.append(route)  # store route

    return routes


# ----------------------------
# Cost functions
# ----------------------------

def route_cost(route):
    # sum of distances along a route
    return sum(distance(route[i], route[i + 1]) for i in range(len(route) - 1))


def total_cost(routes):
    # total distance across all routes
    return sum(route_cost(r) for r in routes)


# ----------------------------
# Local Search (Relocate operator)
# ----------------------------

def local_search(routes, Q, C, r, g):
    improved = True  # flag indicating improvement

    # repeat until no improvement is found
    while improved:
        improved = False

        # iterate over all routes
        for r1 in routes:
            # select a node (exclude depot)
            for i in range(1, len(r1) - 1):
                node = r1[i]

                # try inserting into another route
                for r2 in routes:
                    for j in range(1, len(r2)):

                        # skip trivial moves
                        if r1 == r2 and (j == i or j == i + 1):
                            continue

                        # remove node from r1
                        new_r1 = r1[:i] + r1[i + 1:]

                        # insert node into r2
                        new_r2 = r2[:j] + [node] + r2[j:]

                        # check feasibility of both routes
                        if not check_feasible(new_r1, Q, C, r, g):
                            continue
                        if not check_feasible(new_r2, Q, C, r, g):
                            continue

                        # compute cost difference
                        old_cost = route_cost(r1) + route_cost(r2)
                        new_cost = route_cost(new_r1) + route_cost(new_r2)

                        # accept improvement
                        if new_cost < old_cost:
                            r1[:] = new_r1
                            r2[:] = new_r2
                            improved = True
                            break

                    if improved:
                        break
                if improved:
                    break
            if improved:
                break

    return routes  # return improved solution


# ----------------------------
# Output formatting
# ----------------------------

def format_node(node):
    # format depot
    if node.id == 0:
        return "D0"
    # format charging station
    elif node.is_station:
        return f"S{node.id - 99}"  # e.g. 100 -> S1
    # format customer
    else:
        return f"C{node.id}"


def print_solution(routes):
    # print header (benchmark style)
    print("### Example solution")

    # print total cost (rounded)
    print(round(total_cost(routes), 3))

    # print each route
    for r in routes:
        print(", ".join(format_node(n) for n in r))