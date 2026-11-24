# Handoff — phần dữ liệu, MIP và benchmark của Hưng
## Đã hoàn thiện trong bản commit này

- Chuẩn hóa tập benchmark đang có bằng một `data/manifest.csv` gồm JGL009, BCSSTK01 và BP 400.
- Ghi nguồn, raw SHA-256, graph-file SHA-256, normalized-graph SHA-256, `n`, `m`, bậc lớn nhất và số đỉnh cô lập.
- Ghi BCSSTM01 vào `data/excluded.csv`: sau khi bỏ đường chéo, đồ thị có 48 đỉnh cô lập và 0 cạnh.
- Lưu danh sách 28 ứng viên Table A.2 trong `data/harwell_boeing_candidates.csv`; các ứng viên chưa có raw file/graph/checksum vẫn ở trạng thái chưa xác minh.
- Parser Harwell–Boeing đọc được `.gz`; script chuẩn hóa hỗ trợ cả Harwell–Boeing và Matrix Market.
- Runner xác minh manifest, kiểm tra incumbent độc lập, resume theo dữ liệu/cấu hình/commit, lưu metadata nguồn và phân biệt status với termination reason.
- SAT runner log lịch sử SAT/UNSAT/UNKNOWN theo từng ngưỡng K, thời gian build/solve, số biến và số clause. MIP runner log số biến/ràng buộc. `src/cbmp/solvers/sat.py` chỉ được bổ sung telemetry, không đổi encoding/thuật toán; Hùng nên review thay đổi giao diện này vì file thuộc phần SAT chung.
- Bổ sung guard trước khi chạy SAT/MIP để tránh tạo mô hình vượt giới hạn cấu hình.
- Pilot MIP đặt 60 giây/method/instance; benchmark chính dự kiến 300 giây/method/instance, một luồng.
- Hoàn thiện pipeline bảng CSV và hình bằng `cnsplots`; có bản nháp phần MIP và Experimental Setup trong LaTeX.

## Tập dữ liệu hiện khóa

| Instance | n | m | Max degree | Vai trò |
|---|---:|---:|---:|---|
| JGL009 | 9 | 32 | 8 | Nhỏ, dày |
| BCSSTK01 | 48 | 176 | 11 | Trung bình |
| BP 400 | 822 | 4,015 | 294 | Lớn, thưa; kiểm tra giới hạn |

`m` là số cạnh vô hướng duy nhất sau chuẩn hóa, không phải số nonzero trong ma trận gốc. JGL009 trong Table A.2 báo 50 entries, nhưng đồ thị chuẩn hóa của repo có 32 cạnh. Chỉ so với paper khi đã đối chiếu cùng quy ước.

## Pilot dry-run và solver run thực tế

- JGL009: MIP 82 biến, 2,610 ràng buộc.
- BCSSTK01: MIP 2,305 biến, 405,600 ràng buộc.
- BP 400: MIP 2,712,872,904 ràng buộc, bị chặn trước khi dựng model bởi `max_constraints=1,000,000`.
- Pilot thật tại commit `71d4baf`: Gurobi 14.0.0 và CPLEX 22.2.0.0 đều đã được gọi trên JGL009 và BCSSTK01, nhưng cả hai trả `license_error`.
  - Gurobi: `Model too large for size-limited license`.
  - CPLEX: Error 1016, `Community Edition. Problem size limits exceeded`.
  - Đây là giới hạn edition/license, không phải timeout, infeasible hay bằng chứng mô hình sai.
- Các dòng BP 400 có `error_type=preflight_model_size_limit`; solver chưa được khởi chạy.
- `results/smoke.jsonl` có kết quả OPTIMAL cho `path5` và `cycle6` trên cả hai MIP, nhưng các record mang `commit_hash=778db217`, không phải commit hiện tại `71d4baf`. Cần chạy lại smoke ở commit hiện tại trước khi dùng làm bằng chứng nghiệm thu của snapshot này.

## Kiểm thử trong môi trường rà soát

- `compileall`: thành công.
- Các test không phụ thuộc Python-SAT được chạy lại: 83 passed, 22 subtests passed.
- Full suite trong môi trường rà soát không thu thập được hai module SAT vì môi trường này thiếu `python-sat`; trên máy Windows của Hưng đã có lần chạy full suite 113 passed, 22 subtests passed.
- Manifest benchmark và excluded: hợp lệ (3 benchmark, 1 excluded).
- MIP pilot dry-run và main benchmark dry-run: thành công; main config có 12 lượt cho 4 phương pháp hiện kích hoạt, CP-SAT và CPLEX CP vẫn đang là phương pháp pending.
- Plot `--check-only`: sinh bảng CSV cho 6 record pilot và 3 dataset.
- Package `cnsplots` chưa được cài/chạy thật trong môi trường rà soát. Đã bổ sung extra `plots` vào `pyproject.toml` để lệnh cài đặt trong handoff hoạt động.
- Bổ sung sơ đồ CBMP tĩnh tại `report/figures/cbmp_circular_layout.pdf` để báo cáo không thiếu hình. `pdflatex` biên dịch qua được phần nội dung (4 trang); chưa xác nhận bibliography hoàn chỉnh vì `bibtex` trong môi trường rà soát bị lỗi quyền thực thi.

## Việc cần nhóm trưởng/Đức tiếp tục

- CP-SAT và CPLEX CP hiện vẫn là adapter `NotImplementedError`; cổng ngày 7 cho đủ sáu phương pháp chưa đạt. Không chạy batch chính thức sáu phương pháp trước khi hai adapter này hoàn thiện và qua kiểm chứng nhỏ.
- Sau khi cài `cnsplots`, chạy script sinh hình từ JSONL thật.
- Mở rộng manifest từ candidate list chỉ sau khi tải raw matrix, chuẩn hóa, kiểm checksum và xác nhận đúng đồ thị.
- Nhờ Hùng/Đức chạy `mip_smoke.json` trên máy có solver; sau đó chạy `mip_pilot.json` để xác nhận license đủ quyền cho model Harwell–Boeing (toy smoke có thể chạy được cả với license giới hạn).

## Lệnh trên máy Windows

```cmd
py -3.14 -m pip install -e ".[plots]"
py -3.14 -m pytest tests -v
py -3.14 scripts\validate_manifest.py
py -3.14 scripts\benchmark.py --config configs\mip_smoke.json --no-resume
py -3.14 scripts\benchmark.py --config configs\mip_pilot.json --dry-run
py -3.14 scripts\benchmark.py --config configs\mip_pilot.json --no-resume
py -3.14 scripts\plot_results.py --input results\mip_pilot.jsonl --manifest data\manifest.csv --output-dir results\mip_pilot_summary
```

`mip_smoke.json` chỉ xác nhận adapter hoạt động trên toy; `mip_pilot.json` mới kiểm tra license có chạy được mô hình Harwell–Boeing hay không. Chỉ chạy `configs/benchmark.json` sau khi nhóm xác nhận đủ sáu phương pháp và cổng tích hợp đã đạt.
