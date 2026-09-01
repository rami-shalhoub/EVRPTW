"""Compare greedy vs LS / SA / SA_ext on best_cost and report best/worst improvement."""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "summary_results.csv")


def load(filepath):
    rows = {}
    with open(filepath) as f:
        for r in csv.DictReader(f):
            rows.setdefault(r["instance"], {})[r["algorithm"]] = float(r["best_cost"])
    return rows


def main():
    rows = load(RESULTS)
    for algo, label in [("ls", "LS"), ("sa", "SA"), ("sa_ext", "SA_ext")]:
        deltas = []
        for inst, algos in rows.items():
            if "greedy" in algos and algo in algos:
                deltas.append((inst, algos["greedy"] - algos[algo]))
        if not deltas:
            print(f"task ({label}): no data")
            continue
        best = max(deltas, key=lambda x: x[1])
        worst = min(deltas, key=lambda x: x[1])
        print(f"task ({label}):")
        print(f"  best improvement:  {best[0]} (Δ={best[1]:.1f})")
        print(f"  worst improvement: {worst[0]} (Δ={worst[1]:.1f})")
        print()


if __name__ == "__main__":
    main()
