"""Strict validation for the repository's normalized benchmark manifest."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any

from .graph import load_graph

REQUIRED_COLUMNS = {
    "instance",
    "source_url",
    "raw_path",
    "graph_path",
    "matrix_type",
    "n",
    "m",
    "max_degree",
    "isolated_vertices",
    "raw_sha256",
    "graph_sha256",
    "normalized_graph_sha256",
}


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_graph_sha256(n: int, edges: tuple[tuple[int, int], ...]) -> str:
    payload = f"n={n}\n" + "".join(f"{u},{v}\n" for u, v in edges)
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def graph_statistics(n: int, edges: tuple[tuple[int, int], ...]) -> dict[str, int]:
    degrees = [0] * n
    for u, v in edges:
        degrees[u] += 1
        degrees[v] += 1
    return {
        "n": n,
        "m": len(edges),
        "max_degree": max(degrees, default=0),
        "isolated_vertices": sum(degree == 0 for degree in degrees),
    }


def load_manifest(
    manifest_path: str | Path,
    *,
    repo_root: str | Path | None = None,
    verify: bool = True,
) -> list[dict[str, Any]]:
    """Load rows and, by default, verify raw/graph hashes and graph statistics.

    Paths in the CSV are always interpreted relative to ``repo_root`` (or the
    parent of the manifest's ``data`` directory when omitted).
    """
    manifest = Path(manifest_path).resolve()
    root = Path(repo_root).resolve() if repo_root is not None else manifest.parent.parent
    with manifest.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = set(reader.fieldnames or ())
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(f"Manifest is missing columns: {', '.join(sorted(missing))}")
        rows = list(reader)

    if not rows:
        raise ValueError(f"Manifest contains no instances: {manifest}")

    seen: set[str] = set()
    validated: list[dict[str, Any]] = []
    for line_number, row in enumerate(rows, start=2):
        instance = row["instance"].strip()
        if not instance or instance in seen:
            raise ValueError(f"Manifest line {line_number}: empty or duplicate instance {instance!r}")
        seen.add(instance)

        try:
            expected = {
                key: int(row[key])
                for key in ("n", "m", "max_degree", "isolated_vertices")
            }
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Manifest line {line_number}: invalid integer statistic") from exc

        raw_path = (root / row["raw_path"]).resolve()
        graph_path = (root / row["graph_path"]).resolve()
        if not raw_path.is_relative_to(root) or not graph_path.is_relative_to(root):
            raise ValueError(f"Manifest line {line_number}: paths must stay inside the repository")
        if not raw_path.is_file() or not graph_path.is_file():
            missing_path = raw_path if not raw_path.is_file() else graph_path
            raise FileNotFoundError(f"Manifest line {line_number}: missing file {missing_path}")

        graph = load_graph(graph_path)
        actual = graph_statistics(graph.n, graph.edges)
        actual_normalized_hash = normalized_graph_sha256(graph.n, graph.edges)
        if graph.name != instance:
            raise ValueError(f"Manifest line {line_number}: graph name {graph.name!r} != {instance!r}")

        if verify:
            actual_raw_hash = sha256_file(raw_path)
            actual_graph_hash = sha256_file(graph_path)
            checks = {
                "raw_sha256": actual_raw_hash,
                "graph_sha256": actual_graph_hash,
                "normalized_graph_sha256": actual_normalized_hash,
            }
            for field, value in checks.items():
                if row[field].strip().lower() != value:
                    raise ValueError(
                        f"Manifest line {line_number}: {field} mismatch for {instance}; "
                        f"expected {row[field]}, got {value}"
                    )
            for field, value in expected.items():
                if actual[field] != value:
                    raise ValueError(
                        f"Manifest line {line_number}: {field} mismatch for {instance}; "
                        f"expected {value}, got {actual[field]}"
                    )

        validated.append({
            **row,
            "instance": instance,
            **actual,
            "raw_path": row["raw_path"].strip(),
            "graph_path": row["graph_path"].strip(),
            "raw_sha256": row["raw_sha256"].strip().lower(),
            "graph_sha256": row["graph_sha256"].strip().lower(),
            "normalized_graph_sha256": actual_normalized_hash,
        })
    return validated
