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

Gurobi giải CBMP bằng mô hình gán nhị phân, tối thiểu hóa cận trên khoảng cách vòng trên các cạnh. CP-SAT, CPLEX CP và CPLEX MIP hiện có ví dụ kiểm tra engine. Adapter CBMP cho ba engine này, benchmark theo lô và biểu đồ cnsplots thuộc các ngày sau.
