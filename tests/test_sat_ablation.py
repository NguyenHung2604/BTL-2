"""Compare the controlled SAT variants with the small brute-force oracle."""

from time import monotonic

import pytest

from brute_force import optimum
from cbmp.graph import Graph
from cbmp.validator import validated_bandwidth
from scripts.sat_ablation import _trial


@pytest.mark.parametrize("graph", [
    Graph("odd", 5, ((0, 2), (2, 4), (4, 1), (1, 3))),
    Graph("even", 6, tuple((u, v) for u in range(3) for v in range(3, 6))),
    Graph("long", 8, ((0, 4), (4, 1), (1, 5), (5, 2), (2, 6), (6, 3), (3, 7))),
])
def test_rebuilt_and_variants_agree_at_every_threshold(graph):
    initial = validated_bandwidth(graph.n, graph.edges, list(graph.vertices))
    expected = optimum(graph)
    schedule = None
    for encoding, mode in (("pairwise", "rebuilt"), ("pairwise", "rotation"),
                           ("order", "rebuilt"), ("order", "incremental")):
        events = []
        _trial(encoding, mode, events.append, graph,
               {"incumbent": initial, "lower_bound": 1}, monotonic() + 10)
        assert events[-1] == ("finish", "completed")
        thresholds = [event[1] for event in events if event[0] == "attempt"]
        decisions = [event[1] for event in events if event[0] == "decision"]
        assert decisions == ["SAT" if k >= expected else "UNSAT" for k in thresholds]
        if schedule is None:
            schedule = thresholds
        assert thresholds == schedule
        for event in events:
            if event[0] == "incumbent":
                assert validated_bandwidth(graph.n, graph.edges, event[1]) == event[2]
