# Dữ liệu CBMP

Hai đồ thị toy dùng để kiểm tra nhanh. Harwell–Boeing là bộ benchmark chính thức. Lưu ma trận gốc ở `benchmarks/harwell_boeing/raw/` và đồ thị JSON sau chuẩn hóa ở `benchmarks/harwell_boeing/graphs/`.

Với ma trận vuông cấp n, mỗi chỉ số tương ứng một đỉnh đánh số từ 0 đến n−1. Thêm cạnh vô hướng {i,j} khi i khác j và ít nhất một trong hai phần tử A[i,j], A[j,i] khác 0. Gộp cạnh trùng, bỏ khuyên và giữ cả đỉnh cô lập. Đồ thị JSON chứa name, n và edges (các cặp đỉnh).

Mỗi dòng dữ liệu của manifest.csv ứng với một ma trận thật. Các đường dẫn tính từ gốc repo, m đếm cạnh vô hướng sau chuẩn hóa và graph_sha256 là SHA-256 của tệp JSON. Ma trận đầu tiên là BCSSTK01 (48 đỉnh, 176 cạnh, bậc lớn nhất 11). Bản gốc nén dùng định dạng Matrix Market của bộ sưu tập Harwell–Boeing. Hai ứng viên để thử sau là BCSSTK02 và BCSSTK03 trong cùng bộ BCSSTRUC1.
