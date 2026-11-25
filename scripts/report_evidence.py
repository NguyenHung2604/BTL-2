"""Rebuild the audited run ledger, matched-threshold table and figure from JSONL."""
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cbmp.graph import load_graph
from cbmp.manifest import graph_statistics, load_manifest, normalized_graph_sha256
from cbmp.validator import certify_record, validated_bandwidth

MAIN = "9df7be63e3a7c843c8b1eae836ef4fe3c440351d"
OUT = ROOT / "results/summary/report_audit"
REPORT = ROOT / "report"


def save_csv(name, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def gurobi_records(protocol, budget, names):
    source = ROOT / "results/raw" / f"gurobi_{protocol}_academic.jsonl"
    rows = {}
    for line in source.read_text().splitlines():
        r = json.loads(line)
        name = r["graph_id"]
        assert name not in rows and r["method"] == "gurobi_mip"
        assert r["time_limit"] == budget and r["threads"] == 1 and r["seed"] == 0
        graph = load_graph(ROOT / r["source_path"])
        assert r["graph_checksum"] == normalized_graph_sha256(graph.n, graph.edges)
        certify_record(r, graph.n, graph.edges)
        rows[name] = r
    assert set(rows) == set(names)
    return rows


def supplemental_table():
    sources = ["supplement_26c9d79.jsonl", "supplement_cp_retry.jsonl"]
    methods = {"sat_pairwise":"Pairwise SAT", "sat_order":"Order SAT", "cp_sat":"OR-Tools CP-SAT",
               "cplex_cp":"IBM CP Optimizer", "cplex_mip":"IBM CPLEX MIP", "gurobi_mip":"Gurobi MIP"}
    names = ["ibm32", "bcspwr01", "scrambled_path8"]
    cells = {}
    for source in sources:
        for line in (ROOT/"results/raw"/source).read_text().splitlines():
            r = json.loads(line)
            graph = load_graph(ROOT/r["source_path"])
            if r["labeling"] is not None:
                validated_bandwidth(graph.n, graph.edges, r["labeling"], r["incumbent"])
            if source == sources[1]:
                assert r["method"] == "cplex_cp" and cells[r["method"], r["graph_id"]] == "Error"
            if r["status"] == "OPTIMAL":
                assert r["optimality_proven"] and r["lower_bound"] == r["incumbent"]
                cell = str(r["incumbent"])
            elif r["status"] == "FEASIBLE":
                cell = f"[{r['lower_bound']:g},{r['incumbent']:g}]"
            else:
                cell = "License" if r["termination_reason"] == "license_error" else "Error"
            cells[r["method"],r["graph_id"]] = cell
    for source, name in [("cplex_studio_check_20261125_104852.jsonl", "bcspwr01"),
                         ("cplex_studio_supplement.jsonl", "ibm32")]:
        records = [json.loads(line) for line in (ROOT/"results/raw"/source).read_text().splitlines()]
        [r] = [row for row in records if row["graph_id"] == name and row["method"] == "cplex_mip"]
        assert r["time_limit"] == 10 and r["threads"] == 1 and cells["cplex_mip", name] == "License"
        graph = load_graph(ROOT/f"data/benchmarks/harwell_boeing/graphs/{name}.json")
        value = validated_bandwidth(graph.n, graph.edges, r["labeling"], r["incumbent"])
        degree = graph_statistics(graph.n, graph.edges)["max_degree"]
        lower = max((degree+1)//2, r["lower_bound"])
        cells["cplex_mip", name] = str(value) if r["optimality_proven"] else f"[{lower:g},{value}]"
    retries = gurobi_records("supplement10", 10, names)
    for name, r in retries.items():
        cells["gurobi_mip", name] = (str(r["incumbent"]) if r["optimality_proven"]
                                     else f"[{r['lower_bound']:g},{r['incumbent']}]")
    rows = [r"\begin{table}[htbp]\centering\small",
            r"\caption{Supplement, 10 seconds per graph and method. Single values are proven optima; intervals are validated bounds at timeout. The IBM CPLEX MIP entries for IBM32 and BCSPWR01 use the Studio reruns. The Gurobi row uses the academic-license reruns. IBM CP Optimizer uses the separate engine-path retry.}",
            r"\label{tab:supplement}\begin{tabular}{lccc}\hline",
            r"Method & IBM32 & BCSPWR01 & Scrambled path\\\hline"]
    for method,label in methods.items():
        rows.append(" & ".join([label]+[cells[method,name] for name in names])+r"\\")
    (REPORT/"sections/supplement_table.tex").write_text("\n".join(rows+[r"\hline\end{tabular}\end{table}"])+"\n")


def larger_matrix_table():
    source = ROOT / "results/raw/bcspwr02_final.jsonl"
    records = [json.loads(line) for line in source.read_text().splitlines()]
    assert [r["method"] for r in records] == ["sat_pairwise", "sat_order"]
    rows = [r"\begin{table}[htbp]\centering\small",
            r"\caption{BCSPWR02, 300 seconds per encoding. Variables, clauses and build/load time describe the first formula at $K=23$. Calls count decisions with recorded solver time. The last columns give the bounds at termination and the reason.}",
            r"\label{tab:larger}\begin{tabular}{lrrrrcl}\hline",
            r"Encoding & Variables & Clauses & Build (s) & Calls & [LB,UB] & Reason\\\hline"]
    for r in records:
        g = load_graph(ROOT / r["source_path"])
        assert r["time_limit"] == 300 and validated_bandwidth(g.n,g.edges,list(range(g.n))) == 24
        validated_bandwidth(g.n,g.edges,r["labeling"],r["incumbent"])
        h = r["decision_history"]
        first = h[0]
        assert first["k"] == 23
        calls = sum(step["solve_time"] > 0 for step in h)
        rows.append(f"{r['encoding'].capitalize()} & {first['num_variables']:,} & {first['num_clauses']:,} & "
                    f"{first['build_time']:.3f} & {calls} & [{r['lower_bound']},{r['incumbent']}] & "
                    + r["termination_reason"] + r"\\")
    (REPORT/"sections/bcspwr02_table.tex").write_text("\n".join(rows+[r"\hline\end{tabular}\end{table}"])+"\n")


def main():
    import cnsplots as cns
    import pandas as pd

    OUT.mkdir(parents=True, exist_ok=True)
    supplemental_table()
    larger_matrix_table()
    dataset = load_manifest(ROOT / "data/manifest.csv")
    info = next(r for r in dataset if r["instance"] == "bcsstk01")
    graph = load_graph(ROOT / info["graph_path"])
    lower = (int(info["max_degree"]) + 1) // 2
    logs = [*sorted((ROOT / "results").glob("*.jsonl")), *sorted((ROOT / "results/raw").glob("*.jsonl"))]
    ledger, histories, selected = [], {}, []
    for source in logs:
        for line, raw in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
            if not raw.strip():
                continue
            r = json.loads(raw)
            primary = source.name == "six_method_benchmark.jsonl" and r["commit_hash"] == MAIN
            if primary:
                selected.append(raw)
            if r.get("graph_id") != "bcsstk01":
                continue
            checksum = r.get("normalized_graph_sha256")
            if checksum and checksum != info["normalized_graph_sha256"]:
                raise ValueError(f"Unexpected graph at {source}:{line}")
            witness = r.get("labeling")
            value = None if witness is None else validated_bandwidth(graph.n, graph.edges, witness, r["incumbent"])
            ledger.append(dict(source=source.relative_to(ROOT).as_posix(), line=line,
                               commit=r.get("commit_hash"), method=r["method"], version=r.get("solver_version"),
                               graph_id=r["graph_id"], stored_graph_hash=checksum or r.get("input_sha256"),
                               budget=r.get("time_limit",r.get("wall_budget")), elapsed=r["total_time"],
                               status=r["status"], reason=r["termination_reason"], objective=r["incumbent"],
                               stored_bound=r["lower_bound"], degree_bound=lower, validated=value,
                               native_status=r.get("native_status"), native_bound=r.get("native_best_bound"),
                               error=r.get("error_message")))
            if primary and r["method"] in {"sat_pairwise","sat_order"}:
                histories[r["method"]] = {h["k"]: h for h in r["decision_history"]}
    save_csv("bcsstk01_records.csv", ledger)
    assert len(selected) == 18
    (OUT / "main_18.jsonl").write_text("\n".join(selected)+"\n", encoding="utf-8")
    main_rows = [json.loads(line) for line in selected]
    reruns = [json.loads(line) for line in (ROOT/"results/raw/cplex_studio_main.jsonl").read_text().splitlines()]
    assert len(reruns) == 2 and {r["graph_id"] for r in reruns} == {"jgl009", "bcsstk01"}
    for retry in reruns:
        assert retry["time_limit"] == 300 and retry["threads"] == 1 and retry["method"] == "cplex_mip"
        [i] = [i for i,r in enumerate(main_rows) if (r["method"],r["graph_id"]) == ("cplex_mip",retry["graph_id"])]
        assert main_rows[i]["termination_reason"] == "license_error"
        assert main_rows[i]["graph_checksum"] == retry["graph_checksum"]
        main_rows[i] = retry
    gurobi = gurobi_records("main300", 300, [row["instance"] for row in dataset])
    for i, r in enumerate(main_rows):
        if r["method"] == "gurobi_mip":
            retry = gurobi[r["graph_id"]]
            assert r["graph_checksum"] == retry["graph_checksum"]
            main_rows[i] = retry
    (OUT/"main_latest.jsonl").write_text("".join(json.dumps(r)+"\n" for r in main_rows), encoding="utf-8")
    rows = []
    for k in sorted(set.intersection(*(set(h) for h in histories.values())), reverse=True):
        for method in ("sat_pairwise","sat_order"):
            h = histories[method][k]
            n = graph.n
            edge = len(graph.edges)*n*(n-min(n,2*k+1))
            pairs = n*n*(n-1)//2
            base = n+2*pairs if method=="sat_pairwise" else n*(n-2)+pairs
            assert edge+base == h["num_clauses"]
            rows.append(dict(K=k, encoding=method[4:].capitalize(), variables=h["num_variables"],
                             edge=edge, clauses=h["num_clauses"], build=h["build_time"]))
    save_csv("matched_thresholds.csv",rows)
    body = [r"\begin{table}[htbp]\centering\small",
            r"\caption{BCSSTK01 at the first threshold ($K=23$) of the 300-second main run. Build time includes loading Glucose3.}",
            r"\label{tab:k23}\begin{tabular}{lrrrr}\hline",
            r"Encoding & Variables & Edge clauses & All clauses & Build (s)\\\hline"]
    for r in rows:
        if r["K"]==23:
            body.append("{encoding} & {variables:,} & {edge:,} & {clauses:,} & {build:.3f}".format(**r)+r"\\")
    (REPORT/"sections/k23_table.tex").write_text("\n".join(body+[r"\hline\end{tabular}\end{table}"])+"\n")
    cns.setup_matplotlib()
    fig = cns.figure(width=380,height=180,unit="pt")
    ax = fig.add_subplot(111)
    cns.lineplot(data=pd.DataFrame(rows),x="K",y="clauses",hue="encoding",marker="o",ax=ax)
    ax.invert_xaxis()
    ax.set(xlabel="Bandwidth threshold K (search order)",ylabel="Input clauses at one K")
    cns.savefig(str(REPORT/"figures/bcsstk01_thresholds.pdf"),fig=fig)


if __name__ == "__main__":
    main()
