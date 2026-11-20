"""cplex_cp solver adapter."""

import time
from docplex.cp.model import CpoModel

from ..graph import Graph
from ..result import SolveResult


def solve(graph: Graph, time_limit_seconds: float) -> SolveResult:
  """Optimize graph under one wall-clock budget and return bounds and any incumbent."""
  start = time.perf_counter()
  n = graph.n
  edges = graph.edges

  if n <= 0:
    return SolveResult(
        instance=graph.name,
        method="cplex_cp",
        status="optimal",
        termination_reason="optimal",
        runtime_seconds=time.perf_counter() - start,
        labels=[],
        bandwidth=0,
        lower_bound=0,
    )

  if n == 1:
    return SolveResult(
        instance=graph.name,
        method="cplex_cp",
        status="optimal",
        termination_reason="optimal",
        runtime_seconds=time.perf_counter() - start,
        labels=[0],
        bandwidth=0,
        lower_bound=0,
    )

  mdl = CpoModel(name="CBMP_CP")

  # Vị trí nhãn của từng đỉnh u in [0..n-1], nhận giá trị trong [0..n-1]
  pos = [mdl.integer_var(0, n - 1, name=f"pos_{u}") for u in range(n)]
  mdl.add(mdl.all_diff(pos))

  max_bw = n // 2
  bw = mdl.integer_var(0, max_bw, name="cyclic_bandwidth")

  for u, v in edges:
    diff = mdl.abs(pos[u] - pos[v])
    cyclic_dist = mdl.min(diff, n - diff)
    mdl.add(cyclic_dist <= bw)

  mdl.add(mdl.minimize(bw))

  sol = mdl.solve(
      TimeLimit=max(0.01, float(time_limit_seconds)),
      trace_log=False,
  )
  elapsed = time.perf_counter() - start

  labels: list[int] | None = None
  bandwidth: int | None = None
  lower_bound: int | None = None

  if sol:
    obj_val = sol.get_objective_value()
    if obj_val is not None:
      bandwidth = int(round(obj_val))
      labels = [int(sol[pos[u]]) for u in range(n)]

    # Lấy lower bound nếu solver có cung cấp, fallback về bandwidth nếu tối ưu
    if hasattr(sol, "get_objective_bound") and sol.get_objective_bound() is not None:
      lower_bound = int(sol.get_objective_bound())

    cpo_status = (sol.get_solve_status() or "").lower()
    if "optimal" in cpo_status:
      status = "optimal"
      termination_reason = "optimal"
      if bandwidth is not None and lower_bound is None:
        lower_bound = bandwidth
    elif "feasible" in cpo_status:
      status = "feasible"
      termination_reason = "time_limit"
    else:
      status = "infeasible" if "infeasible" in cpo_status else "unknown"
      termination_reason = cpo_status or "unknown"
  else:
    status = "unknown"
    termination_reason = "no_solution"

  return SolveResult(
      instance=graph.name,
      method="cplex_cp",
      status=status,
      termination_reason=termination_reason,
      runtime_seconds=elapsed,
      labels=labels,
      bandwidth=bandwidth,
      lower_bound=lower_bound,
  )