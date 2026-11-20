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

Hai encoding SAT, CPLEX MIP và Gurobi MIP chạy được qua CLI và benchmark. CP-SAT và CPLEX CP hiện có ví dụ kiểm tra engine. Runner ghi JSONL và tiếp tục các lượt còn thiếu khi chạy lại cùng cấu hình.

~~~powershell
.\.venv\Scripts\python scripts/benchmark.py --config configs/smoke.json
.\.venv\Scripts\python scripts/benchmark.py --config configs/mip_smoke.json --no-resume
.\.venv\Scripts\python scripts/benchmark.py --config configs/benchmark.json --dry-run
.\.venv\Scripts\python scripts/benchmark.py --config configs/mip_pilot.json --dry-run
~~~

`mip_smoke.json` kiểm tra riêng hai adapter MIP trên hai đồ thị toy; `mip_pilot.json` kiểm tra edition/license trên các ma trận Harwell–Boeing.

## Sinh bảng và hình

Cài thêm dependency hình bằng:

~~~powershell
.\.venv\Scripts\python -m pip install -e ".[plots]"
.\.venv\Scripts\python scripts/plot_results.py --input results/mip_pilot.jsonl --manifest data/manifest.csv --output-dir results/mip_pilot_summary
~~~

Script giữ nguyên các trạng thái lỗi/timeout và chỉ vẽ so sánh khi log có đủ dữ liệu; `--check-only` chỉ sinh bảng CSV, không cần `cnsplots`.