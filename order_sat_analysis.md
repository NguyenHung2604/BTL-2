# Phân tích SAT/UNSAT và So sánh Rebuilt vs. Incremental trong CBMP (Order Encoding)

Tài liệu này phân tích hành vi thỏa mãn (**SAT / UNSAT**) của công thức CNF sinh bởi **Order Encoding** (`order.py`) theo ngưỡng băng thông vòng $k$, đồng thời so sánh hai chiến lược giải tìm giá trị tối ưu $k^*$: **Rebuilt** và **Incremental**.

---

## 1. Phân tích trạng thái SAT / UNSAT theo ngưỡng $k$

Xét đồ thị vô hướng $G = (V, E)$ cố định với $n = \vert{}V\vert{}$ đỉnh và $m = \vert{}E\vert{}$ cạnh. Gọi $F(k)$ là tập mệnh đề CNF sinh bởi `order.build(graph, k)`.

### 1.1. Tính đơn điệu của bài toán quyết định

Nếu tồn tại một hoán vị hợp lệ $p$ của $\{0, 1, \dots, n-1\}$ thỏa mãn $\text{cbw}(p) \le k_0$ (tức $F(k_0)$ là **SAT**), thì với mọi $k \ge k_0$, chính hoán vị $p$ đó cũng thỏa mãn $\text{cbw}(p) \le k_0 \le k$. Do đó, trạng thái thỏa mãn của $F(k)$ có tính đơn điệu theo $k$:

$$
\underbrace{\text{UNSAT}(0),\; \dots,\; \text{UNSAT}(k^* - 1)}_{\text{Vùng UNSAT}},\; \underbrace{\text{SAT}(k^*),\; \dots,\; \text{SAT}(\lfloor n/2 \rfloor)}_{\text{Vùng SAT}}
$$

trong đó $k^*$ là cyclic bandwidth tối ưu của đồ thị $G$.

### 1.2. Các mốc biên của $k$

* **Khi $k < 0$:** Khoảng cách vòng luôn không âm nên không tồn tại nghiệm hợp lệ. `order.build` trả về mệnh đề rỗng `[[]]`, luôn **UNSAT**.
* **Khi $k = 0$:** Chỉ có thể **SAT** nếu đồ thị không có cạnh ($m = 0$) hoặc $n \le 1$. Khi $m \ge 1$ và $n \ge 2$, mọi cặp đỉnh kề nhau đều phải nhận vị trí phân biệt nên khoảng cách vòng ít nhất bằng $1$, dẫn đến $F(0)$ luôn **UNSAT**.
* **Khi $k \ge \lfloor n/2 \rfloor$:** Khoảng cách vòng tối đa giữa hai vị trí bất kỳ trên đường tròn $n$ đỉnh là $\lfloor n/2 \rfloor$. Mọi hoán vị đều đạt $\text{cbw}(p) \le \lfloor n/2 \rfloor \le k$, do đó $F(k)$ luôn **SAT** (và `order.build` bỏ qua việc sinh các mệnh đề cấm cặp vị trí cạnh).

### 1.3. Đặc điểm thực nghiệm giữa hai vùng

* **Vùng UNSAT ($k < k^*$):**
  * Ở các mức $k$ nhỏ, số cặp vị trí $(i, j)$ có $d_c(i, j) > k$ lớn, khiến số lượng mệnh đề cấm cạnh $\mathcal{O}(m \cdot n^2)$ tăng cao.
  * CDCL có thể loại nhiều cách xếp bằng một mệnh đề học được. Thời gian chứng minh UNSAT phụ thuộc đồ thị và ngưỡng; log cần ghi riêng từng lần gọi.
* **Vùng SAT ($k \ge k^*$):**
  * Không gian nghiệm mở rộng dần khi $k$ tăng, đồng thời kích thước công thức CNF giảm xuống.
  * Ngay khi solver tìm được một mô hình thỏa mãn, `order.decode` giải mã chuỗi ngưỡng đơn điệu thành hoán vị hợp lệ trên $\{0, \dots, n-1\}$.

---

## 2. So sánh rebuilt với incremental

Thứ tự chọn ngưỡng và vòng đời của solver là hai lựa chọn độc lập. Trong thí nghiệm `scripts/sat_ablation.py`, cả hai bản order giảm từng đơn vị từ cận trên ban đầu. Bản rebuilt dựng toàn bộ CNF và mở Glucose3 mới mỗi lần. Bản incremental giữ một Glucose3, nạp các ràng buộc hoán vị một lần và chỉ thêm các mệnh đề cấm những cặp vị trí vừa vượt ngưỡng. Cách này dùng được khi ngưỡng chỉ giảm. Quét tăng hoặc tìm kiếm nhị phân có bước nới ngưỡng sẽ cần cơ chế vô hiệu hóa ràng buộc cũ.

Trên đường đi 8 đỉnh được đánh số xáo trộn, cả hai đi qua K = 3, 2, 1 và đạt tối ưu 1. Tổng số mệnh đề đã nạp là 1320 với rebuilt và 552 với incremental. Trên đồ thị hai phía đầy đủ K₃,₃, cả hai chứng minh UNSAT ở K = 2, xác nhận nghiệm tối ưu 3. Trên JGL009, cận đầu đã khớp nên số lần gọi SAT là 0.

Thí nghiệm pairwise so sánh riêng việc cố định đỉnh 0 ở vị trí 0; phép quay bảo toàn mọi khoảng cách vòng. Xem `results/raw/week8_ablation.jsonl` để đối chiếu cận, nghiệm, thời gian và lịch sử từng ngưỡng.
