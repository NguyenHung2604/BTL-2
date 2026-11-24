"""Verify source hashes, normalized graph hashes and manifest statistics."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cbmp.manifest import load_manifest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=REPO_ROOT / "data" / "manifest.csv")
    args = parser.parse_args()
    manifest_path = args.manifest if args.manifest.is_absolute() else REPO_ROOT / args.manifest
    rows = load_manifest(manifest_path, repo_root=REPO_ROOT)
    excluded_path = REPO_ROOT / "data" / "excluded.csv"
    excluded_rows = load_manifest(excluded_path, repo_root=REPO_ROOT) if excluded_path.is_file() else []
    print(f"Validated {len(rows)} benchmark instance(s):")
    for row in rows:
        density = 0.0 if row["n"] < 2 else row["m"] / (row["n"] * (row["n"] - 1) / 2)
        print(
            f"  {row['instance']}: n={row['n']}, m={row['m']}, "
            f"max_degree={row['max_degree']}, isolates={row['isolated_vertices']}, "
            f"density={density:.4f}"
        )
    if excluded_rows:
        print(f"Validated {len(excluded_rows)} excluded instance(s):")
        for row in excluded_rows:
            print(
                f"  {row['instance']}: n={row['n']}, m={row['m']}, "
                f"isolates={row['isolated_vertices']} (documented exclusion)"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
