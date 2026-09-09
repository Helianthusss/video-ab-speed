# Báo cáo kiểm thử nghiệm thu

Lần chạy gần nhất: 09-09-2026 trên Windows 11, Python 3.12.14, bằng `python -m unittest discover -s tests -v`. Lần chạy đầu: 06-09-2026 với 24 phép thử. Bộ dữ liệu tổng hợp tách khỏi phiên video công khai và mang nhãn demo; test tự tạo và tự dọn dữ liệu trong thư mục tạm.

## Kết quả tự động

31/31 phép thử đạt, thời gian chạy 10,9 giây.

| Nhóm | Trường hợp | Kết quả |
|---|---|---|
| Công thức | L=100 m, Δt=10 s → 36 km/h | Đạt |
| Công thức | L=98.5 m, Δt=10 s → 35.46 km/h | Đạt |
| Đồng bộ | offset dấu cộng và drift tuyến tính | Đạt |
| Video | A=10 fps, B=20 fps | Đạt |
| Video | VFR có PTS xen kẽ 80/120 ms; lấy đúng frame | Đạt |
| Hướng | A→B và B→A; không dùng trị tuyệt đối | Đạt |
| Interval | xe vào trước cuối interval, ra trong buffer | Đạt |
| Thiếu dữ liệu | thiếu timestamp hoặc sync không tạo tốc độ | Đạt |
| Lưu lượng | N đếm=13, n hợp lệ=6; quy đổi đúng T=20 s | Đạt |
| Lưu lượng | phiên đúng 15 phút dùng q=4N | Đạt |
| Thống kê | mean, SD n-1, median, P85 type 7, Student-t CI | Đạt |
| Biên | n=0/n=1 trả thiếu, không thay bằng 0 | Đạt |
| Seed | sampling và bootstrap tái lập | Đạt |
| Sampling | FPC bị chặn nếu chưa xác nhận quần thể; nhóm hiếm đo toàn bộ | Đạt |
| Gộp | sampling phân tầng không xuất Mean toàn dòng không trọng số | Đạt |
| QC | xe dừng chỉ có cờ, không tự loại | Đạt |
| Loại | bản ghi bị loại vẫn còn trong Raw | Đạt |
| Reliability | bias, MAE, RMSE và Bland–Altman từ cặp biết trước | Đạt |
| Lưu dữ liệu | click A/B, duyệt, đóng/mở từ SQLite | Đạt |
| Cập nhật | sửa sync tính lại tốc độ/tổng hợp | Đạt |
| Phục hồi | lịch sử phục hồi snapshot cũ không mất bản ghi | Đạt |
| Điều kiện đo | báo đủ mục còn thiếu: người thao tác, L, đồng bộ, hai vạch | Đạt |
| Vạch đo | từ chối lưu vạch không đủ hai điểm hợp lệ, trả lỗi 400 | Đạt |
| Đóng gói | `/`, `/static/app.js`, `/static/style.css` phục vụ từ trong package | Đạt |
| Đường dẫn | data, output và demo nằm trong thư mục tạm khi đặt biến môi trường | Đạt |
| SQLite | kết nối đã đóng sau giao dịch; dùng lại báo `ProgrammingError` | Đạt |
| Sao lưu | `/api/backup` trả tệp SQLite hợp lệ | Đạt |
| Xuất | gói ZIP đọc được và chứa Survey.xlsx sau khi đổi vị trí kho media | Đạt |

Bảy phép thử cuối được bổ sung sau khi tổ chức lại mã nguồn thành package `video_ab/` ngày 08-09-2026.

## Kiểm tra giao diện và xuất

- Giao diện đã mở thành công bằng trình duyệt cục bộ; hai camera hiển thị đúng 10 và 20 fps, frame/PTS, timestamp gốc và hiệu chỉnh.
- Bảng xe hiển thị sáu bản ghi biết trước và cảnh báo tốc độ 180 km/h mà không tự loại.
- Frame-step giải mã hai frame kề nhau khác nhau; auto-jump được tính theo L và khoảng tốc độ pilot trong mã thao tác và dùng timestamp hiệu chỉnh để đổi ngược sang thời gian video còn lại.
- Excel xuất 16 sheet, gồm 12 công thức Δt/V trên Raw; quét lỗi không thấy `#REF!`, `#DIV/0!`, `#VALUE!` hoặc `#NUM!`.
- 16/16 sheet được render xem trước. Header rõ, dữ liệu có wrap và hàng đầu được freeze.
- Word và PDF đều render thành một trang; không có chồng lấn, cắt chữ hoặc lỗi dấu tiếng Việt sau lần chỉnh cuối.
- Gói ZIP gồm Excel, CSV từng biểu mẫu, Word, PDF, snapshot JSON và data dictionary.

## Phạm vi chưa đạt và giới hạn

- Chưa có hai video hiện trường cùng quan sát một dòng xe, khoảng cách thực đo, mốc đồng bộ thực địa hoặc dữ liệu chuẩn tương thích. Vì vậy: `[CHƯA ĐỦ CƠ SỞ DỮ LIỆU ĐỂ KẾT LUẬN]` về độ chính xác ngoài hiện trường.
- Chưa kiểm thử tải lớn với video nhiều giờ. Ứng dụng lập chỉ mục toàn bộ PTS khi nhập nên thời gian và dung lượng chỉ mục tăng theo số frame.
- Chưa có block bootstrap cho phụ thuộc thời gian. CI thường phải tắt nếu protocol chưa xác nhận giả định.
- Chế độ che audit ngăn người thao tác nhìn kết quả cũ trong luồng giao diện, nhưng không phải cơ chế phân quyền bảo mật.
- Không có ANPR/AI; việc khớp cùng xe do người thao tác xác nhận theo protocol.
