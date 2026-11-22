"""Deadline and result handling shared by the pairwise search and CP-SAT."""

import math
import multiprocessing as mp
import subprocess
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from time import monotonic

from cbmp.graph import Graph
from cbmp.validator import validated_bandwidth


def _worker(send, implementation, graph, result, deadline):
    try:
        implementation(send.send, graph, result, deadline)
    except MemoryError:
        send.send(("finish", "OOM"))
    except Exception as exc:
        send.send(("error", f"{type(exc).__name__}: {exc}"))
    finally:
        send.close()


def run_solver(implementation, method, package, graph_id, n, edges, config, seed,
               wall_budget, threads):
    """Supervise one optimization, retaining validated incumbents across a timeout."""
    start = monotonic()
    if not math.isfinite(wall_budget) or wall_budget < 0 or threads < 1:
        raise ValueError("Expected a finite nonnegative budget and positive thread count")
    deadline = start + wall_budget
    graph = Graph(graph_id, n, tuple(sorted({tuple(sorted(edge)) for edge in edges})))
    labels = list(graph.vertices)
    best = validated_bandwidth(n, graph.edges, labels)
    degrees = [0] * n
    for u, v in graph.edges:
        degrees[u] += 1
        degrees[v] += 1
    lower = (max(degrees, default=0) + 1) // 2
    try:
        solver_version = version(package)
    except PackageNotFoundError:
        solver_version = None
    commit = (config or {}).get("commit_hash")
    if commit is None and monotonic() < deadline:
        try:
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[2],
                text=True, stderr=subprocess.DEVNULL, timeout=max(0, deadline - monotonic()),
            ).strip()
        except (OSError, subprocess.SubprocessError):
            pass
    result = dict(graph_id=graph_id, method=method,
                  encoding="pairwise" if method == "sat_pairwise" else None,
                  solver_version=solver_version, status="FEASIBLE", incumbent=best,
                  lower_bound=lower, optimality_proven=False, labeling=labels,
                  build_time=0.0, solve_time=0.0, total_time=0.0, num_vars=0,
                  num_clauses=0 if method == "sat_pairwise" else None,
                  termination_reason="timeout", commit_hash=commit, history=[],
                  seed=seed, threads=threads)
    if best > lower and monotonic() < deadline:
        # A blocking encoder or native solver cannot overrun the whole search.
        ctx = mp.get_context("spawn")
        recv, send = ctx.Pipe(duplex=False)
        proc = ctx.Process(target=_worker, args=(send, implementation, graph, result, deadline))
        proc.start()
        send.close()
        phase = attempt = None
        phase_start = 0.0
        try:
            while monotonic() < deadline and recv.poll(max(0, deadline - monotonic())):
                event, *args = recv.recv()
                if event == "phase":
                    new_phase, timestamp = args
                    if phase:
                        result[phase] += timestamp - phase_start
                    phase, phase_start = new_phase, timestamp
                elif event == "attempt":
                    attempt = args
                elif event == "size":
                    result["num_vars"] += args[0]
                    if result["num_clauses"] is not None:
                        result["num_clauses"] += args[1]
                elif event == "decision":
                    status, timestamp = args
                    k, began = attempt
                    result["history"].append(dict(k=k, status=status, elapsed=timestamp - began))
                    attempt = None
                    if status == "UNSAT":
                        result["lower_bound"] = k + 1
                elif event == "incumbent":
                    candidate, claimed = args
                    value = validated_bandwidth(n, graph.edges, candidate, claimed)
                    if value < result["incumbent"]:
                        result.update(labeling=candidate, incumbent=value)
                elif event == "bound":
                    result["lower_bound"] = max(result["lower_bound"], args[0])
                elif event == "error":
                    result.update(termination_reason="error", error_message=args[0])
                    break
                elif event == "finish":
                    result["termination_reason"] = args[0]
                    break
        except EOFError:
            result.update(termination_reason="error", error_message="Worker exited without a result")
        finally:
            stop = monotonic()
            if phase:
                result[phase] += max(0.0, stop - phase_start)
            if attempt:
                k, began = attempt
                result["history"].append(dict(k=k, status="UNKNOWN", elapsed=stop - began))
            if proc.is_alive():
                proc.terminate()
            proc.join()
            recv.close()
            proc.close()
    if result["incumbent"] == result["lower_bound"]:
        result.update(status="OPTIMAL", optimality_proven=True, termination_reason="completed")
    result["total_time"] = monotonic() - start
    return result


def _pairwise(emit, graph, result, deadline):
    from pysat.solvers import Glucose3
    from cbmp.encodings import pairwise

    best = result["incumbent"]
    while best > result["lower_bound"]:
        if monotonic() >= deadline:
            emit(("finish", "timeout"))
            return
        k = best - 1
        began = monotonic()
        emit(("attempt", k, began))
        emit(("phase", "build_time", began))
        clauses, metadata = pairwise.build(graph, k)
        with Glucose3(bootstrap_with=clauses) as solver:
            emit(("size", solver.nof_vars(), len(clauses)))
            emit(("phase", "solve_time", monotonic()))
            answer = solver.solve()
            if answer is True:
                labels = pairwise.decode(solver.get_model(), metadata)
                best = validated_bandwidth(graph.n, graph.edges, labels)
                if best > k:
                    raise ValueError("Pairwise witness violates threshold")
                emit(("incumbent", labels, best))
        now = monotonic()
        status = {True: "SAT", False: "UNSAT", None: "UNKNOWN"}[answer]
        emit(("decision", status, now))
        emit(("phase", None, now))
        if answer is None:
            emit(("finish", "timeout"))
            return
        if answer is False:
            break
    emit(("finish", "completed"))


def solve(graph_id, n, edges, config=None, seed=0, wall_budget=60.0, threads=1):
    """Optimize with fresh Glucose3 instances. Size counters sum completed builds."""
    return run_solver(_pairwise, "sat_pairwise", "python-sat", graph_id, n, edges,
                      config, seed, wall_budget, threads)
