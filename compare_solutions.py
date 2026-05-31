# %%
import os
import pandas as pd

# %%
solution_folder = "./solution/"
instance_files = [f for f in os.listdir(solution_folder) if f.endswith("_g_solution.txt")]

results: list[tuple[str, float, float, str]] = []

for f in instance_files:
    name = f.replace("_g_solution.txt", "")

    greedy_file = f"{name}_g_solution.txt"
    ls_file = f"{name}_ls_solution.txt"

    if not all(os.path.exists(solution_folder + sf) for sf in [greedy_file , ls_file]):
        print(f"Skipping {name}: missing files")
        continue

    with open(solution_folder + greedy_file) as fh:
        g_cost = float(fh.readlines()[1].strip())
    with open(solution_folder + ls_file) as fh:
        ls_cost = float(fh.readlines()[1].strip())

    costs = {"greedy": g_cost, "ls_new": ls_cost}
    min_val = min(costs.values())
    best = "/".join(sorted(k for k, v in costs.items() if v == min_val))
    # rows.append({"instance": name, **costs, "best": best})
    results.append((name, g_cost, ls_cost, best))
    
print(f"{'Instance':<20} {'Greedy':<14} {'LS (new)':<14} {'Best':<8}")
print("-" * 74)
for name, g, ls, best in sorted(results):
    print(f"{name:<20} {g:<14.3f} {ls:<14.3f} {best:<8}")
    
# %%
df = pd.DataFrame(results, columns=['File', 'Greedy', 'LS2', 'Best'])
df.to_csv("./compared_results.csv", index=False)
