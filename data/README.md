# Harwell–Boeing benchmark data

## Normalization contract

Each matrix is converted to a **simple undirected graph** with vertices `0, ..., n-1`.
For every off-diagonal matrix coordinate `(i, j)`, add the undirected edge
`{i, j}` if the stored matrix value is nonzero. Equivalently, an edge exists if
`A[i,j] != 0 OR A[j,i] != 0`. Diagonal entries are dropped, duplicate and
opposite-direction entries collapse to one undirected edge, and isolated
vertices are retained through `n`.

Therefore, matrix nonzero counts in source pages or papers are **not assumed to
be graph edge counts**. The normalized `m` in `manifest.csv` always counts unique
undirected edges after this rule. In particular, the NILS paper's Table A.2
reports `jgl009` with 50 entries, while this repository's normalized graph has
32 unique undirected edges. Do not copy the paper's `|E|` column into the
manifest or compare results until graph conventions have been reconciled.

## Verified benchmark manifest

`manifest.csv` is the authoritative selected set for the current pilot and
benchmark pipeline. Every row stores the source page, raw file path, normalized
graph path, matrix type, `n`, `m`, maximum degree, isolated-vertex count, raw
SHA-256, graph-file SHA-256, and a canonical normalized-graph SHA-256.

| Instance | n | m (simple undirected) | Max degree | Density | Role |
|---|---:|---:|---:|---:|---|
| `jgl009` | 9 | 32 | 8 | 0.8889 | Small, dense; compressed HB parser check |
| `bcsstk01` | 48 | 176 | 11 | 0.1560 | Medium; MIP pilot |
| `bp___400` | 822 | 4,015 | 294 | 0.0119 | Large sparse; preflight/scalability guard |

BP 400 is an additional SMTAPE instance, not one of the 28 NILS Table A.2
candidates; it is included to exercise the large-sparse preflight guard.

Run `python scripts/validate_manifest.py` before any benchmark. The command
fails if a raw file, graph JSON, checksum, or graph statistic differs from the
manifest.

## Excluded matrices

`excluded.csv` records downloaded matrices that were deliberately not included
in the main set. `bcsstm01` is a 48-by-48 matrix containing only diagonal
nonzeros; after diagonal removal it produces 48 isolated vertices and zero
edges. It remains documented as an edge-case dataset, not as a representative
benchmark. The original input bundle contained `jgl009.pua` and
`jgl009.pua.gz`; decompression confirmed they are identical, so the canonical
raw directory keeps only the compressed copy and counts one instance.

## Candidate expansion

`harwell_boeing_candidates.csv` records all 28 names and the paper's reported
size/count from Table A.2 of Ren et al. These are **candidates only** unless
marked verified in the status column. A candidate must be downloaded from its
original source, normalized with the rule above, checksum-locked, and checked
for graph equivalence before it is added to `manifest.csv`. The paper's
reported `E` must not be assumed to equal normalized simple-graph `m`.

## Rebuild a graph from a raw matrix

The preparation script accepts both Matrix Market (`.mtx`, `.mtx.gz`) and
assembled Harwell–Boeing (`.rsa`, `.rua`, `.pua`, including `.gz`) files:

```powershell
python scripts/prepare_harwell_boeing.py `
  data/benchmarks/harwell_boeing/raw/jgl009.pua.gz `
  data/benchmarks/harwell_boeing/graphs/jgl009.json
```

After changing a raw file or graph JSON, regenerate all manifest checksum and
statistic fields deliberately; never hand-edit a checksum to silence a failed
validation.
