# %%
"""
Validate existing solution files against the pyEVRPVerifier.
Usage:
    python validate_all.py [--solution-dir ./solution] [--instance-dir ./resources/instances]
"""
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent

VERIFIER_DIR = (
    Path.home()
    / "Documents"
    / "MSc AI"
    / "Computational Logistics"
    / "Project"
    / "pyEVRPVerifier"
)
VERIFIER_VENV = VERIFIER_DIR / ".venv" / "bin" / "python3"
VERIFIER_SCRIPT = VERIFIER_DIR / "src" / "main.py"

# %%
def run_verifier(instance_path: str, solution_path: str) -> str:
    python = VERIFIER_VENV if VERIFIER_VENV.exists() else "python3"
    result = subprocess.run(
        [str(python), str(VERIFIER_SCRIPT),
         "--instance", instance_path,
         "--solution", solution_path],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.stdout + result.stderr


def parse_verdict(output: str) -> tuple[str, float | None]:
    status = "ERROR"
    objective = None
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("Validation result:"):
            raw = line.split(":", 1)[1].strip()
            status = raw.replace("ValidationStatus.", "")
        if line.startswith("- Objective:"):
            try:
                objective = float(line.split(":")[1].strip())
            except ValueError:
                pass
    return status, objective


def find_matching_instance(solution_path: Path, instance_dir: Path) -> Path | None:
    # solution names: c103_21_solution.txt, c103_21_g_solution.txt, etc.
    # Strip trailing _solution and any _g/_ls/_ls2 suffix to get the instance name.
    stem = solution_path.stem
    if stem.endswith("_solution"):
        stem = stem[:-len("_solution")]
    for suffix in ("_g", "_ls2", "_ls", "_ls_main"):
        if stem.endswith(suffix):
            stem = stem[:-len(suffix)]
            break
    candidates = list(instance_dir.glob(f"{stem}.txt"))
    return candidates[0] if candidates else None

# %%
def main():
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Validate EVRPTW solutions")
    parser.add_argument("--solution-dir", default=PROJECT_DIR / "solution",
                        help="Directory containing solution files (*_solution.txt)")
    parser.add_argument("--instance-dir", default=PROJECT_DIR / "resources" / "instances",
                        help="Directory containing instance files (*.txt)")
    args = parser.parse_args()

    solution_dir = Path(args.solution_dir)
    instance_dir = Path(args.instance_dir)

    if not solution_dir.is_dir():
        print(f"Solution directory not found: {solution_dir}")
        sys.exit(1)

    solution_files = sorted(solution_dir.glob("*_solution.txt"))
    if not solution_files:
        print(f"No solution files (*_solution.txt) found in {solution_dir}")
        sys.exit(1)

    results = []

    print(f"{'Name':<20} {'Verdict':<20} {'Objective':>10}")
    print("-" * 55)

    for spath in solution_files:
        name = spath.stem.replace("_solution", "")
        ipath = find_matching_instance(spath, instance_dir)
        if ipath is None:
            print(f"{name:<20} {'NO INSTANCE':<20} {'-':>10}")
            continue

        output = run_verifier(str(ipath), str(spath))
        status, obj = parse_verdict(output)
        obj_str = f"{obj:.2f}" if obj is not None else "-"
        results.append((name, status, obj))
        print(f"{name:<20} {status:<20} {obj_str:>10}")

    feasible = [r for r in results if r[1] == "FEASIBLE"]
    infeasible = [r for r in results if r[1] != "FEASIBLE"]
    print()
    print(f"Total: {len(results)}  |  Feasible: {len(feasible)}  |  Infeasible: {len(infeasible)}")
    if infeasible:
        print("\nInfeasible:")
        for r in infeasible:
            print(f"  {r[0]}  status={r[1]}")

# %%
if __name__ == "__main__":
    main()
