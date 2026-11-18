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

Lõi đọc đồ thị, tính bandwidth, kiểm tra nghiệm và kiểu kết quả đã sẵn sàng. Test lõi chỉ cần pytest. Hai đồ thị mẫu nằm trong `data/toy/`. Các encoding, solver, công cụ chuẩn hóa, chạy benchmark và vẽ hình bằng cnsplots đang chờ triển khai. Xem tham số bằng `python scripts/solve.py --help` hoặc dùng `--help` với từng script. Chỉnh ngân sách mỗi lượt chạy trong `configs/` sau pilot.
