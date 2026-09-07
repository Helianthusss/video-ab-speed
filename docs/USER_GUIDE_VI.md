# Hướng dẫn sử dụng công cụ khảo sát tốc độ A–B

## 1. Mở phần mềm

Trên macOS, mở thư mục dự án và bấm đúp `Start.command`. Giữ cửa sổ Terminal mở trong lúc sử dụng, sau đó mở `http://127.0.0.1:8765` trong trình duyệt. Nếu chạy bản kiểm tra ở cổng 8766, dùng `http://127.0.0.1:8766`.

## 2. Chọn đúng loại phiên

- **Phiên thực hành**: dùng video thử hoặc cùng một video cho hai camera. Không dùng kết quả cho nghiên cứu.
- **Phiên nghiên cứu**: chỉ dùng khi có hai video, khoảng cách và căn cứ đồng bộ hợp lệ.

Mỗi phiên được tự động lưu. Tạo phiên mới không xóa phiên cũ; có thể chọn lại phiên ở hộp **Phiên đang mở**.

## 3. Thiết lập phiên

Mở **2. Thiết lập & đồng bộ**, sau đó nhập:

1. Mã vị trí khảo sát.
2. Địa điểm.
3. Tên người thao tác.
4. Thời điểm bắt đầu nếu đã xác định.
5. Khoảng cách thực tế `L` giữa hai mặt cắt, đơn vị mét.
6. Khoảng bắt đầu, kết thúc và độ dài khoảng tổng hợp, đơn vị giây.

`uL` và `uT` là độ không đảm bảo của khoảng cách và thời gian. Để trống khi chưa có căn cứ.

## 4. Đồng bộ hai camera

Trong cùng màn hình:

1. Nhập offset đầu và cuối cần cộng vào timestamp Camera B.
2. Ghi căn cứ quan sát, ví dụ cùng thời điểm tín hiệu đèn đổi trạng thái.
3. Chỉ chọn **Tôi đã kiểm tra và xác nhận đồng bộ** sau khi kiểm tra thực tế.
4. Bấm **Lưu thiết lập**.

Nếu hai video dùng cùng đồng hồ đã được kiểm tra, hai offset có thể bằng 0. Không mặc định offset bằng 0 khi chưa có bằng chứng.

## 5. Nhập video

Mở **1. Đo video**. Chọn video Camera A rồi Camera B và chờ phần mềm lập chỉ mục. Video dài có thể cần vài phút. Không đóng trang trong lúc thông báo đang chuẩn bị video.

Không thể đổi video sau khi đã ghi xe hoặc khóa protocol; hãy tạo phiên mới nếu chọn nhầm video.

## 6. Vẽ và khóa vạch

Thực hiện riêng cho từng camera:

1. Bấm **Vẽ vạch**.
2. Bấm điểm thứ nhất trên ảnh.
3. Bấm điểm thứ hai để tạo đường cắt ngang quỹ đạo xe.
4. Kiểm tra đường vàng trên nhiều frame.
5. Bấm **Khóa vạch** khi vị trí đã đúng.

Sau khi khóa, vạch không thể di chuyển trong phiên đó. Tạo phiên mới nếu cần thay đổi.

## 7. Ghi mốc đầu

1. Chọn hướng `A→B` hoặc `B→A`.
2. Chọn đúng loại xe.
3. Ghi đặc điểm nhận dạng cụ thể: màu, kiểu xe, trang phục, làn và thứ tự.
4. Phát video ở camera đầu vào rồi dừng gần vạch.
5. Dùng `−1 frame` và `+1 frame` để chọn khung hình đầu tiên ngay trước khi phần đầu xe chạm hoặc cắt vạch.
6. Bấm **Ghi mốc đầu**.

Phần mềm chỉ cho ghi khi đã có hai video, người thao tác, `L`, đồng bộ có căn cứ và hai vạch đã khóa.

## 8. Ghi mốc cuối

Phần mềm chuyển sang camera còn lại và hiển thị khoảng thời gian hỗ trợ tìm xe. Khoảng này không phải quy tắc tự động loại xe.

1. Tìm đúng xe bằng các đặc điểm đã ghi.
2. Chọn khung hình đầu tiên ngay trước khi đầu xe chạm vạch cuối.
3. Kiểm tra hộp **Xe đang xử lý** đang chọn đúng ID.
4. Bấm **Ghi mốc cuối**.

## 9. Rà soát bản ghi

Sau mốc cuối, cửa sổ rà soát mở ra:

- Chọn trạng thái khớp.
- Chọn quyết định giữ, loại hoặc cần rà soát.
- Chọn mã QC.
- Nhập người rà soát và lý do khi quyết định giữ hoặc loại.
- Bấm **Lưu rà soát**.

Không xóa dữ liệu bị loại; phần mềm giữ lại để phục vụ kiểm tra.

## 10. Lưu lượng, lấy mẫu và kiểm tra độc lập

Mở **3. Lưu lượng & mẫu** để nhập số đếm độc lập với mẫu đo tốc độ. Chỉ dùng FPC khi `N` đúng là quần thể hữu hạn được lấy mẫu không hoàn lại.

Mở **4. Kiểm tra độc lập** để chọn mẫu đo lại theo seed. Trong lúc đo độc lập, kết quả gốc được che trên giao diện.

## 11. Xem và xuất kết quả

Mở **5. Kết quả & xuất**:

- **Tính lại** cập nhật bảng kết quả.
- **Tải báo cáo đầy đủ** tạo Excel, CSV, Word, PDF và JSON.
- **Sao lưu database** tải bản sao SQLite.
- **Phục hồi snapshot JSON** tạo một phiên mới từ snapshot; không ghi đè phiên hiện tại.

## 12. Xử lý lỗi thường gặp

- Video không chạy sau khi đổi phiên: tải lại trang bằng `Command + R`.
- Báo chưa thể ghi mốc: làm theo đúng danh sách thiếu được hiển thị.
- Không thấy vạch: bấm **Vẽ vạch** rồi chọn đủ hai điểm trên ảnh.
- Chọn nhầm video hoặc khóa nhầm vạch: tạo phiên mới.
- Trang không mở: kiểm tra Terminal còn chạy và dùng đúng cổng.

Trước mỗi đợt khảo sát thật, tạo một phiên thử, đo vài xe có đáp án kiểm tra và xuất toàn bộ báo cáo để xác nhận quy trình.
