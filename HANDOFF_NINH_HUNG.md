# Handoff — phần dữ liệu, MIP, benchmark và báo cáo của Ninh Ngọc Hưng

## Trạng thái snapshot

- Snapshot được rà soát là `BTL-2.zip`, tại commit `c7fa492aedce4706310544ca66a7fbefde53885e` (`feat/ninh-hung-next`, cùng commit với `origin/main-fix`). ZIP chứa working tree có các file đã sửa/chưa commit; vì vậy commit hash xác định HEAD, không có nghĩa working tree sạch.
- Không chỉnh sửa `report/main.pdf` trong lần rà soát này.
- Dataset benchmark đã xác minh gồm 3 graph Harwell–Boeing; `bcsstm01` được ghi riêng là trường hợp loại trừ.

## Dữ liệu đã xác minh

| Instance | n | m | Max degree | Isolates | Vai trò |
|---|---:|---:|---:|---:|---|
| JGL009 | 9 | 32 | 8 | 0 | Nhỏ, dày |
| BCSSTK01 | 48 | 176 | 11 | 0 | Trung bình, thưa |
| BP 400 | 822 | 4,015 | 294 | 0 | Lớn, thưa; kiểm tra giới hạn |

`m` là số cạnh vô hướng duy nhất sau chuẩn hóa: bỏ self-loop, gộp cạnh trùng/đối xứng và giữ đỉnh cô lập. Không đồng nhất `m` với số nonzero/entries của ma trận gốc. JGL009 có 50 entries theo nguồn nhưng graph chuẩn hóa trong repo có 32 cạnh. Candidate list 28 tên không có nghĩa đã xác minh đủ 28 graph.

## MIP formulation và kết quả

Hai adapter CPLEX MIP và Gurobi MIP dùng chung assignment formulation. Với `n` đỉnh và `m` cạnh vô hướng:

- Số biến: `n^2 + 1`.
- Số ràng buộc: `2n + mn^2` theo cách sinh model hiện tại.

| Instance | Variables | Constraints |
|---|---:|---:|
| JGL009 | 82 | 2,610 |
| BCSSTK01 | 2,305 | 405,600 |
| BP 400 | 675,685 | 2,712,872,904 |

BP 400 bị preflight guard chặn trước khi tạo model vì vượt ngưỡng 1,000,000 constraints; đây không phải kết quả solver, timeout hay infeasibility. Trong batch sáu phương pháp, CPLEX MIP gặp license error trên JGL009 và BCSSTK01; Gurobi MIP chứng minh tối ưu JGL009 và tìm incumbent 15 trên BCSSTK01 nhưng không chứng minh tối ưu trong ngân sách chạy.

## Batch benchmark chính — 300 giây/lượt

Nguồn: `results/raw/six_method_benchmark.jsonl`, 18 record (3 graph × 6 phương pháp), một luồng.

| Method | JGL009 | BCSSTK01 | BP 400 |
|---|---:|---:|---:|
| Pairwise SAT | 4 (OPT) | [6, 12] | SAT size guard |
| Order SAT | 4 (OPT) | [6, 13] | SAT size guard |
| CP-SAT | 4 (OPT) | [6, 12] | [147, 399] |
| CPLEX MIP | License error | License error | MIP size guard |
| Gurobi MIP | 4 (OPT) | [6, 15] | MIP size guard |
| CP Optimizer | 4 (OPT) | [6, 12] | [147, 263] |

Các cặp `[LB, UB]` dùng lower bound được chứng nhận độc lập và incumbent đã được validator kiểm tra. Timeout/FEASIBLE không phải chứng minh tối ưu. License error và size guard không được xem là timeout hay kết quả chất lượng nghiệm.

## Smoke mới trên máy Windows của người dùng

Nguồn: `results/raw/six_method_smoke_fresh.jsonl`, 12 record trên `cycle6` và `path5`:

- 10 lượt `OPTIMAL`.
- 2 lượt CPLEX CP có `NO_SOLUTION`/error do không tìm thấy chương trình `cpoptimizer` trên PATH.
- Đây là lỗi thiếu executable trong môi trường smoke, không phải bài toán vô nghiệm. Các lần kiểm tra engine khác trên máy người dùng đã xác nhận CP-SAT, CPLEX MIP và Gurobi MIP trả `OPTIMAL` trên toy.

## Kiểm chứng và giới hạn môi trường

- Trên máy Windows của người dùng: full test suite báo **141 passed, 22 subtests passed**; manifest validator xác nhận 3 benchmark graph và 1 graph bị loại; `plot_results.py --check-only --verify-runs` đọc 18 lượt và 3 dataset.
- Trong lần rà soát ZIP ở môi trường hiện tại: `scripts/validate_manifest.py` đạt; `plot_results.py --check-only --verify-runs` đạt và bảng LaTeX sinh lại khớp nội dung hiện tại. Full pytest không thể thu thập vì môi trường rà soát thiếu `ortools` và `pysat`; đây không phải kết quả test thất bại của code trên máy Windows.
- Đã tái chạy từ checkout sạch tại commit `f8f56a7` trên Windows, dùng lại môi trường Python của dự án. Thêm `D:\cpoptimizer\bin\x64_win64` vào PATH của phiên chạy rồi chạy `python scripts/benchmark.py --config configs/smoke.json --output <log-moi> --no-resume`. Cả 6 phương pháp trên cycle6 và path5 đạt OPTIMAL, cận dưới và bandwidth đều bằng 1. Log ở `results/raw/six_method_smoke_clean_f8f56a7.jsonl`.
- Kết quả CP Optimizer bandwidth 12 trong pilot 60 giây cần trưởng nhóm xác nhận nguồn/log trước khi sửa hoặc diễn giải lại đoạn báo cáo liên quan.

## Việc bàn giao còn lại

1. Xác nhận với trưởng nhóm nguồn kết quả CP Optimizer bandwidth 12 của pilot 60 giây.
2. Smoke từ checkout sạch đã đạt 12/12 tại commit `f8f56a7`.
3. Chốt nội dung README và gói dữ liệu/log cuối cùng.
4. Tạo lại và xác minh `CHECKSUMS.sha256` sau khi tất cả file đã chốt.

## Lệnh tái kiểm tra trên Windows

```powershell
py -3.14 -m pip install -e ".[dev,engines,plots]"
py -3.14 -m pytest -q
py -3.14 scripts\validate_manifest.py
py -3.14 scripts\plot_results.py --input results\raw\six_method_benchmark.jsonl --manifest data\manifest.csv --output-dir results\summary\week8_main --verify-runs --tex-outcomes report\sections\six_method_table.tex --check-only
```

Để chạy smoke mới, dùng output JSONL riêng. Không chạy nối vào `results/raw/six_method_smoke.jsonl` nếu muốn giữ log cũ.
