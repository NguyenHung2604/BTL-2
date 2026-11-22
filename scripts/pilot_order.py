from pathlib import Path
import time

from cbmp.encodings import order
from cbmp.graph import load_graph
from cbmp.solvers import cplex_cp

# Thử lấy hàm kiểm tra/tính objective nếu có trong repo
try:
  from cbmp.validator import validate_labels  # đổi tên hàm nếu file dùng tên khác
except ImportError:
  validate_labels = None


def cyclic_dist(a: int, b: int, n: int) -> int:
  d = abs(a - b)
  return min(d, n - d)


def check_manual_cbmp(graph, labels: list[int] | None, k: int) -> tuple[bool, str]:
  if labels is None:
    return False, "labels is None"
  n = graph.n
  if len(labels) != n or sorted(labels) != list(range(n)):
    return False, f"invalid permutation: {labels}"
  max_edge_dist = max((cyclic_dist(labels[u], labels[v], n) for u, v in graph.edges), default=0)
  if max_edge_dist > k:
    return False, f"bandwidth {max_edge_dist} > k={k}"
  return True, f"ok (bw={max_edge_dist})"


def main() -> None:
  data_dir = Path("data/benchmarks/harwell_boeing/graphs")
  sample_files = sorted(data_dir.glob("*.json"))[:3]  # lấy 3 đồ thị đầu tiên để test nhanh
  if not sample_files:
    print("Không tìm thấy file .json nào trong thư mục data/")
    return

  for path in sample_files:
    g = load_graph(path)
    print(f"\n=== Instance: {g.name} (n={g.n}, m={len(g.edges)}) ===")

    # 1. Pilot CPLEX CP
    try:
      cp_res = cplex_cp.solve(g, time_limit_seconds=5.0)
      print(
          f"[CPLEX CP] status={cp_res.status}, reason={cp_res.termination_reason}, "
          f"bw={cp_res.bandwidth}, lb={cp_res.lower_bound}, t={cp_res.runtime_seconds:.3f}s"
      )
      if cp_res.labels is not None and cp_res.bandwidth is not None:
        ok, info = check_manual_cbmp(g, cp_res.labels, cp_res.bandwidth)
        print(f"           check labels: {ok} ({info})")
    except Exception as e:
      print(f"[CPLEX CP] lỗi khi chạy: {type(e).__name__}: {e}")

    # 2. Pilot Order encoding (thử với k = 1 và k = max(1, g.n // 2))
    for k in sorted({1, max(1, g.n // 2)}):
      t0 = time.perf_counter()
      clauses, meta = order.build(g, k)
      dt_build = time.perf_counter() - t0
      num_vars = max((abs(lit) for c in clauses for lit in c), default=0)
      print(f"[Order k={k}] vars={num_vars}, clauses={len(clauses)}, build_time={dt_build:.4f}s")

      # Nếu có cài python-sat (pysat) thì giải thử để test luôn decode
      try:
        from pysat.solvers import Glucose3

        with Glucose3(bootstrap_with=clauses) as solver:
          sat = solver.solve()
          if sat:
            model = solver.get_model()
            labels = order.decode(model, meta)
            ok, info = check_manual_cbmp(g, labels, k)
            print(f"           SAT -> decoded ok={ok} ({info})")
          else:
            print("           UNSAT")
      except ImportError:
        pass


if __name__ == "__main__":
  main()