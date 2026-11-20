"""Pure threshold encoding. Positive y[v,t] means labels[v] <= t."""

from collections.abc import Sequence
from itertools import combinations
from typing import TypedDict

from ..graph import Graph
from ..objective import cyclic_distance


<<<<<<< HEAD
def build(graph: Graph, k: int) -> tuple[list[list[int]], dict[str, Any]]:
  """Return signed-integer CNF clauses for bandwidth <= k and decoding metadata."""
  # Lấy số đỉnh và danh sách cạnh (điều chỉnh lại nếu graph.py đặt tên khác, vd: graph.num_vertices)
  n: int = graph.n
  edges = graph.edges

  clauses: list[list[int]] = []

  # Nếu n <= 1, bài toán tầm thường (băng thông luôn bằng 0 <= k)
  if n <= 1:
    return clauses, {"n": n, "var_map": {}}

  # 1. Ánh xạ biến Order Encoding:
  # Biến x[u][p] đại diện cho mệnh đề: (vị trí của đỉnh u <= p), với p chạy từ 0 đến n - 2.
  # (Hiển nhiên vị trí của u <= n - 1 luôn True nên không cần tạo biến).
  var_map: dict[tuple[int, int], int] = {}
  next_var = 1
  for u in range(n):
    for p in range(n - 1):
      var_map[(u, p)] = next_var
      next_var += 1

  def get_le(u: int, p: int) -> int | bool:
    """Trả về literal cho (pos[u] <= p), hoặc hằng số True/False nếu vượt biên."""
    if p < 0:
      return False
    if p >= n - 1:
      return True
    return var_map[(u, p)]

  def add_clause(lits: list[int | bool]) -> None:
    """Tự động rút gọn mệnh đề chứa hằng số True/False trước khi thêm vào CNF."""
    cleaned: list[int] = []
    for lit in lits:
      if lit is True:
        return  # Mệnh đề luôn đúng -> bỏ qua
      if lit is not False:
        cleaned.append(lit)
    clauses.append(cleaned)

  # 2. Ràng buộc đơn điệu (Monotonicity): (pos[u] <= p) => (pos[u] <= p + 1)
  for u in range(n):
    for p in range(n - 2):
      clauses.append([-var_map[(u, p)], var_map[(u, p + 1)]])

  # 3. Ràng buộc song ánh / khác vị trí (All-Different):
  # Hai đỉnh phân biệt u != v không thể cùng nhận giá trị p (với p từ 0 đến n - 1).
  # Điều kiện (pos[u] == p) tương đương: (pos[u] <= p) AND NOT (pos[u] <= p - 1).
  # Do đó, cấm cả u và v cùng bằng p: NOT(pos[u] == p) OR NOT(pos[v] == p)
  for p in range(n):
    for u in range(n):
      for v in range(u + 1, n):
        # Lits đại diện cho việc u KHÔNG nằm ở p: NOT(u <= p) OR (u <= p - 1)
        u_not_p = [-get_le(u, p) if isinstance(get_le(u, p), int) else not get_le(u, p), get_le(u, p - 1)]
        v_not_p = [-get_le(v, p) if isinstance(get_le(v, p), int) else not get_le(v, p), get_le(v, p - 1)]
        add_clause(u_not_p + v_not_p)

  # 4. Ràng buộc khoảng cách vòng (Cyclic Distance <= k) cho mỗi cạnh (u, v):
  # Khoảng cách vòng d_c(pos[u], pos[v]) > k khi và chỉ khi hiệu d = |pos[u] - pos[v]|
  # rơi vào tập giá trị cấm: {k + 1, k + 2, ..., n - k - 1}.
  # Ta cấm mọi cặp vị trí (p_u, p_v) có khoảng cách vòng > k:
  # NOT(pos[u] == p_u) OR NOT(pos[v] == p_v)
  if k < n // 2:
    for u, v in edges:
      for p_u in range(n):
        for p_v in range(n):
          diff = abs(p_u - p_v)
          cyclic_dist = min(diff, n - diff)
          if cyclic_dist > k:
            u_not_pu = [
                -get_le(u, p_u) if isinstance(get_le(u, p_u), int) else not get_le(u, p_u),
                get_le(u, p_u - 1),
            ]
            v_not_pv = [
                -get_le(v, p_v) if isinstance(get_le(v, p_v), int) else not get_le(v, p_v),
                get_le(v, p_v - 1),
            ]
            add_clause(u_not_pu + v_not_pv)

  metadata: dict[str, Any] = {
      "n": n,
      "var_map": var_map,
  }
  return clauses, metadata


def decode(model: Sequence[int], metadata: dict[str, Any]) -> list[int]:
  """Map a satisfying signed-literal model and build metadata to positions labels[v]."""
  n: int = metadata["n"]
  if n <= 0:
    return []
  if n == 1:
    return [0]

  var_map: dict[tuple[int, int], int] = metadata["var_map"]
  true_vars = {lit for lit in model if lit > 0}

  labels: list[int] = []
  for u in range(n):
    # Tìm giá trị p nhỏ nhất (từ 0 đến n - 2) mà biến (pos[u] <= p) là True.
    # Nếu tất cả đều False thì vị trí của u là n - 1.
    pos = n - 1
    for p in range(n - 1):
      if var_map[(u, p)] in true_vars:
        pos = p
        break
    labels.append(pos)

  return labels
=======
class OrderMetadata(TypedDict):
    n: int
    var_map: dict[tuple[int, int], int]


def threshold(v: int, t: int, n: int) -> int:
    return 1 + v * (n - 1) + t


def different_from(v: int, i: int, n: int) -> list[int]:
    """Encode p[v] != i as p[v] <= i-1 OR p[v] > i, omitting false boundary terms."""
    literals = []
    if i > 0:
        literals.append(threshold(v, i - 1, n))
    if i < n - 1:
        literals.append(-threshold(v, i, n))
    return literals


def build(graph: Graph, k: int) -> tuple[list[list[int]], OrderMetadata]:
    """Monotone chains select one position. Forbid collisions and distant edge pairs."""
    n = graph.n
    var_map = {(v, t): threshold(v, t, n) for v in graph.vertices for t in range(n - 1)}
    metadata: OrderMetadata = {"n": n, "var_map": var_map}
    if k < 0:
        return [[]], metadata
    clauses = [
        [-var_map[v, t], var_map[v, t + 1]]
        for v in graph.vertices for t in range(n - 2)
    ]
    for u, v in combinations(graph.vertices, 2):
        for i in range(n):
            clauses.append(different_from(u, i, n) + different_from(v, i, n))
    if k < n // 2:
        for u, v in graph.edges:
            for i in range(n):
                for j in range(n):
                    if cyclic_distance(i, j, n) > k:
                        clauses.append(different_from(u, i, n) + different_from(v, j, n))
    return clauses, metadata


def decode(model: Sequence[int], metadata: OrderMetadata | dict[str, int]) -> list[int]:
    """Return the first true threshold in each chain, or n-1 for an all-false chain."""
    n = metadata["n"]
    positive = {lit for lit in model if lit > 0}
    var_map = metadata.get("var_map")
    if var_map is None:  # Earlier build() results stored only n.
        var_map = {(v, t): threshold(v, t, n) for v in range(n) for t in range(n - 1)}
    return [next((t for t in range(n - 1) if var_map[v, t] in positive), n - 1)
            for v in range(n)]
>>>>>>> 2de39700b4b3275def1c54556981016019170898
