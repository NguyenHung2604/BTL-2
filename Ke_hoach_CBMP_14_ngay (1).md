# KẾ HOẠCH BTL 2 — CYCLIC BANDWIDTH MINIMIZATION PROBLEM

**Nhóm:** Nguyễn Minh Hùng (nhóm trưởng), Nguyễn Minh Đức, Ninh Ngọc Hưng.  
**Thời gian:** 14 ngày tính từ buổi khởi động của nhóm. Đánh dấu lại các việc đã xong trước khi xếp lịch phần còn lại.  
**Ngân sách:** 42 giờ/người, 126 giờ toàn nhóm, gồm họp, lập trình, kiểm thử, viết và sửa báo cáo. Thời gian máy chạy tự động tính riêng. Các ước lượng cần hiệu chỉnh sau ngày 3.

## 1. Kết luận sau khi đọc toàn bộ ZIP

ZIP chứa đúng 3 PDF, tổng cộng 61 trang; không chứa mã nguồn, dữ liệu benchmark hay bộ nguồn LaTeX.

| Tài liệu | Số trang PDF | Vai trò |
|---|---:|---|
| Assignment 2 - requirements.pdf | 2 | Nguồn yêu cầu chính thức. Dòng CBMP yêu cầu pairwise encoding và order encoding. |
| 3 - Cyclic Bandwidth Minimization Problem - CBMP.pdf | 27 | Bài “A new iterated local search algorithm for the cyclic bandwidth problem”, Ren và cộng sự, bản sửa tháng 4/2020. Cung cấp định nghĩa, heuristic NILS, benchmark và thực nghiệm; không cung cấp sẵn hai SAT encoding phải cài. |
| Mau xay dung bao cao BTL so 1 và BTL so 2.pdf | 32 | Bài mẫu “Exact SAT Solving for the Two-Dimensional Bandwidth Minimization Problem”. Học cấu trúc bài báo, chứng minh, ablation và cách phân biệt feasible/optimal; không dùng mô hình lưới của bài này làm mô hình CBMP. |

### Ma trận đáp ứng yêu cầu

| Mức | Yêu cầu từ tài liệu | Sản phẩm kiểm tra được | Phụ trách |
|---|---|---|---|
| Bắt buộc riêng CBMP | Pairwise encoding | Công thức CNF, mã hóa, giải mã, test và kết quả | Hùng |
| Bắt buộc riêng CBMP | Order encoding | Biến ngưỡng, miền, all-different, khoảng cách vòng, chứng minh và test | Đức |
| Yêu cầu chung | So sánh SAT với CPLEX CP, CPLEX MIP, Gurobi, CP-SAT | Bốn adapter, mô hình minh bạch và bảng kết quả trên cùng dữ liệu | Chia ba người ở mục 3 |
| Yêu cầu chung | Thực nghiệm kích thước lớn | Dải kích thước tăng dần; báo cáo cả timeout/OOM và giới hạn mở rộng | Hưng điều phối |
| Yêu cầu chung | Bài báo khoa học, Elsevier cas-sc | Nguồn LaTeX và PDF biên dịch được | Cả ba |
| Yêu cầu chung | Data Availability có link repository | Mã nguồn, cấu hình, dữ liệu hoặc hướng dẫn lấy dữ liệu, kết quả thô | Hùng kiểm tra |
| Yêu cầu chung | Dùng cnsplots để visualize | Script tái sinh hình và hình trong báo cáo | Hưng |
| Khuyến khích | Các encoding AMO/ALO khác | Thử thêm sequential counter trên một phần bộ test | Hùng, sau khi lõi đúng |
| Mở rộng đề xuất | Incremental SAT | So sánh rebuilt/incremental có kiểm soát | Đức, Hùng review |

**Phân biệt quan trọng:** dòng CBMP không ghi bắt buộc chạy cả SAT nhiều lần và incremental như các dòng BMP/BCP. Incremental là phần nâng cao đáng làm khi đủ thời gian. Đề cũng không bắt buộc tái hiện toàn bộ NILS, chạy đủ 113 instance, 50 lần lặp hoặc 600 giây như paper. Không có rubric tỷ trọng điểm, hạn nộp, số trang hay thời lượng thuyết trình cụ thể trong ZIP. Ngày 1 cần hỏi giảng viên các điểm này, đồng thời tiếp tục triển khai lõi.

## 2. Chốt bài toán và phạm vi kỹ thuật

Cho đồ thị đơn vô hướng G=(V,E), n=|V|. Một nghiệm là hoán vị nhãn p(v) thuộc {0,...,n−1}. Khoảng cách vòng:

`d_n(i,j) = min(|i-j|, n-|i-j|)`.

Mục tiêu: `min_p max_{(u,v) in E} d_n(p(u),p(v))`. Quy ước giá trị 0 nếu E rỗng. Ví dụ n=10, vị trí 0 và 9 cách nhau 1, không phải 9. Đây phải là test bắt buộc cho mọi mô hình.

### Hai hướng SAT cần thực hiện

- **Pairwise/direct:** x[v,i] đúng khi p(v)=i; mỗi đỉnh đúng một vị trí, mỗi vị trí tối đa một đỉnh. Với mỗi cạnh (u,v), cấm cặp vị trí (i,j) có d_n(i,j)>K bằng clause `¬x[u,i] ∨ ¬x[v,j]`. Bản chuẩn dùng pairwise AMO, ALO là clause tuyển. Ghi riêng chi phí ràng buộc vị trí và ràng buộc cạnh.
- **Order:** dùng biến ngưỡng, chẳng hạn y[v,k] biểu diễn p(v)≤k, k=0,...,n−2; thêm tính đơn điệu, xử lý biên và all-different. Phải tự suy ra và kiểm thử điều kiện khoảng cách vòng. Đổi AMO từ pairwise sang sequential counter không tự tạo ra order encoding. Ngày 2 thống nhất với giảng viên cách hiểu encoding nếu bài giảng có quy ước riêng.
- Khi triển khai order, chú ý điều kiện tương đương `|p(u)-p(v)|≤K OR |p(u)-p(v)|≥n−K`; chỉ mã hóa nhánh đầu sẽ giải nhầm BMP. Nếu dùng biến equality phụ để nối với biến ngưỡng, ghi rõ đây là cấu trúc lai, công bố đầy đủ clause và chứng minh liên kết hai chiều; không tuyên bố nhỏ hơn khi chưa đếm thực tế.
- Dùng cùng một SAT backend trong so sánh hai encoding để hạn chế yếu tố gây nhiễu. Mỗi encoding có hàm build và decode độc lập.

### Tối ưu và chứng minh tối ưu

Dùng bài toán quyết định F(K): tồn tại hoán vị có CB≤K hay không. Khởi đầu với cận dưới `ceil(Δ(G)/2)` và cận trên từ một hoán vị hợp lệ đã kiểm tra, luôn không quá `floor(n/2)`. Với đồ thị không cạnh xử lý riêng giá trị 0. Cận bậc đến từ việc quanh một vị trí chỉ có tối đa 2K vị trí khác cách không quá K.

Bản đầu dùng tìm kiếm giảm ngưỡng, tạo solver mới mỗi lần: giải ở K; nếu SAT, giải mã, kiểm tra, tính băng thông thực B rồi thử B−1. Chỉ ghi OPTIMAL khi có nghiệm B và UNSAT ở B−1, hoặc B bằng cận dưới hợp lệ. Timeout/UNKNOWN không phải UNSAT. Một nghiệm khả thi không tự chứng minh tối ưu.

Mở rộng incremental dùng cùng chuỗi giảm K, giữ solver và chỉ bổ sung ràng buộc siết ngưỡng; kiểm tra tương đương với rebuilt. Nếu sau này tìm kiếm nhị phân và cần nới ngưỡng, không giữ nguyên các clause siết chặt trước đó mà thiếu cơ chế kích hoạt phù hợp.

### Mô hình đối chứng

- CPLEX CP và CP-SAT: biến vị trí nguyên, all-different, ràng buộc khoảng cách vòng và biến mục tiêu. Hai backend phải thực hiện cùng bài toán.
- CPLEX MIP và Gurobi: cùng một đặc tả ILP để so sánh backend công bằng. Có thể dùng biến gán và các ràng buộc điều kiện cho từng cặp vị trí; chọn formulation sau pilot, kiểm tra độ lớn mô hình trước khi chạy lớn.
- Ngày 1–2 chạy ví dụ thật trên cả bốn engine. Cài được Python package chưa phải bằng chứng engine và giấy phép chạy được bài lớn. Không mặc định CPLEX MIP chạy được thì CPLEX CP cũng chạy được.

## 3. Phân công đồng đều theo nỗ lực

| Người | Công việc và ngân sách giờ | Tổng |
|---|---|---:|
| **Nguyễn Minh Hùng — nhóm trưởng** | Đặc tả chung, repo, quyết định phạm vi (4h); pairwise và decode (10h); CP-SAT (6h); chứng minh pairwise, review order (4h); phân tích SAT/ablation (4h); viết phần được giao (6h); họp, tích hợp, nghiệm thu, dự phòng (8h) | **42h** |
| **Nguyễn Minh Đức** | Thiết kế và cài order encoding (13h); CPLEX CP (6h); chứng minh order và kiểm thử biên (5h); incremental sau cổng ngày 7 hoặc sửa lõi (4h); viết phần được giao (6h); họp, review, hỗ trợ và dự phòng (8h) | **42h** |
| **Ninh Ngọc Hưng** | Đặc tả ILP chung, adapter Gurobi và CPLEX MIP (11h); dữ liệu, brute-force nhỏ và validator độc lập (7h); benchmark runner, log, resume (6h); cnsplots và sinh bảng (4h); viết phần được giao (6h); họp, review, đóng gói và dự phòng (8h) | **42h** |

**Tính công bằng:** mỗi người đều có code, kiểm chứng, thực nghiệm và viết. Hùng có thời gian quản lý được tính vào tải, không nhận thêm toàn bộ báo cáo. Đức gánh phần order khó nên không giao thêm quản trị benchmark. Hưng có hai backend MIP dùng chung formulation, không thiết kế hai mô hình hoàn toàn khác nhau.

**Review vòng:** Đức review Hùng; Hùng review Đức; Hưng kiểm tra nghiệm của cả hai; Đức review mô hình MIP của Hưng. Người viết không tự là người duy nhất duyệt tính đúng.

## 4. Lịch làm việc 14 ngày

Mỗi ngày dự kiến khoảng 3 giờ/người; giờ chạy máy không tính là giờ ngồi làm. Có thể chia thành hai phiên 75–90 phút và cập nhật ngắn, không cần cố định giờ nếu lịch học thay đổi.

| Ngày | Hùng | Đức | Hưng | Mốc nghiệm thu chung |
|---|---|---|---|---|
| **1** | Họp khởi động; đặc tả, repo, hợp đồng đầu vào/ra; tập hợp câu hỏi gửi thầy | Đọc order, phác biến/ràng buộc; kiểm tra CPLEX CP | Kiểm tra MIP/Gurobi; lập danh mục ma trận Harwell–Boeing và quy tắc đọc | Một trang scope; mỗi việc có chủ; tình trạng 4 engine rõ ràng |
| **2** | Viết công thức pairwise và test khoảng cách vòng | Viết đặc tả order, all-different và các trường hợp biên | Đặc tả ILP; chuyển thử một ma trận Harwell–Boeing; brute-force n≤8 | Cả ba tính cùng đáp án trên ví dụ tay; review mô hình trước code lớn |
| **3** | Pairwise build/decode đầu tiên | Order build/decode đầu tiên | Validator và Gurobi đầu tiên | Hai SAT chạy được test nhỏ; chốt lại ước lượng tải |
| **4** | Vòng giảm ngưỡng, trạng thái và CP-SAT | Sửa order theo test; CPLEX CP đầu tiên | CPLEX MIP từ ILP chung; chuẩn hóa dữ liệu | Mỗi engine có ít nhất một kết quả được validator xác nhận |
| **5** | Hoàn thiện CP-SAT; kiểm tra optimal/timeout | Hoàn thiện CPLEX CP, chứng minh order | Runner, timeout tiến trình và kết quả JSON/CSV | Sáu phương pháp đi qua cùng pipeline; test chéo nhỏ |
| **6** | Pilot pairwise và CP-SAT | Pilot order và CP | Pilot hai MIP; ước lượng RAM, thời gian | Pilot 3–5 ma trận Harwell–Boeing khác nhau về kích thước và mật độ; chọn timeout và giới hạn RAM |
| **7** | Review, sửa tích hợp; viết pairwise và khung bài | Review order, hoàn thành proof; viết mục order | Khóa danh sách ma trận Harwell–Boeing và checksum, runner; viết setup và MIP | **Bản lõi đủ yêu cầu chạy được; đóng băng giao diện** |
| **8** | Thử symmetry hoặc AMO sequential nếu lõi đạt | Thử incremental nếu lõi đạt; nếu chưa thì sửa lỗi | Khởi chạy batch chính thức; thử pipeline biểu đồ | Một cải tiến có đối chứng; báo cáo đã có nội dung phương pháp |
| **9** | Phân tích số biến/clause và thời gian encode | Phân tích SAT/UNSAT, so rebuilt/incremental | Theo dõi batch; chạy resume; hình và bảng lần 1 | Có dữ liệu thật; không còn bảng kết quả điền tay |
| **10** | Viết so sánh hai encoding | Viết ablation và lập luận tối ưu | Viết đối chứng ILP/CP và scalability | **Dừng thêm tính năng; chốt cấu hình báo cáo** |
| **11** | Viết Introduction, Discussion và giới hạn | Hoàn thiện Background, Related Work, proof | Hoàn thiện Results, captions và phụ lục | Bản thảo đầy đủ, mọi nhận xét gắn với số liệu |
| **12** | Kiểm tra luận điểm và kết quả mâu thuẫn | Kiểm tra toán, ký hiệu, tài liệu tham khảo | Tái chạy từ checkout sạch; kiểm tra bảng–CSV | **Bản PDF hoàn chỉnh; tái lập smoke benchmark thành công** |
| **13** | Ghép bài, sửa abstract/conclusion; hỏi chéo hai bạn | Sửa LaTeX, lỗi tham chiếu; tập giải thích order | Kiểm tra hình, README; tập giải thích fairness | Diễn tập bảo vệ; mỗi người hiểu toàn bộ hệ thống |
| **14** | Duyệt checklist, tag phiên bản, nộp theo hạn thật | Kiểm tra nguồn LaTeX/PDF và proof cuối | Kiểm tra gói dữ liệu/log, link và checksum | **Gói nộp hoàn chỉnh; ngày dự phòng xử lý sự cố** |

### Bốn cổng quyết định

1. **Ngày 3:** nếu một người dự báo vượt tải quá khoảng 20%, chuyển một đầu việc độc lập cho người còn dung lượng; không chuyển mặc định cho nhóm trưởng.
2. **Ngày 7:** chỉ mở cải tiến khi cả hai SAT và bốn đối chứng đã chạy đúng trên bộ kiểm chứng nhỏ, runner ghi trạng thái đúng. Nếu chưa đạt, dùng toàn bộ thời gian cải tiến để hoàn thành lõi.
3. **Ngày 10:** không thêm solver/heuristic/tính năng; chỉ sửa lỗi và chạy bổ sung có lý do.
4. **Ngày 12:** nếu kết quả mâu thuẫn, tạm bỏ kết luận so sánh tương ứng cho đến khi xác minh; không làm đẹp số liệu để giữ câu chuyện.

## 5. Hợp tác và định nghĩa hoàn thành

### Một giao diện chung từ ngày 1

- Đầu vào: graph_id, n, danh sách cạnh duy nhất, cấu hình, seed, ngân sách wall-time, số luồng.
- Đầu ra: method, encoding, solver_version, status, incumbent, lower_bound, optimality_proven, labeling, build_time, solve_time, total_time, peak_memory khi đo được, số biến/clause hoặc biến/ràng buộc, termination_reason, commit_hash.
- Với SAT lưu thêm lịch sử từng K: kết quả SAT/UNSAT/UNKNOWN và thời gian. Với MIP/CP lưu trạng thái gốc và cận do engine trả về.
- Tách status nghiệm (OPTIMAL/FEASIBLE/NO_SOLUTION) khỏi nguyên nhân kết thúc (completed/timeout/OOM/license_error/error). Không gọi lỗi giấy phép là timeout thuật toán.

### Quy trình nhóm

- Một bảng việc gồm Backlog, Doing, Review, Done; mỗi người tối đa hai việc đang làm.
- Mỗi ngày cập nhật ba dòng: đã hoàn thành gì kèm commit/log; đang kẹt gì; bước tiếp theo. Họp ngắn 10 phút; review dài ở ngày 3, 7, 10, 12.
- Kẹt 45–60 phút phải gửi ví dụ lỗi nhỏ, đầu vào và traceback để người khác hỗ trợ; không chờ đến cuối tuần.
- Mỗi nhánh thay đổi nhỏ có một người review. Không để đến ngày 10 mới ghép ba notebook.
- Một task code chỉ Done khi chạy qua giao diện chung, có test quan trọng, nghiệm qua validator và có đoạn giải thích phương pháp. Một task báo cáo chỉ Done khi có nguồn/số liệu, biên dịch và được người khác đọc.
- Mỗi người bàn giao phần mình gồm code + test + đoạn báo cáo + log. Hùng chỉnh thống nhất, không viết lại thay cả nhóm.

Cấu trúc repo đề xuất: `src/encodings/`, `src/backends/`, `src/core/`, `tests/`, `data/manifest.csv`, `configs/`, `results/raw/`, `results/summary/`, `scripts/`, `report/sections/`, `report/figures/`, `README.md`. Dữ liệu lớn dùng hướng dẫn tải cùng checksum nếu không phù hợp đưa vào Git.

## 6. Thiết kế thực nghiệm có sức thuyết phục

### Dữ liệu theo ba lớp

| Lớp | Quy mô đề xuất | Mục đích |
|---|---|---|
| Kiểm chứng | n≤8; path, cycle, complete, star, đồ thị ngẫu nhiên và đồ thị không liên thông | Đối chiếu vét cạn; kiểm tra mọi K từ 0 đến floor(n/2) trên các graph nhỏ đã chọn |
| So sánh chính | Các ma trận Harwell–Boeing đã xác minh nguồn và chuyển đổi thành đồ thị; dùng bảng A.2 của Ren và cộng sự làm danh sách ứng viên | Cả sáu phương pháp dùng cùng manifest; báo rõ số ma trận thực tế và lý do chọn trước khi chạy chính |
| Mở rộng | Nhóm ma trận Harwell–Boeing lớn hơn trong manifest; chọn sau pilot theo số đỉnh, cạnh và RAM | Đo giới hạn xây mô hình và khả năng chứng minh tối ưu; ghi cả timeout và OOM |

**Bộ benchmark chính thức của nhóm là Harwell–Boeing.** Bảng A.2 của bài NILS liệt kê 28 instance của họ này. Chỉ so với giá trị công bố khi đã xác nhận cùng đồ thị và quy ước xử lý. Path/cycle và đồ thị vét cạn nằm trong bộ kiểm thử riêng. Lưu ma trận gốc hoặc hướng dẫn tải và checksum, cạnh chuẩn hóa, số đỉnh, số cạnh và bậc lớn nhất. Giữ lại danh sách các ma trận bị loại cùng lý do.

Từ ma trận: chốt đồ thị vô hướng theo mẫu khác 0 ngoài đường chéo; nếu cần đối xứng hóa dùng quy tắc rõ ràng A[i,j]≠0 hoặc A[j,i]≠0; bỏ self-loop, gộp cạnh trùng, giữ đỉnh cô lập. Lưu n, số cạnh vô hướng sau chuẩn hóa và checksum. Không đồng nhất số phần tử khác 0 với số cạnh. Bảng trong tài liệu có các con số không thể là số cạnh đồ thị đơn (chẳng hạn n=9 và |E|=50); cần kiểm tra quy ước dữ liệu trước khi đối chiếu, không sao chép mù quáng.

### Kiểm chứng bắt buộc trước benchmark

- Validator độc lập kiểm tra nhãn là hoán vị và tự tính lại max khoảng cách vòng.
- Duyệt hoán vị trên graph rất nhỏ để đối chiếu cả đáp án tối ưu và SAT/UNSAT từng K.
- Kiểm tra n chẵn/lẻ, wrap-around 0 và n−1, K=0, K=floor(n/2), đỉnh cô lập, graph rỗng cạnh.
- Test path có cạnh và cycle có tối ưu 1; complete graph có tối ưu floor(n/2). Kiểm tra lại bằng lập luận hoặc vét cạn trên kích thước nhỏ.
- Cùng dữ liệu, nếu hai phương pháp đều báo OPTIMAL mà đáp án khác nhau thì ít nhất một pipeline có lỗi: dừng dùng hàng đó để kết luận.

### Ngân sách và so sánh công bằng

- Pilot 30–60 giây/instance/phương pháp; đề xuất batch chính 300 giây, gồm xây mô hình và mọi lần gọi solver của bài toán tối ưu. Điều chỉnh một lần sau pilot, trước khi xem kết quả chính.
- Không cấp 300 giây cho từng K của SAT rồi so với 300 giây cho toàn bộ MIP.
- Ưu tiên cùng máy, cùng giới hạn RAM, một luồng cho bảng chính khi backend hỗ trợ. Nếu dùng nhiều máy, mỗi máy chạy đủ các phương pháp trên cùng nhóm instance và báo cáo tách theo máy; không chia mỗi người một solver rồi gộp tốc độ trực tiếp.
- Nếu dùng đủ 28 ma trận × 6 phương pháp × 300 giây, ngân sách tối đa là 14 giờ máy nếu mọi lượt chạm trần; 3 lần lặp là 42 giờ, chưa gồm ablation. Chạy batch từ ngày 8.
- Chạy lặp 3 lần trên tập chính nếu đủ tài nguyên; nếu không, một lượt đầy đủ và 3 lượt trên tập đại diện chọn trước. Nêu rõ giao thức, median/range; ba lần lặp không tự đủ để tuyên bố ý nghĩa thống kê.
- Log thời gian build/load/solve và end-to-end; khi timeout vẫn giữ nghiệm tốt nhất đã kiểm tra. Không xóa các dòng thất bại.

### Câu hỏi nghiên cứu và hình cần có

1. **RQ1:** hai encoding khác nhau thế nào về số biến, clause, thời gian encode và tỷ lệ chứng minh tối ưu?
2. **RQ2:** SAT cạnh tranh với bốn đối chứng ra sao dưới cùng ngân sách?
3. **RQ3:** symmetry hoặc incremental có đóng góp riêng không?
4. **RQ4:** số đỉnh, mật độ và bậc lớn nhất của đồ thị Harwell–Boeing ảnh hưởng thế nào đến khả năng mở rộng?

Bộ trình bày mục tiêu: một hình vòng tròn minh họa CBMP; bảng thống kê dataset; bảng OPTIMAL/FEASIBLE/timeout/error; cactus plot số instance chứng minh tối ưu theo thời gian; scatter thời gian pairwise/order với đường y=x và ký hiệu timeout; hình số clause/RAM theo quy mô; một bảng ablation. Tạo hình thực nghiệm bằng cnsplots theo yêu cầu. Hình phải có đơn vị, chú thích và mô tả tập mẫu. Không cần chèn đủ mọi loại hình nếu trùng thông tin.

Nếu báo cáo gap, dùng `(UB−LB)/max(1,UB)` và ghi đây là độ rộng cận tương đối; không gọi khoảng cách tới tối ưu thật khi chưa biết tối ưu. So sánh thời gian trên tập cùng chứng minh tối ưu phải kèm tỷ lệ giải được toàn bộ tập để tránh thiên lệch chỉ nhìn ca dễ.

## 7. Điểm nhấn nên đầu tư

### Ưu tiên 1 — Tính đúng và chứng minh tối ưu

Chứng minh hai chiều cho từng encoding: nghiệm bài toán sinh được mô hình CNF; mô hình CNF giải mã thành hoán vị hợp lệ, mọi cạnh có khoảng cách vòng≤K. Trình bày soundness/completeness và chứng minh vòng giảm K. Kèm một ví dụ thật: có nghiệm B, UNSAT ở B−1. Nếu chỉ có log solver thì gọi là chứng nhận tối ưu theo kết quả solver; không gọi là chứng cứ UNSAT được kiểm tra độc lập nếu chưa xuất và kiểm chứng proof.

### Ưu tiên 2 — Phá đối xứng có lập luận

Cố định một đỉnh neo p(a)=0 vì quay toàn bộ vòng không đổi khoảng cách. Có thể thêm p(b)<p(c) cho hai đỉnh phân biệt khác a để chọn một trong hai chiều phản xạ khi n≥3. Chứng minh phép phản xạ sau neo giữ tính hợp lệ. Chạy ablation bật/tắt với cùng cấu hình; không tự cố định thêm nhiều đỉnh vào vị trí tùy ý.

### Ưu tiên 3 — Incremental hoặc AMO ablation

Chọn một cải tiến sau ngày 7. So sánh cùng solver, cùng thứ tự ngưỡng, cùng cận đầu và cùng giới hạn. Muốn tách hiệu ứng AMO khỏi biểu diễn nhãn, giữ các phần còn lại không đổi. Không gộp thay solver, đổi AMO và bật symmetry rồi quy toàn bộ cải thiện cho order encoding.

### Chỉ làm nếu dư thời gian

Dùng heuristic đơn giản tạo upper bound; đưa cùng upper bound cho các phương pháp hoặc công bố rõ lợi thế khởi tạo và tính cả thời gian heuristic. Không đặt mục tiêu cài đầy đủ NILS, làm giao diện web hay tạo thuật toán “mới” trong hai tuần khi các yêu cầu chính chưa hoàn thành.

## 8. Viết báo cáo như một nghiên cứu nhỏ

Tên gợi ý: **Exact SAT Encodings for the Cyclic Bandwidth Minimization Problem: A Comparative Study**. Chỉ đưa “Incremental” vào tiêu đề nếu thực sự có cài đặt và thí nghiệm đó.

| Phần | Nội dung cần đạt | Người viết chính | Người review |
|---|---|---|---|
| Abstract | Bài toán, hai encoding, thiết lập, kết quả định lượng thật và giới hạn; viết cuối | Hùng | Đức, Hưng |
| Introduction | Động lực, khoảng trống được khảo sát, 3 đóng góp cụ thể | Hùng | Đức |
| Background / Related Work | CBMP khác BMP/2DBMP; định nghĩa, cận, NILS và phương pháp exact | Đức | Hùng |
| Pairwise encoding | Biến, nhóm clause, ví dụ, độ lớn và chứng minh | Hùng | Đức |
| Order encoding | Biến ngưỡng, all-different, wrap-around, chứng minh | Đức | Hùng |
| Exact baselines | ILP chung của hai MIP; mô hình CP và CP-SAT | Hưng; Đức/Hùng bổ sung backend mình | Cả ba |
| Experimental setup | Dataset, tiền xử lý, máy, phiên bản, giới hạn, seed, trạng thái | Hưng | Đức |
| Results | Hưng viết đối chứng/scalability; Hùng viết hai encoding; Đức viết ablation | Cả ba | Review chéo |
| Discussion / Conclusion | Giải thích thắng/thua, giới hạn và kết quả được dữ liệu hỗ trợ | Hùng | Đức, Hưng |
| Appendix / Data Availability / Contributions | Proof dài, bảng đầy đủ, link repo, cách tái lập và đóng góp thực tế | Mỗi người phần mình; Hưng đóng gói | Hùng |

Đề xuất 10–14 trang nội dung chính, phụ lục riêng nếu cần; đây là lựa chọn lập kế hoạch, cần theo giới hạn giảng viên nếu có. Báo cáo cuối dùng LaTeX `\documentclass[a4paper,fleqn]{cas-sc}` như đề yêu cầu. Có thể viết nháp bằng tiếng Việt; xác nhận ngôn ngữ nộp với giảng viên ngày 1.

### Cách trình bày để thuyết phục

- Mỗi công thức giải thích biến, miền, ý nghĩa và lý do đúng; không chỉ chép một khối ký hiệu.
- Mỗi biểu đồ phải trả lời một câu hỏi. Sau hình viết “quan sát → bằng chứng → giải thích có cơ sở → giới hạn”.
- Công bố cả trường hợp SAT thua, order nhiều clause hơn dự kiến, hoặc encoding nhỏ nhưng solve chậm. Đây là thông tin khoa học có giá trị.
- Tách kết quả nhóm chạy khỏi số liệu trích dẫn paper. Không so tốc độ trên máy nhóm với thời gian paper năm 2020 để tuyên bố nhanh hơn.
- Không đưa giá trị tối ưu 2DBMP của bài mẫu sang CBMP, dù tên instance giống nhau.
- Có ba đóng góp vừa sức: hai encoding được kiểm chứng; so sánh công bằng sáu phương pháp; phân tích một yếu tố cải tiến có ablation. Chỉ viết đóng góp đã hoàn thành.
- Không đặt trước kết luận “order luôn tốt hơn pairwise”. Ít biến/clause chưa đủ suy ra solver nhanh hơn.
- Bài mẫu có cả proof và giới hạn nghiên cứu; học cách lập luận, không sao chép abstract, số liệu hay tuyên bố tính mới.

## 9. Rủi ro và phương án xử lý

| Rủi ro | Phát hiện trước | Cách xử lý |
|---|---|---|
| Thiếu engine/giấy phép | Ngày 2 | Ghi lỗi, tìm môi trường học thuật phù hợp; báo giảng viên sớm để thống nhất phương án. Không tự coi bỏ backend là đã đủ yêu cầu. |
| Order sai wrap-around | Ngày 4–5 | Truth table cặp nhãn nhỏ, vét cạn, kiểm tra mọi K; bỏ cải tiến để sửa lõi. |
| CNF tăng quá lớn | Ngày 6 | Đếm clause trước khi cấp phát; giới hạn tài nguyên và log OOM; điều chỉnh dải lớn theo pilot, vẫn báo kết quả giới hạn mở rộng. |
| Benchmark kéo dài | Ngày 6–8 | Tính ngân sách; resume theo run_id; giữ tập chính nhỏ nhưng đa dạng; giảm số lần lặp trước khi bỏ phương pháp bắt buộc. |
| Mỗi người dùng dữ liệu khác | Ngày 2 | Một parser, manifest và checksum chung; validator chung. |
| Trưởng nhóm quá tải | Ngày 3, 7 | Mỗi người tự viết phần code mình; tính giờ quản lý trong 42h; chia lại task độc lập. |
| Cuối kỳ mới viết | Ngày 7 | Method/setup đã có nháp; ngày 10 chỉ điền kết quả đã chốt, ngày 12 có PDF hoàn chỉnh. |

## 10. Checklist trước khi nộp

- [ ] Pairwise và order đều hiện diện, không nhầm order với sequential counter.
- [ ] Khoảng cách vòng, hoán vị và các trường hợp biên được kiểm thử.
- [ ] Bốn backend đối chứng chạy được; mọi ngoại lệ được ghi nhận và thống nhất với giảng viên.
- [ ] Đã thử dữ liệu tăng quy mô; có timeout/OOM rõ ràng nếu xảy ra.
- [ ] Mọi nghiệm báo cáo được validator kiểm tra; mọi OPTIMAL có cơ sở.
- [ ] Time limit tính công bằng cho toàn bài toán, không theo từng K riêng.
- [ ] CSV thô, cấu hình, phiên bản và seed đầy đủ; bảng/hình tái sinh bằng script.
- [ ] Hình thực nghiệm dùng cnsplots, caption đủ thông tin.
- [ ] LaTeX cas-sc và PDF biên dịch được, không lỗi trích dẫn hoặc bảng tràn.
- [ ] Data Availability có link repository nhóm thực tế; kiểm tra quyền truy cập theo yêu cầu nộp.
- [ ] README có cách cài, chạy test, chạy một instance và sinh lại hình; một người khác đã thử từ môi trường sạch.
- [ ] Đóng góp của ba người phản ánh việc thực tế, không chỉ dự kiến.
- [ ] Mỗi người giải thích được mục tiêu, hai encoding, tiêu chí tối ưu, fairness và một kết quả chính.

### Hùng rà soát ngày 24/11/2026

| Hạng mục | Bằng chứng và trạng thái |
|---|---|
| Hai encoding, khoảng cách vòng, hoán vị, điều kiện tối ưu | 68 test và 14 subtest đạt trong `test_encodings.py`, `test_validator.py`, `test_brute_force.py`, `test_search.py`. Discussion đối chiếu hai encoding tại cùng ngưỡng trước khi so tổng toàn lượt. |
| Nghiệm, cận và giới hạn thời gian | Đã chạy lại `certify_record` trên 51 bản ghi của batch năm phương pháp 300 giây, pilot sáu phương pháp 60 giây và rerun sáu phương pháp 300 giây. Cả 30 hoán vị có nghiệm đều khớp bandwidth công bố. Trên BCSSTK01, CP-SAT ở batch đầu chứng minh 12. Hai lượt SAT ở rerun kết thúc UNKNOWN tại ngưỡng cuối. |
| Quy mô và bốn backend đối chứng | Log giữ cả ba đồ thị và các trường hợp timeout, size guard, lỗi license. CPLEX MIP gặp lỗi license trên hai đồ thị nhỏ trong rerun. Việc giảng viên chấp nhận ngoại lệ còn chờ xác nhận. |
| Dữ liệu và khả năng tái hiện | Đối chiếu số biến, tổng clause và thời gian build trong Discussion với lịch sử từng ngưỡng ở JSONL. README có lệnh cài, test, chạy một đồ thị và sinh hình. Việc kiểm tra từ checkout sạch và gói dữ liệu thuộc Hưng. |
| Hình, PDF, trích dẫn | Script sinh hình dùng cnsplots. Báo cáo hiện chèn sơ đồ vòng. Việc duyệt hình thực nghiệm và caption thuộc Hưng. PDF build được với Tectonic và BibTeX. Log còn cảnh báo tràn 117.0831 pt ở phần tạo tiêu đề; công đoạn duyệt LaTeX/PDF cuối thuộc Đức. |
| Data Availability | URL trong báo cáo trùng origin. Đã đọc được HEAD từ GitHub bằng git ls-remote khi tắt credential helper. |
| Đóng góp, bảo vệ và nộp | README ghi phân công ba người. Cần hai bạn xác nhận đóng góp thực tế và trả lời câu hỏi bên dưới trước khi chốt bản nộp. Kế hoạch chưa ghi hạn và kênh nộp chính thức. |

**Câu hỏi Hùng chuẩn bị cho buổi hỏi chéo**

- Đức: Với biến ngưỡng, làm thế nào giải mã hai trường hợp toàn đúng và toàn sai? Vì sao 552 và 1.320 ở scrambled_path8 là tổng clause qua ba ngưỡng? Dùng `order_cp_pilot.jsonl` để phân biệt kết quả order 13 trong pilot riêng trên BCSSTK01 với 14 trong pilot sáu phương pháp có giới hạn bộ nhớ.
- Hưng: Trên BP 400, bằng chứng nào phân biệt việc bị chặn trước khi dựng mô hình với một lần solver chạy hết giờ? Khi đối chiếu CP-SAT trên BCSSTK01, vì sao batch đầu ghi OPTIMAL còn rerun sáu phương pháp ghi FEASIBLE dù cùng đạt 12?

## 11. Nguồn và vị trí đối chiếu

Số trang dưới đây là thứ tự trang PDF, không phải số trang in trong bài mẫu.

1. **Assignment 2 - requirements.pdf:** trang 1, dòng 3 là phạm vi CBMP; trang 2 là đối chứng, LaTeX, thực nghiệm lớn, Data Availability và cnsplots.
2. **3 - Cyclic Bandwidth Minimization Problem - CBMP.pdf:** trang 2 định nghĩa; trang 4–11 NILS; trang 12–14 thiết lập và nguồn dữ liệu; trang 18–20 ablation; trang 23 cận bậc/cận trên; trang 24–27 bảng chi tiết.
3. **Mau xay dung bao cao BTL so 1 và BTL so 2.pdf:** trang 2–5 cách đặt vấn đề và mô hình; trang 6–10 encoding và tối ưu; trang 11–19 thiết lập/kết quả; trang 20–25 chứng minh và cận; trang 26–30 phụ lục số liệu; trang 31 tham khảo.

Tài liệu này là kế hoạch thực hiện, không phải kết quả benchmark đã chạy. Quy mô, số giờ, số trang và thời gian thực nghiệm là đề xuất để nhóm hoàn thành trong hai tuần; chất lượng bài cuối phụ thuộc triển khai và bằng chứng thực tế.
