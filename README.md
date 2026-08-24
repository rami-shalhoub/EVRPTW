**Electric-Vehicle Routing Problem with Time Window** (EVRPTW)

## Problem Definition

| Variables|
| ------|
| **complete directed graph** $G = (V, A)$:<br> • nodes $V$:<br>  – customers $c \in V^c$, each customer $i$ has:<br>   ▪ positive demand $q_i$<br>   ▪ service time $s_i$<br>  – charging stations $f \in V^f$<br> • edges $A$: each edge $(i,j) \in A$ has:<br>  – distance $d_{ij}$<br>  – travel time $t_{ij}$ |
| **set of $k$ identical vehicles** $k \in K$:<br> • each vehicle has capacity $C$ and is **fully loaded at the |
| **time window** $[e_i, l_i]$:<br> • service must start within $[e_i, l_i]$ (starts at $e_i$) but can finish later than $l_i$|
| **charging rate** $g$:<br> • $Q$ = maximum battery capacity<br> • current charge $y$<br> • charging time: $g \cdot (Q - y)$ [charging rate × remaining capacity]<br> • at the charging station it charges to **full** (we can visit a station more than once)  |
| **energy consumption rate** $r$:<br> • energy consumption for edge $(i,j)$: $r \cdot d_{ij}$ |

### Goal

Construct routes that:

- serve all customers exactly once
- minimise the total travel distance (reduces the possibility of recharging to increase the range)

### Constraints

- all routes must start and end at the depot
- all customers must be served
- vehicle load capacity
- battery capacity
- battery charge can never fall below zero
- time window constraints

### Assumptions

- flat terrain
- constant travel speed

---

## Instances

| Attribute | Description |
| --- | --- |
| ‘StringID’ | used at the end to show the constructed solution |
| ‘Type’ | used to fast identify the node type (‘d’: depot, ‘f’: charging station, ‘c’: customer) |
| (x, y) | the node coordinates |
| ‘demand’ | how much cargo this node needs |
| ‘ReadyTime’ $e_{i}$ | earliest time the vehicle may arrive at this node. If it arrives earlier, it waits |
| ‘DueDate’ $l_{i}$ | latest time the vehicle may **begin service** at this node. Arriving after this = time window violation |
| ‘ServiceTime’ $s_{i}$ | how long the vehicle spends at the node after arriving (this is **not** the charge time) |

### Data Structure

the data is taken from the instances files and store them in custom data type `Node`

```python
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
```

---

## Implementation

```mermaid
graph TB
    a1(["SEQUENTIAL INSERTION<br>sort by angle insert greedily"])
    a2(["INSERT CHARGING STATION<br>whenever battery would run out"])
    a3(["FEASIBLE SOLUTION<br>all constraints satisfied"])
    a4(["RELOCATE NEIGHBOURHOOD<br>+ forwards/backward slack"])
    a5(["LOCAL OPTIMUM<br>best solution found so far"])

    b1(["INI TEMP T<br>set T0 and cooling rate α"])
    b2(["GENERATE NEIGHBOUR<br>random relocate move"])
    b3{"ACCEPT"}
    b3_1(["Yes"])
    b3_2(["probability e^(-Δ/T)"])
    b4(["Update T ← α·T"])
    b5(["track best solution"])

    c1(["NEIGHBOURHOOD k=1<br>relocate 'cheapest'"])
    c2(["NEIGHBOURHOOD k=2<br>intra-2-opt"])
    c3(["NEIGHBOURHOOD k=3<br>stationInRe EVRPTW_specific"])

    subgraph Task1 [Construction heuristic + local search]
        direction LR
        a1 --> a2 --> a3 --> a4
        a5 -.-> a4 
        a5 -.->|repeat until no improvement| a4
    end

    subgraph Task2 [Simulated Annealing metaheuristic]
        direction LR
        b1 --> b2 --> b3
        b3 -->|if better| b3_1
        b3 -->|no| b3_2
        b3_1 & b3_2 --> b4 --> b5
        b5 -.->|T > T_min| b2
    end

    subgraph Task3 [Advanced: multiple neighbourhoods VNS-style]
        c1 --> c2 --> c3
    end

    Task1 --> Task2 --> Task3
```

## Task 2
    1.	Take Construction heuristic from Task 1  
    2.	Simulated Annealing
     a.	Neighborhood 1: Customer Relocate: select random customer, remove it, insert it in a new position
     b.	Charging Station Repair: Check after each customer relocate if the route is still batteriefeasible  if no then insert cheapest reachable charging station. If the charging station is between two customers and the battery is enough then delete the charging station. Optional: If two stations are possible then select the nearest one

## Task 3:
Several Neighborhoods: 
N1 – Relocate: Move one Customer
N2- Swap: Swap two customers
N3 – Multiple Relocate

Improving Intensification by local search instead of an evaluation after every big change:
Relocate --> 2-Opt --> Charging Station Optimization --> Evaluate

Improving by bigger changes:
Two relocates, more swaps, relocate + station replace


---

## How to Run 

1.  clone the app
    
    ```sh
    git clone https://github.com/rami-shalhoub/EVRPTW.git
    cd ./EVRPTW
    ```
2.  setup python environment
    
    ```sh
    python -m venv .env
    source ./.env/bin/activate
    pip install -r requirements.txt
    ```
3.  run the app
    
    ```sh
    python main.py
    ```
    
    or check the option with `python main.py --help`
4.  check the data
    
    ```sh
    python validate_all.py --solution-dir ./solution --instance-dir ./resources/instances
    ```
5.  run `shiny`
    
    ```sh
    shiny run
    ```