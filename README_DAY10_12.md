# CBMP — bàn giao phần Ninh Ngọc Hưng (Ngày 10–12)

Gói này **chỉ bổ sung một file báo cáo độc lập**; không ghi đè `experiments.tex`, `baselines.tex`, mã nguồn solver, cấu hình benchmark hay kết quả thô của nhóm.

## 1. Phần đã chốt từ batch thật

- 15/15 lượt đã có trong `results/benchmark_day8.jsonl`.
- 3 graph đã xác minh: JGL009 (n=9,m=32), BCSSTK01 (n=48,m=176), BP 400 (n=822,m=4015).
- 5 method được cấu hình: pairwise SAT, order SAT, CP-SAT, CPLEX MIP, Gurobi MIP.
- MIP dùng chung formulation: `n^2+1` biến và `2n + m*n^2` ràng buộc.
- CPLEX MIP/Gurobi MIP: license error ở hai graph nhỏ; BP 400 bị preflight guard. Không được diễn giải thành solver timeout hay formulation sai.
- CPLEX CP không nằm trong batch vì thiếu CP Optimizer engine; không thuộc phần triển khai chính của Hưng theo phân công.

## 2. Cách đưa đoạn Results vào báo cáo

Copy `report/sections/ninh_hung_results.tex` vào đúng thư mục `report/sections/` trong repo.

Trong `report/main.tex`, thêm đúng một dòng sau `\input{sections/experiments}`:

```tex
\input{sections/ninh_hung_results}
```

Không thay thế `experiments.tex` hoặc `baselines.tex`. File mới dùng số liệu batch 300 giây được người dùng xác nhận trong console. Nếu muốn bảng chi tiết hơn (incumbent, lower bound, build/solve time), hãy lấy từ `run_summary.csv`/JSONL thực tế, không tự điền số.

## 3. Hoàn tất Ngày 10 — phần MIP và scalability

Đã có công thức kích thước và số đếm kiểm tra được:

| Instance | Variables | Constraints |
|---|---:|---:|
| JGL009 | 82 | 2,610 |
| BCSSTK01 | 2,305 | 405,600 |
| BP 400 | 675,685 | 2,712,872,904 |

BP 400 vượt `max_constraints=1,000,000`, do đó bị từ chối trước khi dựng model. MIP adapter vẫn cần được đánh giá bằng smoke tests trên toy và bằng solver/license phù hợp; batch này chưa chứng minh được hai backend giải thành công các graph benchmark.

## 4. Hoàn tất Ngày 11 — bảng/hình và diễn giải

Đã sinh 7 hình, mỗi hình có SVG và PDF, tại `results/benchmark_day8_summary/`:

- `cbmp_circular_layout`
- `dataset_size_profile`
- `status_by_method`
- `cactus_optimality`
- `pairwise_vs_order`
- `sat_clauses_vs_n`
- `mip_constraints_vs_n`

CSV đầu ra cần được giữ cùng batch: `dataset_summary.csv`, `run_summary.csv`, `status_summary.csv`, `metadata.json` (và các CSV phụ nếu script sinh ra). Không sửa tay CSV hoặc JSONL để làm đẹp kết quả.

## 5. Ngày 12 — clean-checkout reproducibility (PowerShell)

**Không chạy `git clean -fd`, không xóa file results, không checkout đè working tree.** Trước tiên, lưu trạng thái hiện tại:

```powershell
git status --short
git rev-parse HEAD
git diff --stat
```

Sau khi các thay đổi cần giữ đã được commit và push, tạo worktree sạch ở commit đã push (thay `<COMMIT_DA_PUSH>` bằng hash thật):

```powershell
git fetch origin
git worktree add ..\BTL-2-clean <COMMIT_DA_PUSH>
Set-Location ..\BTL-2-clean
py -3.14 -m pip install -e ".[plots]"
py -3.14 -m pytest -q
py -3.14 scripts\validate_manifest.py
```

Chạy smoke trên tập toy, không chạy lại batch 300 giây:

```powershell
py -3.14 scripts\benchmark.py --config configs\mip_smoke.json --no-resume
py -3.14 scripts\benchmark.py --config configs\cp_sat_smoke.json --no-resume
```

Lưu ý: smoke MIP chỉ chứng minh adapter và license chạy được trên toy; không chứng minh license đủ kích thước cho Harwell–Boeing. Cũng cần kiểm tra file config smoke trong commit đã chọn có đúng output path riêng để không ghi đè kết quả khác.

Cuối cùng, kiểm tra báo cáo biên dịch được bằng lệnh LaTeX đang dùng trong repo/môi trường của nhóm. Nếu thiếu `latexmk`/BibTeX, ghi rõ dependency còn thiếu thay vì đánh dấu build thành công.

## 6. Những việc không nên nhận thêm vào phần của Hưng

- Không tự viết lại CP-SAT (phân công Hùng).
- Không tự cài/triển khai CPLEX CP/CP Optimizer (phân công Đức).
- Không nhận việc sửa order encoding hoặc pairwise encoding trừ khi được review phát hiện lỗi cụ thể.
- Phần Hưng cần chốt: shared ILP + hai MIP adapters + dữ liệu/validator + runner/log/resume + cnsplots + phần báo cáo MIP/experimental setup/scalability + clean-checkout verification.

## 7. Bằng chứng cần giữ khi bàn giao

- `results/benchmark_day8.jsonl` (15 records)
- `results/benchmark_day8_summary/*.csv` và `metadata.json`
- 7 hình SVG/PDF
- `data/manifest.csv`, `data/excluded.csv`, raw/normalized graph files và checksum
- test output `119 passed, 22 subtests passed` (theo lần chạy gần nhất đã báo)
- commit hash, Python version, OR-Tools version, Gurobi/CPLEX license error messages, CPU/RAM/OS nếu lấy được từ máy chạy
