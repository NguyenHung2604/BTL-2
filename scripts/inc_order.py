from pathlib import Path
import time

from cbmp.encodings import order
from cbmp.graph import load_graph
from cbmp.solvers import cplex_cp
from pysat.solvers import Glucose3


def cyclic_dist(a: int, b: int, n: int) -> int:
  d = abs(a - b)
  return min(d, n - d)


def is_valid_cbmp(graph, labels: list[int], k: int) -> bool:
  n = graph.n
  if len(labels) != n or sorted(labels) != list(range(n)):
    return False
  return all(cyclic_dist(labels[u], labels[v], n) <= k for u, v in graph.edges)


def find_min_k_linear(graph):
  n = graph.n
  t0 = time.perf_counter()
  for k in range(0, n // 2 + 1):
    clauses, meta = order.build(graph, k)
    with Glucose3(bootstrap_with=clauses) as solver:
      if solver.solve():
        labels = order.decode(solver.get_model(), meta)
        elapsed = time.perf_counter() - t0
        return k, labels, is_valid_cbmp(graph, labels, k), elapsed
  return None, None, False, time.perf_counter() - t0


def main() -> None:
  files = sorted(Path("data/toy").glob("*.json"))
  if not files:
    print("Không tìm thấy file .json trong data/toy/")
    return

  for p in files:
    g = load_graph(p)
    k_star, labels, valid, dt = find_min_k_linear(g)
    print(f"[Order SAT] {p.name} (n={g.n}, m={len(g.edges)}) -> min_k={k_star}, valid={valid}, t={dt:.4f}s")
    print(f"            labels={labels}")

    try:
      cp_res = cplex_cp.solve(g, time_limit_seconds=5.0)
      print(f"[CPLEX CP ] {p.name} -> bw={cp_res.bandwidth}, status={cp_res.status}, t={cp_res.runtime_seconds:.4f}s")
    except Exception as e:
      print(f"[CPLEX CP ] lỗi: {type(e).__name__}: {e}")


if __name__ == "__main__":
  main()