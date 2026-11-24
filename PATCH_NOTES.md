# Patch notes — synchronized six-method results

This patch reconciles the report and handoff text with the archived benchmark
records in `results/raw/six_method_benchmark.jsonl`.

## Changes in this revision

- `report/sections/ninh_hung_results.tex`: replaced the stale five-method,
  300-second narrative with the actual six-method, 18-record batch; retained
  the shared MIP model-size analysis; distinguished optimality proofs,
  feasible incumbents at timeout, CPLEX license errors, and preflight guards.
- `report/sections/experiments.tex`: retained the historical five-method,
  60-second pilot as a separate experiment and corrected the main-batch
  cross-reference and record count.
- `report/main.tex`: removed the duplicated six-method narrative so the
  generated six-method table is included only once; the detailed interpretation
  now lives with Hưng's results section.
- `report/sections/six_method_table.tex`: retained as the generated six-method
  outcome table; the detailed discussion is in `ninh_hung_results.tex`.

## Source of truth and interpretation

- Main benchmark: `results/raw/six_method_benchmark.jsonl` (18 records: three
  graphs by six methods; 300-second target; one requested thread).
- Historical five-method, 300-second batch:
  `results/benchmark_day8.jsonl` (15 records).
- Historical five-method, 60-second pilot: `results/pilot_day8.jsonl`
  (15 records). Neither historical batch replaces the current six-method
  main batch.
- Verified graph manifest: three graphs only; the 28-item paper candidate
  list is not a claim that all 28 graphs were downloaded and verified.
- CPLEX MIP Community Edition license errors and SAT/MIP preflight size
  rejections are not timeouts, infeasibility results, or optimizer outcomes.
- The six-method log records benchmark commit
  `9df7be63e3a7c843c8b1eae836ef4fe3c440351d`; this is provenance for that
  run, not proof of the current source snapshot's Git commit.

## Validation scope

The raw benchmark JSONL, manifest, solver outputs, and generated figures
were not modified or rerun. `plot_results.py --check-only --verify-runs`
completed successfully and regenerated the summary CSVs and six-method
LaTeX table from the archived log. The focused tests
`test_plot_results.py`, `test_benchmark_runner.py`, and `test_manifest.py`
passed (16 tests). A `pdflatex` source pass produced a 9-page draft, but
citations remain unresolved because BibTeX is unavailable in this
environment (cross-references resolved on the second pass). Therefore
`report/main.pdf` was deliberately not replaced; rebuild the complete PDF on
Overleaf or a machine with BibTeX before submission.
