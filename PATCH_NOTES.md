# CBMP Day 8 patch notes

This patch updates the main benchmark configuration and report text to reflect the current repository and the 15-run day-8 pilot reported in the terminal.

## Files
- `configs/benchmark.json`: activates the five methods currently dispatched by the runner (`sat_pairwise`, `sat_order`, `cp_sat`, `cplex_mip`, `gurobi_mip`), leaves `cplex_cp` pending, uses the planned 300-second end-to-end limit, and writes to a new output file `results/benchmark_day8.jsonl`.
- `scripts/benchmark.py`: corrects the runner docstring to mention CP-SAT.
- `report/sections/baselines.tex`: documents the implemented CP-SAT model and accurately records that CPLEX CP is still a stub.
- `report/sections/experiments.tex`: replaces outdated pilot claims with the 15-run, five-method pilot outcomes and current dataset limitations.
- `README.md`: corrects the solver availability summary.

## Validation performed on this patch
- `python -m json.tool configs/benchmark.json`
- `python -m py_compile scripts/benchmark.py scripts/plot_results.py`
- `scripts/plot_results.py --check-only` successfully generated CSVs from the pilot JSONL included in the uploaded archive (that archive snapshot contains 6 pilot records, not the newer 15-run log shown in the terminal).

The full figure generation step could not be verified in this environment because the optional `cnsplots` package is not installed here. On Windows, install it with `py -3.14 -m pip install -e ".[plots]"`.

## Important
The current main benchmark intentionally covers five methods. CPLEX CP is pending; CPLEX MIP and Gurobi MIP hit Community/size-limited license restrictions on the non-toy instances. Do not describe this as a completed six-method comparison. The manifest currently contains three verified graphs, not the full 28-candidate Harwell--Boeing set.
