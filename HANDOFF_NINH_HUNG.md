# Handoff — phần dữ liệu, MIP và benchmark của Hưng

## Đã hoàn thiện trong bản này

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

## Pilot dry-run đã kiểm tra

- JGL009: MIP 82 biến, khoảng 2,610 ràng buộc.
- BCSSTK01: MIP 2,305 biến, khoảng 405,600 ràng buộc.
- BP 400: MIP 2,712,872,904 ràng buộc, bị chặn trước khi dựng model.
- Với SAT, cận trên clause của BP 400 cũng vượt guard; runner không khởi chạy SAT.

## Kiểm thử trong môi trường rà soát

- `compileall`: thành công.
- Các test được chạy trong môi trường rà soát: 83 passed, 22 subtests passed.
- 8 test MIP bị skip do môi trường rà soát không có Gurobi/CPLEX.
- Không thể thu thập hai module SAT trong môi trường rà soát do thiếu `python-sat`; máy của Hưng trước đó đã chạy 101 test pass trước các thay đổi này. Cần chạy lại full suite trên máy có `python-sat`.
- Dry-run manifest/pilot/main config: thành công.
- Logic biểu đồ đã kiểm tra với shim Matplotlib/Seaborn; package `cnsplots` thật chưa được cài trong môi trường rà soát.
- Chưa chạy solver pilot thật; không có số liệu runtime hay kết luận hiệu năng trong bản này.

## Việc cần nhóm trưởng/Đức tiếp tục

- CP-SAT và CPLEX CP hiện vẫn là adapter `NotImplementedError`; cổng ngày 7 cho đủ sáu phương pháp chưa đạt. Không chạy batch chính thức sáu phương pháp trước khi hai adapter này hoàn thiện và qua kiểm chứng nhỏ.
- Sau khi cài `cnsplots`, chạy script sinh hình từ JSONL thật.
- Mở rộng manifest từ candidate list chỉ sau khi tải raw matrix, chuẩn hóa, kiểm checksum và xác nhận đúng đồ thị.

## Lệnh trên máy Windows

```cmd
py -3.14 -m pip install -e ".[plots]"
py -3.14 -m pytest tests -v
py -3.14 scripts\validate_manifest.py
py -3.14 scripts\benchmark.py --config configs\mip_pilot.json --dry-run
py -3.14 scripts\benchmark.py --config configs\mip_pilot.json --no-resume
py -3.14 scripts\plot_results.py --input results\mip_pilot.jsonl --manifest data\manifest.csv --output-dir results\mip_pilot_summary
```

Chỉ chạy `configs/benchmark.json` sau khi nhóm xác nhận đủ sáu phương pháp và cổng tích hợp đã đạt.
