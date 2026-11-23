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
  * SAT solver (CDCL) phải duyệt và loại bỏ toàn bộ không gian hoán vị để chứng minh không tồn tại lời giải hợp lệ, nên thời gian giải trên mỗi lần gọi thường lớn hơn đáng kể so với vùng SAT.
* **Vùng SAT ($k \ge k^*$):**
  * Không gian nghiệm mở rộng dần khi $k$ tăng, đồng thời kích thước công thức CNF giảm xuống.
  * Ngay khi solver tìm được một mô hình thỏa mãn, `order.decode` giải mã chuỗi ngưỡng đơn điệu thành hoán vị hợp lệ trên $\{0, \dots, n-1\}$.

---

## 2. So sánh chiến lược Rebuilt và Incremental

Để tìm giá trị băng thông vòng tối ưu $k^*$, có thể tiếp cận theo hướng dựng lại độc lập từng bước (**Rebuilt**) hoặc tìm kiếm/tái sử dụng có hệ thống qua các ngưỡng $k$ (**Incremental**).

| Tiêu chí so sánh | Rebuilt (Dựng lại độc lập từng mức $k$) | Incremental (Tìm kiếm / tái sử dụng theo ngưỡng $k$) |
| :--- | :--- | :--- |
| **Cơ chế hoạt động** | Với mỗi giá trị $k$ cần kiểm tra, gọi `order.build(graph, k)` để sinh lại toàn bộ `clauses` và khởi tạo một phiên SAT solver mới từ đầu. | Thu hẹp dải tìm kiếm $k \in [lo, hi]$ (tăng dần từ $0$ đến khi gặp SAT đầu tiên, hoặc tìm kiếm nhị phân), hoặc giữ một phiên solver duy nhất với biến kích hoạt (*assumption literals*) cho từng ngưỡng $k$. |
| **Chi phí dựng công thức** | Lặp lại việc sinh các mệnh đề cấu trúc cố định (đơn điệu $\mathcal{O}(n^2)$ và all-different $\mathcal{O}(n^3)$) ở mọi lần thử $k$. | Giảm số lần gọi `build`/`solve` nhờ thu hẹp miền $k$; nếu dùng *assumptions* trên cùng solver, phần mệnh đề cấu trúc chỉ cần nạp một lần duy nhất. |
| **Tận dụng tri thức học được (Learnt Clauses)** | Không chia sẻ mệnh đề học được giữa các lần chạy solver khác nhau. | Giữ lại các mệnh đề xung đột (*learnt clauses*) về cấu trúc hoán vị và ràng buộc đồ thị khi dùng chung một thực thể solver qua các mức $k$. |
| **Mức độ tương thích với `order.py`** | Tương thích trực tiếp 100% với hàm `order.build(graph, k)` hiện tại. | Với `order.build(graph, k)` hiện tại, có thể áp dụng ngay ở tầng tìm kiếm (quét tuyến tính hoặc binary search). Nếu muốn incremental ở mức mệnh đề, cần gắn thêm literal điều kiện cho từng ngưỡng $k$. |
| **Độ phức tạp cài đặt & kiểm thử** | Đơn giản, mỗi lần chạy độc lập nên dễ kiểm tra và khoanh vùng lỗi `build` / `decode`. | Cần quản lý chặt cận tìm kiếm $[lo, hi]$ hoặc trạng thái biến giả định giữa các bước giải. |

---

## 3. Khuyến nghị áp dụng trong thực nghiệm

1. **Tận dụng cận dưới tự nhiên:** Với đồ thị có $n \ge 2$ và $m \ge 1$, luôn bắt đầu tìm kiếm từ $lo = 1$ thay vì $0$ vì $k = 0$ chắc chắn **UNSAT**.
2. **Chọn chiến lược theo kích thước đồ thị:**
   * Trên các đồ thị nhỏ (`data/toy/`), quét tăng dần từ $k = 1$ lên đến khi gặp **SAT** đầu tiên cho kết quả nhanh, dễ quan sát ranh giới **UNSAT $\to$ SAT** và thuận tiện đối chiếu với kết quả tối ưu từ CP/MIP.
   * Trên các đồ thị trung bình và lớn (`data/pilot/`), nên sử dụng **tìm kiếm nhị phân (Binary Search)** trên đoạn $[lo, \lfloor n/2 \rfloor]$ để giảm số lần gọi solver từ $\mathcal{O}(n)$ xuống $\mathcal{O}(\log n)$, hạn chế số lần phải giải các bài toán khó ở vùng **UNSAT**.