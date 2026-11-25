# Cyclic Bandwidth Minimization Problem

Tìm cách xếp các đỉnh của đồ thị lên một vòng sao cho khoảng cách vòng lớn nhất trên các cạnh là nhỏ nhất. Quy ước `labels[v]` là vị trí của đỉnh `v`.

| Thành viên | Phụ trách |
|---|---|
| Nguyễn Minh Hùng | SAT pairwise, bộ giải SAT chung, CP-SAT |
| Nguyễn Minh Đức | SAT order, CPLEX CP |
| Ninh Ngọc Hưng | Mô hình MIP, CPLEX MIP, Gurobi MIP, chuẩn hóa Harwell–Boeing, benchmark và biểu đồ |

## Cài đặt và kiểm thử

Chạy từ gốc repo với Python 3.10 trở lên. Ví dụ trên PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest -q
```

## Chạy phần ngày 1–3

Hai encoding dùng Glucose3. Tham số `--k` kiểm tra có hoán vị đạt bandwidth ≤ K hay không. Với `cycle6`, cả hai encoding cho SAT ở K=1 và UNSAT ở K=0. Khi bỏ `--k`, bộ giải tìm bandwidth tối ưu dưới ngân sách chung.

```powershell
.\.venv\Scripts\python scripts/solve.py data/toy/cycle6.json --method sat_pairwise --k 1 --time-limit-seconds 10
.\.venv\Scripts\python scripts/solve.py data/toy/cycle6.json --method sat_order --k 0 --time-limit-seconds 10
.\.venv\Scripts\python scripts/prepare_harwell_boeing.py data/benchmarks/harwell_boeing/raw/bcsstk01.mtx.gz data/benchmarks/harwell_boeing/graphs/bcsstk01.json
```

Pairwise dùng biến gán đỉnh–vị trí, mỗi hàng đúng một và mỗi cột tối đa một. Order dùng chuỗi biến ngưỡng đơn điệu cho từng đỉnh. Điểm chuyển từ sai sang đúng xác định vị trí, với quy ước ngưỡng cuối luôn đúng. Mỗi cặp đỉnh phải khác vị trí. Cả hai encoding cấm mọi cặp vị trí của hai đầu cạnh có khoảng cách vòng vượt K. Bộ test so từng K với vét cạn trên đồ thị tối đa 8 đỉnh và kiểm tra các nhãn trả về bằng validator.

## Kiểm tra các engine

Nhóm phụ thuộc `engines` cài các Python API. CPLEX CP cần thêm chương trình `cpoptimizer` trên PATH. Cấu hình Gurobi 13.x khớp với cài đặt đã chạy thử trên máy nhóm.

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev,engines]"
foreach ($engine in 'cp_sat','cplex_cp','cplex_mip','gurobi_mip') {
    .\.venv\Scripts\python scripts/check_engines.py $engine
}
.\.venv\Scripts\python scripts/solve.py data/toy/cycle6.json --method gurobi_mip --time-limit-seconds 10
```

Batch tại commit 9df7be6 có 18 lượt trong `results/raw/six_method_benchmark.jsonl`. Smoke ban đầu có 12 lượt trong `results/raw/six_method_smoke.jsonl`; smoke mới trên máy Windows được lưu riêng ở `results/raw/six_method_smoke_fresh.jsonl` (10 `OPTIMAL`, 2 CPLEX CP lỗi do không tìm thấy `cpoptimizer` trên PATH). Lỗi thiếu executable không có nghĩa graph vô nghiệm. Runner ghi JSONL và tiếp tục các lượt còn thiếu khi chạy lại cùng cấu hình.

~~~powershell
.\.venv\Scripts\python scripts/benchmark.py --config configs/smoke.json
.\.venv\Scripts\python scripts/benchmark.py --config configs/mip_smoke.json --no-resume
.\.venv\Scripts\python scripts/benchmark.py --config configs/benchmark.json --dry-run
.\.venv\Scripts\python scripts/benchmark.py --config configs/mip_pilot.json --dry-run
~~~

Để tái hiện pilot sáu phương pháp có giới hạn 1 GiB trên Windows và thí nghiệm symmetry/incremental:

~~~powershell
.\.venv\Scripts\python -m pip install -e ".[windows-memory]"
.\.venv\Scripts\python scripts/benchmark.py --config configs/benchmark_day8_pilot.json --windows-job-memory-mib 1024
.\.venv\Scripts\python scripts/sat_ablation.py --output results/raw/week8_ablation.jsonl
~~~

Giới hạn Windows áp cho tổng bộ nhớ cam kết của runner và các tiến trình con. Cấu hình chính dùng 300 giây cho mỗi phương pháp trên mỗi đồ thị. Các batch mới ghi vào `results/raw/`.

`mip_smoke.json` kiểm tra riêng hai adapter MIP trên hai đồ thị toy; `mip_pilot.json` kiểm tra edition/license trên các ma trận Harwell–Boeing.

## Sinh bảng và hình

Cài thêm dependency hình bằng:

~~~powershell
.\.venv\Scripts\python -m pip install -e ".[plots]"
.\.venv\Scripts\python scripts/plot_results.py --input results/mip_pilot.jsonl --manifest data/manifest.csv --output-dir results/mip_pilot_summary
~~~

Để xuất bảng sáu phương pháp trực tiếp vào báo cáo sau một batch:

~~~powershell
.\.venv\Scripts\python scripts/plot_results.py --input results/summary/report_audit/main_latest.jsonl --output-dir results/summary/week8_main --verify-runs --tex-outcomes report/sections/six_method_table.tex
~~~

Script giữ nguyên các trạng thái lỗi/timeout và chỉ vẽ so sánh khi log có đủ dữ liệu; `--check-only` chỉ sinh bảng CSV, không cần `cnsplots`.
## Kết quả và khả năng tái lập

Snapshot hiện có 3 đồ thị đã xác minh trong `data/manifest.csv` (JGL009, BCSSTK01, BP 400), không phải toàn bộ 28 ứng viên trong candidate list. Batch sáu phương pháp gồm 18 lượt nằm tại `results/raw/six_method_benchmark.jsonl`; smoke ban đầu gồm 12 lượt tại `results/raw/six_method_smoke.jsonl`, smoke mới gồm 12 lượt tại `results/raw/six_method_smoke_fresh.jsonl`. Mỗi lượt benchmark chính có ngân sách 300 giây, một luồng. Log giữ riêng `status` và `termination_reason`: timeout, license error và preflight size guard không được xem là cùng một loại kết quả.

Để kiểm tra witness, cập nhật lower bound độc lập, CSV và bảng LaTeX từ log:

```powershell
.\.venv\Scripts\python scripts/plot_results.py --input results/summary/report_audit/main_latest.jsonl --manifest data/manifest.csv --output-dir results/summary/week8_main --verify-runs --tex-outcomes report/sections/six_method_table.tex --check-only
```

`--check-only` không cần `cnsplots`; để tái sinh hình, cài `.[plots]` và bỏ `--check-only`. Xem `HANDOFF_NINH_HUNG.md` để biết kết quả kiểm chứng, giới hạn license/môi trường, và cách diễn giải các batch.

Lưu ý: không tự động thay `report/main.pdf` trong quá trình kiểm tra dữ liệu/checksum. Dùng bản PDF đã được nhóm chốt sau khi trưởng nhóm xác nhận nội dung báo cáo.

Các file quan trọng (manifest, graph JSON, raw benchmark/smoke logs, summary CSV, bảng LaTeX và PDF/hình báo cáo) có SHA-256 trong `CHECKSUMS.sha256`. Kiểm tra sau khi giải nén bằng:

```powershell
Get-Content CHECKSUMS.sha256 | ForEach-Object { $p = ($_ -split '  ', 2); $actual = (Get-FileHash -Algorithm SHA256 $p[1]).Hash.ToLower(); if ($actual -ne $p[0]) { Write-Error "Checksum mismatch: $($p[1])" } }
```

## Reproduce the audited report

Run from the repository root with the project dependencies and the plots extra.
The historical main JSONL contains two 18-row batches. The report script
selects the complete batch at 9df7be6 and keeps all original records intact.
Blank native status/bound fields in the BCSSTK01 ledger mean unrecorded.
Stored adapter bounds and independently validated objectives have separate columns.

~~~powershell
python scripts/report_evidence.py
python scripts/plot_results.py --input results/summary/report_audit/main_latest.jsonl --output-dir results/summary/report_audit/main --verify-runs --tex-outcomes report/sections/six_method_table.tex --check-only
~~~

The additional normalized matrices are indexed by data/manifest_supplement.csv.
Use configs/supplement.json for the 18 sequential runs and
configs/supplement_cp_retry.json for the three IBM CP Optimizer retries.
For a new run, pass --output with a new JSONL path. The historical CP errors
and the three successful retries are kept separately.

The separate 300-second SAT comparison on BCSPWR02 uses
`configs/bcspwr02_final.json` and `results/raw/bcspwr02_final.jsonl`.
From the repo root, use the benchmark runner with an unused output path
to repeat the measurement. The report script reads the archived log.

The original 18 main records remain in main_18.jsonl. The latest report view, main_latest.jsonl, substitutes only the two matching 300-second CPLEX Studio runs. The supplement substitutes the two 10-second CPLEX Studio runs on IBM32 and BCSPWR01.
