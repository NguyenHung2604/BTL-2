
"""Reader for Harwell-Boeing sparse matrices converted to CBMP graphs."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from pathlib import Path


@dataclass(frozen=True)
class HBGraph:
    """Simple undirected graph extracted from an HB matrix."""

    n: int
    edges: tuple[tuple[int, int], ...]
    checksum: str
    matrix_type: str

    @property
    def num_edges(self) -> int:
        return len(self.edges)


def _format_width(fmt: str) -> tuple[int, int, str]:
    """Return (repeat, field_width, descriptor) from a basic Fortran format."""
    match = re.search(
        r"\(\s*(?:[+-]?\d+\s*P\s*)?(\d*)\s*([IDEFG])\s*(\d+)(?:\.\d+)?\s*\)",
        fmt.upper(),
    )

    if not match:
        raise ValueError(f"Unsupported Fortran format: {fmt}")

    repeat = int(match.group(1) or 1)
    descriptor = match.group(2)
    width = int(match.group(3))
    return repeat, width, descriptor


def _read_formatted_values(
    lines: list[str],
    fmt: str,
    expected_count: int,
) -> list[str]:
    """Read fixed-width fields from HB data cards."""
    repeat, width, _ = _format_width(fmt)
    values: list[str] = []

    for line in lines:
        # A format such as (8I10) describes up to 8 fields per card.
        for index in range(repeat):
            start = index * width
            field = line[start:start + width].strip()

            if field:
                values.append(field)

            if len(values) == expected_count:
                return values

    if len(values) != expected_count:
        raise ValueError(
            f"Expected {expected_count} values, found {len(values)} "
            f"for format {fmt}"
        )

    return values


def _parse_fortran_number(value: str) -> float:
    """Parse an HB numeric field, including Fortran D exponents."""
    return float(value.replace("D", "E").replace("d", "e"))


def read_harwell_boeing(path: str | Path) -> HBGraph:
    """Read an HB sparse matrix and convert nonzeros to an undirected graph.

    Vertices correspond to matrix rows/columns. An undirected edge {u, v}
    exists if A[u, v] or A[v, u] is nonzero. Diagonal entries are ignored.
    """
    path = Path(path)
    lines = path.read_text(encoding="ascii").splitlines()

    if len(lines) < 4:
        raise ValueError("Invalid Harwell-Boeing file: incomplete header")

    # Header line 2: total, pointer, index, value and RHS card counts.
    try:
        counts = [int(lines[1][i:i + 14]) for i in range(0, 70, 14)]
        total_cards, ptr_cards, ind_cards, val_cards, rhs_cards = counts
    except (ValueError, IndexError):
        try:
            total_cards, ptr_cards, ind_cards, val_cards, rhs_cards = (
                int(x) for x in lines[1].split()
            )
        except (ValueError, TypeError):
            raise ValueError("Cannot parse HB card counts") from None

    # Header line 3: matrix type, rows, columns, nonzeros, elemental values.
    header = lines[2].split()
    if len(header) < 5:
        raise ValueError("Invalid HB matrix header")

    matrix_type = header[0].upper()
    nrow, ncol, nnzero, _ = map(int, header[1:5])

    if nrow != ncol:
        raise ValueError(
            f"CBMP requires a square matrix; got {nrow} x {ncol}"
        )

    if nrow <= 0:
        raise ValueError("Matrix must contain at least one vertex")

    if len(matrix_type) != 3:
        raise ValueError(f"Invalid HB matrix type: {matrix_type}")

    # This reader handles assembled sparse matrices, not elemental matrices.
    if matrix_type[2] == "E":
        raise NotImplementedError(
            "Elemental Harwell-Boeing matrices are not supported"
        )

    # Header line 4: pointer, index, value and RHS formats.
    formats = re.findall(r"\([^)]*\)", lines[3])
    if len(formats) < 3:
        raise ValueError("Cannot parse HB data formats")

    ptr_fmt, ind_fmt, val_fmt = formats[:3]

    # The optional RHS header occupies one card when RHS cards are present.
    data_start = 4 + (1 if rhs_cards > 0 else 0)

    ptr_lines = lines[data_start:data_start + ptr_cards]
    ind_start = data_start + ptr_cards
    ind_lines = lines[ind_start:ind_start + ind_cards]
    val_start = ind_start + ind_cards
    val_lines = lines[val_start:val_start + val_cards]

    # CSC column pointers and row indices are one-based in HB files.
    pointers = [
        int(value)
        for value in _read_formatted_values(
            ptr_lines, ptr_fmt, ncol + 1
        )
    ]
    row_indices = [
        int(value)
        for value in _read_formatted_values(
            ind_lines, ind_fmt, nnzero
        )
    ]

    if pointers[0] != 1 or pointers[-1] != nnzero + 1:
        raise ValueError("Invalid HB column pointers")

    if any(a > b for a, b in zip(pointers, pointers[1:])):
        raise ValueError("HB column pointers must be nondecreasing")

    if any(index < 1 or index > nrow for index in row_indices):
        raise ValueError("HB row index is outside the matrix")

    value_kind = matrix_type[0]
    if value_kind == "P":
        nonzero_flags = [True] * nnzero
    else:
        repeat, width, descriptor = _format_width(val_fmt)
        raw_values = _read_formatted_values(
            val_lines,
            val_fmt,
            nnzero * (2 if value_kind == "C" else 1),
        )

        if value_kind == "C":
            nonzero_flags = [
                (
                    _parse_fortran_number(raw_values[2 * i]) != 0
                    or _parse_fortran_number(raw_values[2 * i + 1]) != 0
                )
                for i in range(nnzero)
            ]
        else:
            nonzero_flags = [
                _parse_fortran_number(value) != 0
                for value in raw_values
            ]

    edges: set[tuple[int, int]] = set()

    for column in range(ncol):
        # Convert the one-based CSC range to Python indices.
        for entry in range(pointers[column] - 1, pointers[column + 1] - 1):
            row = row_indices[entry] - 1

            if not nonzero_flags[entry]:
                continue

            if row == column:
                continue

            edges.add((min(row, column), max(row, column)))

    normalized_edges = tuple(sorted(edges))

    # Checksum is computed from the normalized graph representation.
    checksum_input = (
        f"n={nrow}\n"
        + "".join(f"{u},{v}\n" for u, v in normalized_edges)
    ).encode("ascii")
    checksum = hashlib.sha256(checksum_input).hexdigest()

    return HBGraph(
        n=nrow,
        edges=normalized_edges,
        checksum=checksum,
        matrix_type=matrix_type,
    )
