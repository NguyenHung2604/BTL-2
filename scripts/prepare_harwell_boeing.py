"""Normalize a Matrix Market or Harwell–Boeing sparse matrix into CBMP JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cbmp.graph import Graph  # noqa: E402
from cbmp.harwell_boeing import read_harwell_boeing, read_matrix  # noqa: E402


def load_matrix_graph(raw_path: Path) -> Graph:
    """Dispatch by file extension and retain isolated vertices."""
    lower_name = raw_path.name.lower()
    if lower_name.endswith((".mtx", ".mtx.gz")):
        graph = read_matrix(raw_path)
        return Graph(raw_path.name.removesuffix(".gz").removesuffix(".mtx"), graph.n, graph.edges)

    hb = read_harwell_boeing(raw_path)
    name = raw_path.name.removesuffix(".gz")
    for suffix in (".rsa", ".rua", ".pua", ".rse", ".cua", ".psa"):
        if name.lower().endswith(suffix):
            name = name[:-len(suffix)]
            break
    return Graph(name, hb.n, hb.edges)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_path", type=Path)
    parser.add_argument("graph_path", type=Path)
    args = parser.parse_args()

    graph = load_matrix_graph(args.raw_path)
    args.graph_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"name": graph.name, "n": graph.n, "edges": [list(edge) for edge in graph.edges]}
    args.graph_path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"{graph.name}: n={graph.n}, m={len(graph.edges)} -> {args.graph_path}")


if __name__ == "__main__":
    main()
