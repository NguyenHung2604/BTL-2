"""Tests for strict benchmark manifest validation."""

import csv
import hashlib
from pathlib import Path

import pytest

from cbmp.manifest import load_manifest

ROOT = Path(__file__).resolve().parents[1]


def test_repository_manifest_verifies_every_raw_and_graph_file():
    rows = load_manifest(ROOT / "data" / "manifest.csv", repo_root=ROOT)
    assert [row["instance"] for row in rows] == ["jgl009", "bcsstk01", "bp___400"]
    assert [(row["n"], row["m"]) for row in rows] == [(9, 32), (48, 176), (822, 4015)]


def test_manifest_rejects_raw_checksum_mismatch(tmp_path):
    raw = tmp_path / "source.hb"
    graph = tmp_path / "graph.json"
    raw.write_bytes(b"original")
    graph.write_text('{"name":"tiny","n":2,"edges":[[0,1]]}\n', encoding="utf-8")
    graph_bytes = graph.read_bytes()
    normalized = hashlib.sha256(b"n=2\n0,1\n").hexdigest()
    fields = [
        "instance", "source_url", "raw_path", "graph_path", "matrix_type", "n", "m",
        "max_degree", "isolated_vertices", "raw_sha256", "graph_sha256", "normalized_graph_sha256",
    ]
    row = {
        "instance": "tiny", "source_url": "https://example.invalid/tiny", "raw_path": "source.hb",
        "graph_path": "graph.json", "matrix_type": "PUA", "n": 2, "m": 1,
        "max_degree": 1, "isolated_vertices": 0,
        "raw_sha256": hashlib.sha256(b"wrong").hexdigest(),
        "graph_sha256": hashlib.sha256(graph_bytes).hexdigest(),
        "normalized_graph_sha256": normalized,
    }
    manifest = tmp_path / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)

    with pytest.raises(ValueError, match="raw_sha256 mismatch"):
        load_manifest(manifest, repo_root=tmp_path)


def test_diagonal_only_matrix_is_documented_as_excluded():
    import csv
    from cbmp.graph import load_graph

    with (ROOT / "data" / "excluded.csv").open(encoding="utf-8", newline="") as stream:
        row = next(csv.DictReader(stream))
    graph = load_graph(ROOT / row["graph_path"])
    assert row["instance"] == "bcsstm01"
    assert (graph.n, len(graph.edges)) == (48, 0)
    assert row["exclusion_reason"] == "edgeless_after_diagonal_removal"
