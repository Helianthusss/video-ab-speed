# HƯỚNG DẪN SỬ DỤNG CHI TIẾT

## Công cụ khảo sát tốc độ phương tiện bằng hai camera A–B

Tài liệu này dành cho người mới sử dụng máy tính và chưa có kinh nghiệm nghiên cứu. Hãy đọc và làm lần lượt. Khi chưa hiểu một mục, không nên đo tiếp hoặc tự điền số liệu ước đoán.

---

## Bắt đầu nhanh với bản demo online

Mở link HTTPS do người triển khai cung cấp. Link Cloudflare tạm có thể thay đổi khi mở lại demo. Đăng nhập bằng tài khoản và mật khẩu được cung cấp riêng; không lưu mật khẩu vào tài liệu hoặc Git.

1. Chọn **Demo · DEMO-HF** ở **Phiên đang mở**. Bản demo đã có đoạn video khoảng 2 phút tại cả A và B, hai vạch minh họa và xác nhận đồng bộ.
2. Ở **1. Đo video**, bấm **Phát video** dưới Camera A hoặc B. Hai camera điều khiển riêng. Bấm **Tạm dừng** trước khi chọn mốc.
3. Dùng thanh tua để tìm xe, sau đó **−1 frame / +1 frame** để chọn khung hình đầu tiên mà đầu xe chạm/cắt vạch. Frame ngay trước phải chưa chạm.
4. Chọn hướng, loại xe, nhập đặc điểm nhận dạng và bấm **Ghi mốc đầu**. Tìm đúng xe tại camera còn lại, chọn frame theo cùng quy tắc rồi **Ghi mốc cuối**.
5. Mở bản ghi để rà soát: chỉ chọn **Đã xác nhận** và **Giữ** khi đủ căn cứ. Xe bị che khuất cần ghi QC và lý do, không đoán timestamp.
6. Mở **5. Kết quả & xuất → Tính lại**. Muốn đánh giá độ lặp lại, thực hiện **4. Kiểm tra độc lập** theo mục 19 trước khi tải báo cáo.

**Phát video và chọn frame:** nút Phát video dùng trình phát video trực tiếp của trình duyệt, có bộ đệm và tốc độ 0.25× / 0.5× / 1× / 2×. Vạch vẫn hiển thị trên hình. Khi tạm dừng, tua hoặc bước ±1 frame, phần mềm lấy ảnh gốc theo chỉ mục PTS để kiểm tra mốc. Không ghi mốc trong lúc một camera còn phát. Đường truyền vẫn có thể gây chờ tải; con số FPS trên màn hình là FPS nguồn. Thời gian đo lấy từ PTS, không lấy thời gian chờ mạng. Nếu trình duyệt không hỗ trợ codec, dùng MP4 H.264 hoặc bước frame; không tự thay video đã dùng để đo.

Máy đang chạy demo phải bật, có Internet và không sleep. Nếu trang hoặc ảnh không tải, kiểm tra máy chủ và tunnel trước; tải lại trang sẽ đưa vị trí xem về đầu video. Dữ liệu đã lưu nằm trên máy chủ; tránh nhiều người cùng sửa một phiên.

**Giới hạn demo:** A và B dùng cùng một clip, vạch và L = 100 m chỉ minh họa. Bản này giúp học quy trình, không xác nhận tốc độ thực của xe. Giao diện hiện tại chọn frame và ghép xe thủ công; YOLO/tracker thử nghiệm chưa tự động vận hành trong web này.

## 1. Phần mềm dùng để làm gì?

Phần mềm đo **tốc độ hành trình của cùng một phương tiện** giữa hai vị trí:

- **A:** vị trí Camera A và vạch đo A.
- **B:** vị trí Camera B và vạch đo B.
- **L:** khoảng cách thực tế từ vạch A đến vạch B, tính bằng mét.

Người sử dụng chọn thời điểm một xe đi qua vạch thứ nhất, tìm đúng xe đó trong video còn lại, rồi chọn thời điểm xe đi qua vạch thứ hai. Phần mềm dùng khoảng cách `L` và thời gian hành trình để tính tốc độ.

Phần mềm không tự nhận diện xe. Người sử dụng phải đối chiếu loại xe, màu, hình dáng, làn, biển số nếu nhìn được và thứ tự xe xung quanh.

## 2. Những từ cần biết

| Từ trên màn hình | Ý nghĩa |
|---|---|
| Phiên | Một lần làm việc riêng cho một địa điểm và một cặp video. |
| Frame | Một khung hình riêng lẻ của video. |
| Vạch A/B | Đường vàng trên ảnh, đại diện mặt cắt đo ngoài thực địa. |
| Mốc đầu | Frame đầu tiên mà phần đầu xe chạm hoặc cắt vạch đầu tiên theo chiều di chuyển. |
| Mốc cuối | Frame đầu tiên mà phần đầu của chính xe đó chạm hoặc cắt vạch còn lại theo chiều di chuyển. |
| Đồng bộ | Xác định quan hệ thời gian giữa hai camera. |
| Offset | Số giây cộng vào thời gian Camera B để quy về đồng hồ Camera A. |
| QC | Mã ghi lại vấn đề về chất lượng của phép đo. |
| Snapshot | Tệp `snapshot.json` lưu dữ liệu phiên, nhưng không chứa video. |
| Demo | Phiên thực hành, không dùng làm kết quả nghiên cứu. |
| Research | Phiên nghiên cứu thật. |

## 3. Chuẩn bị trước khi bắt đầu

Một phiên nghiên cứu cần có:

1. Video Camera A và video Camera B.
2. Khoảng cách thực tế `L` giữa hai vạch, có nguồn đo rõ ràng.
3. Căn cứ đồng bộ hai video, chẳng hạn một tín hiệu đèn hoặc sự kiện nhìn thấy ở cả hai camera.
4. Mã địa điểm khảo sát và tên người thao tác.
5. Quy tắc chọn xe, thời gian khảo sát và phương án lấy mẫu đã được thống nhất.

Không tự tạo số liệu còn thiếu. Nếu chưa có căn cứ cho `L`, sai số hoặc đồng bộ, hãy hỏi người phụ trách nghiên cứu.

## 4. Mở và đóng phần mềm

Cách mở và địa chỉ trang khác nhau giữa Windows và macOS. Hãy làm theo đúng phần dành cho máy của bạn.

### Trên Windows

**Mở phần mềm**

1. Mở thư mục chứa phần mềm, ví dụ `D:ideo_ab_github`.
2. Tìm tệp **Start.bat**.
3. Bấm đúp vào tệp.
4. Một cửa sổ đen (Command Prompt) sẽ mở và in địa chỉ trang. Không đóng cửa sổ này khi đang dùng.
5. Trên Windows trình duyệt **không tự mở**. Hãy tự mở trình duyệt, nhập `http://127.0.0.1:8765` rồi nhấn **Enter**.

Nếu Windows hoặc phần mềm diệt virus hỏi có cho chạy không, chọn cho phép. Nếu cửa sổ đen báo thiếu `.venv\Scripts\python.exe`, phần mềm chưa được cài trên máy này; hãy liên hệ người phụ trách kỹ thuật thay vì tự cài.

**Đóng phần mềm**

1. Chờ dòng **Đã tự lưu** trên trang.
2. Quay lại cửa sổ đen.
3. Nhấn đồng thời **Ctrl + C**.
4. Đóng cửa sổ đen và trình duyệt.

### Trên macOS

**Mở phần mềm**

1. Ra màn hình Desktop.
2. Tìm **MỞ PHẦN MỀM KHẢO SÁT.command**.
3. Bấm đúp vào biểu tượng.
4. Cửa sổ Terminal màu đen sẽ mở. Không đóng cửa sổ này khi đang dùng.
5. Trình duyệt thường tự mở. Nếu không, nhập `http://127.0.0.1:8766` vào trình duyệt và nhấn **Enter**.

Nếu macOS chặn trong lần đầu, bấm chuột phải vào biểu tượng, chọn **Open/Mở**, rồi chọn **Open/Mở** lần nữa.

**Đóng phần mềm**

1. Chờ dòng **Đã tự lưu**.
2. Quay lại Terminal.
3. Nhấn đồng thời **Control + C**.
4. Đóng Terminal và trình duyệt.

### Kiểm tra đã mở đúng

Phần mềm mở thành công khi thấy tiêu đề **Khảo sát tốc độ A–B** và năm tab từ **1. Đo video** đến **5. Kết quả & xuất**.

Hai hệ điều hành dùng **cổng mặc định khác nhau**: Windows là `8765`, macOS là `8766`. Nhập nhầm cổng thì trình duyệt báo không kết nối được dù phần mềm vẫn đang chạy. Số cổng đúng luôn được in trong cửa sổ đen lúc khởi động; khi nghi ngờ, hãy đọc dòng đó.

## 5. Chọn loại phiên

### Phiên thực hành

1. Bấm **Tạo phiên thực hành**.
2. Bấm **OK**.
3. Kiểm tra dải cảnh báo Demo ở đầu trang.

Có thể nhập cùng một video cho A và B để học thao tác. Tuyệt đối không dùng kết quả Demo trong nghiên cứu.

### Phiên nghiên cứu

1. Chỉ tạo khi có hai video thật, khoảng cách thật và căn cứ đồng bộ.
2. Bấm **Tạo phiên nghiên cứu**.
3. Bấm **OK**.
4. Kiểm tra đầu trang hiển thị **PHIÊN NGHIÊN CỨU**.

Tạo phiên mới không xóa phiên cũ. Hộp **Phiên đang mở** dùng để chọn lại phiên đã lưu. Không dùng cùng một phiên cho địa điểm hoặc cặp video khác.

## 6. Điền thông tin phiên

Mở **2. Thiết lập & đồng bộ** và điền lần lượt:

| Trường | Cách điền |
|---|---|
| Tên dự án | Tên nghiên cứu hoặc dự án. |
| Mã vị trí * | Mã duy nhất, ví dụ `LET-DK-01`. |
| Địa điểm | Tên đường, giao lộ, quận và thành phố. |
| Người thao tác * | Họ tên người đang click video. |
| Thời điểm bắt đầu | Ngày giờ khảo sát nếu đã xác định. |
| Múi giờ | Giữ `Asia/Ho_Chi_Minh` khi khảo sát tại Việt Nam. |
| Camera tham chiếu | Thường là `A`, trừ khi phương án quy định khác. |
| Khoảng cách A–B, mét * | Khoảng cách đo thực tế; 100 mét thì nhập `100`. |
| Sai số khoảng cách, mét | Chỉ nhập khi có căn cứ. |
| Sai số thời gian, giây | Chỉ nhập khi đã đánh giá được. |
| Bắt đầu phân tích, giây | `0` nếu phân tích từ đầu video. |
| Kết thúc phân tích, giây | Ví dụ `900` là 15 phút. |
| Độ dài khoảng tổng hợp, giây | `900` nếu tổng hợp theo từng 15 phút. |

Trường có dấu `*` là bắt buộc. Trường chưa có căn cứ nên để trống.

## 7. Đồng bộ hai camera

### Với hai video nghiên cứu thật

1. Tìm sự kiện nhận biết được ở cả hai video.
2. Xác định độ lệch thời gian giữa Camera B và Camera A.
3. Nhập **Offset tại đầu video (giây)**.
4. Nếu đã kiểm tra cuối video, nhập **Offset tại cuối video (giây)**.
5. Ghi bằng chứng vào **Căn cứ đồng bộ**, ví dụ: `Đối chiếu lúc đèn chuyển xanh tại 16:45:58`.
6. Chỉ đánh dấu **Tôi đã kiểm tra và xác nhận đồng bộ** sau khi thực sự kiểm tra.
7. Bấm **Lưu thiết lập**.
8. Chờ thông báo đã lưu.

Không mặc định offset bằng 0 chỉ vì hai video có vẻ bắt đầu cùng lúc.

### Khi thực hành bằng cùng một video

1. Nhập `0` cho cả hai offset.
2. Ghi: `Demo: Camera A và B dùng cùng một video, offset 0 giây`.
3. Đánh dấu đã kiểm tra.
4. Bấm **Lưu thiết lập**.

Cách này chỉ dùng trong phiên Demo.

Không mở hoặc sửa **Tùy chọn nâng cao dành cho người phụ trách phương pháp** nếu chưa biết JSON. Sai một dấu phẩy hoặc dấu ngoặc có thể gây lỗi.

## 8. Nhập video

1. Mở **1. Đo video**.
2. Tại Camera A, bấm **Choose File/Chọn tệp**.
3. Chọn đúng video A, rồi bấm **Open/Mở**.
4. Chờ phần mềm chuẩn bị xong. Video dài có thể mất vài phút.
5. Kiểm tra Camera A đã hiện hình.
6. Làm tương tự với Camera B.
7. Kiểm tra cả hai khung đều có hình và thông tin thời gian.

Không đóng trang, đổi phiên hoặc tắt Terminal khi đang chuẩn bị video. Nếu đã ghi xe mà phát hiện chọn nhầm video, hãy tạo phiên mới.

## 9. Điều khiển video

- **Phát video/Tạm dừng:** chạy hoặc dừng video.
- **−1 frame/+1 frame:** lùi hoặc tiến đúng một khung hình.
- Hộp `0.25`, `0.5`, `1`, `2`: tốc độ phát video, không phải tốc độ xe.
- Thanh trượt: di chuyển nhanh đến vùng thời gian cần xem.
- **Phóng to/Thu nhỏ:** hỗ trợ nhìn rõ xe và vạch.

Khi chọn mốc chính xác, hãy tạm dừng rồi đi từng frame. Không chọn mốc khi video vẫn đang chạy.

## 10. Vẽ và khóa vạch

Làm riêng cho từng camera:

1. Chọn một frame nhìn rõ mặt đường.
2. Bấm **Vẽ vạch**.
3. Bấm điểm thứ nhất trên ảnh.
4. Bấm điểm thứ hai ở phía đối diện.
5. Kiểm tra đường vàng cắt ngang đúng quỹ đạo xe tại mặt cắt khảo sát.
6. Di chuyển qua vài frame để kiểm tra vị trí.
7. Nếu sai và chưa khóa, bấm **Vẽ vạch** rồi chọn lại hai điểm.
8. Khi chắc chắn đúng, bấm **Khóa vạch**.
9. Lặp lại cho camera còn lại.

Vạch phải đúng với hai đầu của khoảng cách `L` ngoài thực địa. Sau khi khóa, muốn đổi vạch phải tạo phiên mới.

## 11. Kiểm tra trạng thái sẵn sàng

Bảng **Tiến độ phiên** phải cho thấy:

1. Đã nhập người thao tác và `L`.
2. Đã nhập hai video.
3. Đã khóa hai vạch.
4. Đã xác nhận đồng bộ và ghi căn cứ.

Nếu bấm ghi mốc quá sớm, phần mềm sẽ liệt kê mục còn thiếu. Hãy hoàn thành đúng mục được báo.

## 12. Đo một xe hướng A→B

### Ghi mốc đầu tại Camera A

1. Chọn **Hướng xe: A→B**.
2. Chọn đúng loại xe.
3. Nhập đặc điểm rõ ràng, ví dụ: `Xe máy đen, người lái áo trắng, làn giữa, sau ô tô đỏ`.
4. Phát Camera A để tìm xe.
5. Khi xe gần vạch, tạm dừng.
6. Đi từng frame để chọn **khung hình đầu tiên mà phần đầu xe chạm hoặc cắt vạch theo chiều di chuyển**.
7. Bấm **Ghi mốc đầu**.
8. Chờ thông báo đã lưu.

### Ghi mốc cuối tại Camera B

1. Đọc lại đặc điểm nhận dạng.
2. Tìm đúng xe bằng loại, màu, hình dáng, làn và thứ tự xe xung quanh.
3. Khi xe gần vạch B, tạm dừng.
4. Đi từng frame và chọn khung hình đầu tiên mà phần đầu xe chạm hoặc cắt vạch B.
5. Kiểm tra **Xe đang xử lý** đang chọn đúng mã xe.
6. Bấm **Ghi mốc cuối**.

Khoảng thời gian gợi ý chỉ hỗ trợ tìm xe, không phải quy tắc tự động loại xe.

## 13. Đo một xe hướng B→A

1. Chọn **Hướng xe: B→A**.
2. Chọn loại và mô tả xe.
3. Ghi mốc đầu tại Camera B.
4. Tìm đúng xe tại Camera A.
5. Ghi mốc cuối tại Camera A.

Quy tắc chọn frame phải giống mục 12.

### Xác nhận frame qua vạch — thống nhất ngày 09/09/2026

- Frame liền trước phải cho thấy phần đầu xe chưa chạm vạch; frame được chọn là frame đầu tiên chạm hoặc cắt vạch.
- Nếu xe chuyển từ chưa chạm sang đã cắt vạch giữa hai frame, chọn frame đầu tiên đã cắt vạch. Không tự tạo timestamp nội suy thay cho frame quan sát.
- Phần mềm lưu PTS/time base gốc của frame được chọn, sau đó áp dụng hiệu chỉnh đồng bộ khi tính thời gian hành trình.
- Khi bị che khuất hoặc không có frame trước để xác minh, đánh dấu không chắc frame (QC 3), ghi lý do và giữ trạng thái cần rà soát.
- Áp dụng cùng quy tắc ở hai camera và cả hai hướng. Điểm giữa cạnh dưới khung bao trong bản AI thử chỉ là gợi ý, chưa xác định đầu xe.
- Quy tắc này áp dụng cho các phép đo tiếp theo. Không tự dịch timestamp các phiên đã đo theo quy tắc cũ; cần xem lại video trước khi sửa.


## 14. Rà soát bản ghi

Sau mốc cuối, cửa sổ rà soát xuất hiện.

### Trạng thái khớp

- **Đã xác nhận:** chắc chắn là cùng một xe.
- **Cần rà soát:** chưa đủ chắc chắn.
- **Không chắc:** có nghi ngờ đáng kể.
- **Chờ khớp:** chưa hoàn thành xác nhận.

### Quyết định

- **Giữ:** đưa bản ghi đủ điều kiện vào phân tích.
- **Loại:** không dùng trong phân tích nhưng vẫn giữ dấu vết.
- **Cần rà soát:** chưa quyết định.

### Mã QC

| Mã | Ý nghĩa |
|---|---|
| 0 | Không phát hiện vấn đề |
| 1 | Xe bị che khuất |
| 2 | Không chắc cùng xe |
| 3 | Không chắc frame |
| 4 | Xe dừng hoặc bị gián đoạn |
| 5 | Ngoài phạm vi nghiên cứu |
| 6 | Vấn đề khác |

Nếu chọn **Giữ** hoặc **Loại**, phải nhập người rà soát và lý do. Sau đó bấm **Lưu rà soát**.

Không xóa bản ghi xấu để làm kết quả đẹp hơn. Chọn **Loại** và ghi lý do để giữ tính minh bạch.

## 15. Xem lại hoặc sửa một xe

1. Tìm bảng xe ở cuối tab 1.
2. Bấm mã ID của xe.
3. Kiểm tra trạng thái, quyết định, QC, người rà soát và lý do.
4. Sửa thông tin cần thiết.
5. Bấm **Lưu rà soát**.

Cảnh báo tốc độ bất thường hoặc trùng cặp sự kiện yêu cầu xem lại; phần mềm không tự loại xe.

## 16. Hoàn tác và làm lại

- **Hoàn tác:** quay lại thao tác vừa thực hiện.
- **Làm lại:** khôi phục thao tác vừa hoàn tác.

Sau khi đổi phiên hoặc mở lại trang, hãy dùng **Lịch sử và phục hồi** ở tab 5 nếu cần quay về bản cũ.

## 17. Nhập lưu lượng giao thông

Mở **3. Lưu lượng & mẫu**:

1. Chọn hướng xe.
2. Chọn mặt cắt A hoặc B theo phương án nghiên cứu.
3. Nhập số thứ tự khoảng thời gian; khoảng đầu là `0`, khoảng sau là `1`.
4. Chọn loại xe.
5. Nhập số xe đếm được, là số nguyên không âm.
6. Bấm **Lưu số đếm**.
7. Lặp lại cho từng loại và từng hướng.

Số đếm lưu lượng độc lập với số xe được chọn để đo tốc độ.

## 18. Tạo kế hoạch lấy mẫu

Phần này chỉ dùng khi đã có thiết kế lấy mẫu:

- **N đủ điều kiện:** tổng số xe trong quần thể có thể chọn.
- **CV pilot:** hệ số biến thiên từ khảo sát thử; không tự đoán.
- **Sai số tương đối:** mục tiêu chính xác đã được quy định.
- **Seed:** số giúp tái lập việc chọn mẫu.
- **FPC:** hiệu chỉnh quần thể hữu hạn.
- **N đúng quần thể:** xác nhận N là toàn bộ quần thể hữu hạn được lấy mẫu không hoàn lại.
- **Nhóm hiếm:** áp dụng theo phương án cho nhóm phương tiện hiếm.

Chỉ chọn FPC khi người phụ trách phương pháp xác nhận. Nếu chưa có kế hoạch, không tự nhập thông số để tạo kết quả.

## 19. Kiểm tra độc lập

Mở **4. Kiểm tra độc lập**:

1. Nhập tên người đo lại.
2. Chọn `inter-observer` nếu người khác đo lại; chọn `intra-observer` nếu cùng người đo lại vào thời điểm khác.
3. Nhập tỷ lệ theo protocol; `0.1` là 10%.
4. Bấm **Chọn mẫu kiểm tra**.
5. Chọn một xe và bấm **Bắt đầu**.
6. Phần mềm che kết quả cũ.
7. Dựa vào mô tả xe, tự chọn lại frame A và B.
8. Quay lại tab 4, chọn mức khớp.
9. Bấm **Lưu cặp frame A/B**.

Không cho người đo lại xem kết quả gốc trước khi hoàn thành.

## 20. Xem kết quả

1. Mở **5. Kết quả & xuất**.
2. Bấm **Tính lại**.
3. Đọc bảng theo site, hướng và khoảng thời gian.

Một xe chỉ được giữ trong kết quả khi đã có đủ hai mốc, tính được tốc độ, nằm trong khoảng phân tích, được xác nhận khớp và có quyết định **Giữ**.

- **N đếm:** số xe đếm được nếu đã nhập lưu lượng.
- **n chọn/khớp/giữ:** số xe được chọn, ghép và giữ lại.
- **MC%:** tỷ lệ xe máy trong số đếm.
- **Mean:** tốc độ trung bình.
- **95% CI:** khoảng tin cậy khi protocol cho phép.
- **P85:** tốc độ mà 85% quan sát không vượt quá, khi đủ điều kiện tính.

Không kết luận về tai nạn hoặc quan hệ nhân quả chỉ từ một bảng tốc độ.

### Công thức và các độ đo đánh giá

Với timestamp đã quy về đồng hồ A: hướng A→B dùng `Δt = tB_corrected − tA_corrected`; hướng B→A dùng `Δt = tA_corrected − tB_corrected`. Tốc độ hành trình `v = 3.6 × L / Δt` (km/h), chỉ tính khi L và Δt dương. Đây là tốc độ trung bình trên đoạn đường giữa hai vạch, không phải tốc độ tức thời tại camera.

Ví dụ tính toán minh họa: L = 100 m và Δt = 10 s cho v = 36 km/h. Khoảng cách cần đo giữa hai vạch theo tuyến xe chạy, không chỉ lấy khoảng cách giữa thân hai camera.

Trong ZIP báo cáo, xem bảng/sheet **Audit** để đối chiếu từng xe và **Reliability** để xem các chỉ số tổng hợp. Các chỉ số này hiện nằm trong báo cáo xuất, không phải tất cả đều có biểu đồ trên web.

| Chỉ số | Ý nghĩa và đơn vị |
|---|---|
| `n` | Số cặp đo gốc–đo lại tính được tốc độ; không phải tổng số xe trong video. |
| `bias` | Trung bình (tốc độ đo lại − tốc độ gốc), km/h; dấu cho biết xu hướng lệch. |
| `MAE` | Trung bình trị tuyệt đối chênh lệch tốc độ, km/h. |
| `RMSE` | Căn trung bình bình phương chênh lệch tốc độ, km/h; nhạy hơn với chênh lệch lớn. |
| `limits` | Giới hạn đồng thuận: bias ± 1.96 × SD của chênh lệch, km/h; cần ít nhất hai cặp. Không phải khoảng tin cậy của tốc độ trung bình. |
| `frame_difference_A/B` | Frame đo lại trừ frame gốc, theo từng camera, trong bảng Audit. |
| `time_difference_A/B` | Timestamp thô đo lại trừ timestamp gốc, giây, trong bảng Audit. |
| `correct / incorrect / uncertain` | Số lần kiểm tra ghép xe được đánh dấu đúng / sai / không chắc. `matching_denominator` là tổng lượt audit hoàn thành. |

Nếu cần tỷ lệ khớp đúng, tính `100 × correct / matching_denominator` và báo cáo cả số sai, không chắc; không tự bỏ nhóm không chắc khỏi mẫu số. Đây là kết luận của người kiểm tra, chưa phải độ chính xác so với chuẩn độc lập. Khi chưa đo lại, các chỉ số trống là bình thường, không có nghĩa sai số bằng 0.

Các thống kê Mean, SD, CV, Median, V85 mô tả phân bố tốc độ; chúng không đo độ chính xác nhận dạng xe. MAE/RMSE ở đây đo sự đồng thuận giữa các lần thao tác, không chứng minh tốc độ đúng ngoài hiện trường. Hai lần cùng sai L hoặc đồng bộ vẫn có thể đồng thuận tốt. Mã hiện tại tổng hợp các cặp audit tính được tốc độ; hãy xem riêng cặp khớp sai/không chắc và phân biệt kiểm tra cùng người với khác người khi diễn giải.

Để đánh giá đề tài, chuẩn bị tập kiểm tra có xe máy bị che khuất và các cặp ô tô/xe tải dễ nhầm, ghi nhãn độc lập và giữ tập này riêng với dữ liệu tinh chỉnh. Nếu đánh giá AI, cần bổ sung bảng nhầm lẫn và precision/recall theo loại xe, tỷ lệ bỏ sót, lỗi ghép A–B và sai lệch thời điểm chạm vạch so với nhãn chuẩn. Web hiện chưa tự tính các chỉ số AI này. Chốt ngưỡng chấp nhận trước khi đánh giá; không suy ra một tỷ lệ chính xác khi chưa có tập chuẩn.

## 21. Xuất báo cáo

1. Chọn đúng phiên.
2. Mở tab 5 và bấm **Tính lại**.
3. Bấm **Tải báo cáo đầy đủ**.
4. Chờ tải tệp `.zip`.
5. Mở thư mục **Downloads/Tải về**.
6. Bấm đúp tệp ZIP để giải nén.

Gói xuất có Excel, CSV, Word, PDF và `snapshot.json`. Giữ nguyên tệp ZIP làm bản lưu gốc.

## 22. Snapshot và phục hồi

### Phục hồi snapshot

1. Mở tab 5.
2. Tại **Phục hồi snapshot JSON**, bấm **Choose File/Chọn tệp**.
3. Chọn đúng `snapshot.json`.
4. Chờ phần mềm tải xong.
5. Kiểm tra **Phiên đang mở**. Phần mềm tạo một phiên mới và không ghi đè phiên cũ.
6. Kiểm tra lại thiết lập, video, vạch, danh sách xe và kết quả.

Snapshot không chứa video. Khi chuyển máy, cần sao lưu thêm database, thư mục media và video gốc.

### Phục hồi từ lịch sử

1. Trong tab 5, tìm **Lịch sử và phục hồi**.
2. Chọn thời điểm trước khi làm sai.
3. Bấm **Phục hồi phiên bản đã chọn**.
4. Kiểm tra dữ liệu sau phục hồi.

## 23. Sao lưu sau mỗi buổi

1. Chờ **Đã tự lưu**.
2. Tải báo cáo đầy đủ của từng phiên quan trọng.
3. Bấm **Sao lưu database**.
4. Giữ nguyên video gốc A và B.
5. Tạo thư mục có tên rõ, ví dụ `LET-DK-01_2026-09-07`.
6. Lưu video, ZIP báo cáo, snapshot và database vào đó.
7. Sao chép thêm một bản tới nơi lưu trữ được nhóm nghiên cứu cho phép.

Không đưa video nghiên cứu lên GitHub. GitHub lưu mã nguồn phần mềm, không phải nơi mặc định lưu video và database khảo sát.

## 24. Xử lý lỗi thường gặp

### Trang không mở

Kiểm tra cửa sổ đen (Command Prompt trên Windows, Terminal trên macOS) còn mở, khởi động lại phần mềm và dùng **đúng cổng của máy mình**: `http://127.0.0.1:8765` trên Windows, `http://127.0.0.1:8766` trên macOS. Số cổng đúng được in trong cửa sổ đen lúc khởi động.

### Video hoặc nút không hoạt động

Tải lại trang: **F5** hoặc **Ctrl + R** trên Windows, **Command + R** trên macOS. Sau đó chọn lại đúng phiên và kiểm tra cửa sổ đen. Nếu vẫn lỗi, chụp màn hình thông báo đỏ và ghi lại nút vừa bấm.

### Không thấy vạch

Nhập video, bấm **Vẽ vạch**, chọn đủ hai điểm và bấm **Khóa vạch** khi đúng.

### Báo chưa thể ghi mốc

Đọc danh sách còn thiếu: hai video, người thao tác, `L`, căn cứ đồng bộ hoặc hai vạch.

### JSON Parse error

Phần JSON nâng cao đã bị sửa sai. Không tiếp tục tự sửa nếu không quen JSON. Tải lại trang để lấy bản đã lưu gần nhất hoặc nhờ người phụ trách kỹ thuật.

### Báo phiên đã thay đổi

Phiên có thể đang mở ở hai tab. Tải lại trang (**F5**/**Ctrl + R** trên Windows, **Command + R** trên macOS) và chỉ dùng một tab để nhập dữ liệu.

### Chọn nhầm video hoặc khóa nhầm vạch

Tạo phiên mới. Không cố thay video sau khi đã ghi xe.

## 25. Mười quy tắc bảo đảm chất lượng

1. Dùng cùng một quy tắc chọn frame cho mọi xe.
2. Mô tả xe đủ chi tiết để ghép đúng.
3. Không tự điền số liệu chưa đo.
4. Không tự loại xe chỉ vì tốc độ khác thường.
5. Không xóa bản ghi bị loại.
6. Không dùng dữ liệu Demo trong nghiên cứu.
7. Không dùng cùng một video cho A và B trong nghiên cứu thật.
8. Không xác nhận đồng bộ khi chưa có bằng chứng.
9. Ghi nhật ký khi điều kiện site hoặc quy tắc thay đổi.
10. Sao lưu sau mỗi buổi làm việc.

## 26. Bài thực hành cho người mới

1. Tạo một phiên Demo.
2. Nhập tên người thao tác và `L = 100` chỉ cho bài tập.
3. Nhập cùng một video cho A và B.
4. Đặt offset 0 và ghi rõ căn cứ Demo.
5. Vẽ và khóa hai vạch.
6. Đo ít nhất ba xe.
7. Rà soát một xe giữ, một xe cần xem lại và một xe loại.
8. Mở kết quả và bấm **Tính lại**.
9. Tải báo cáo đầy đủ.
10. Thử phục hồi `snapshot.json` thành phiên mới.

Chỉ chuyển sang Research khi đã hoàn thành bài thực hành và hiểu mục đích của từng bước.

## 27. Danh sách kiểm tra trước khi kết thúc

- [ ] Đúng phiên và đúng mã site.
- [ ] Hai video đúng địa điểm và thời gian.
- [ ] Khoảng cách `L` có căn cứ đo.
- [ ] Đồng bộ đã được kiểm tra và ghi căn cứ.
- [ ] Hai vạch đúng vị trí và đã khóa.
- [ ] Mỗi xe có mô tả nhận dạng rõ.
- [ ] Các bản ghi giữ/loại có người rà soát và lý do.
- [ ] Kết quả đã được tính lại.
- [ ] Báo cáo, snapshot và database đã được sao lưu.
