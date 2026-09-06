# Đối chiếu phương pháp V4 với công cụ

Tài liệu nguồn được dùng làm yêu cầu phương pháp. Các chỉ dẫn không liên quan đến việc xây dựng công cụ không được coi là lệnh thực thi. Tài liệu gốc không bị sửa.

| Mục V4 | Yêu cầu phương pháp | Chức năng | Trường dữ liệu và phép tính | Đầu ra | Kiểm thử | Phân loại |
|---|---|---|---|---|---|---|
| 1 | Hai mặt cắt A B, khoảng cách thực đo xấp xỉ 100 m | Hai vùng video và vạch ảo độc lập | `videoA`, `videoB`, `lines`, `L`, `uL` | Setup, Video sync | khóa vạch; L dương | V4 + bổ sung lưu sai số |
| 2 | Cùng xe; tốc độ hành trình đoạn | Mốc đầu/mốc cuối theo hướng | `tA`, `tB`, `dt`; `V=3.6L/dt` | Raw, Site summary | 100/10=36; 98.5/10=35.46 | V4 |
| 3 | Khóa camera, dùng cùng chuẩn thời gian, lượng hóa sai số | Lập chỉ mục frame/PTS, đồng bộ offset/drift có phiên bản | PTS, time base, FPS, CFR/VFR; `B_corrected=B_raw+offset(B_raw)` | Video sync, Sensitivity | FPS khác nhau; VFR; offset/drift | V4 + chi tiết triển khai |
| 4 | Frame đầu phần đầu xe chạm/cắt vạch; khớp đa đặc điểm; không suy đoán | Quy tắc hiển thị, mô tả xe, trạng thái pending/review/confirmed | frame A/B, type, direction, description, matching, QC | Raw, QC exclusion | thiếu khớp, che khuất, rẽ, dừng | V4 |
| 5.1 | Đếm toàn bộ tách khỏi mẫu tốc độ | Form flow theo mặt cắt, hướng, interval, class | `count`; 15 phút `q=4N`; khác 15 phút `N*3600/T` | Flow count, Site summary | N đếm khác n chọn/khớp/giữ | V4 + thời lượng khác 15 phút |
| 5.2–5.5 | Xác định estimand; n0, FPC; lấy mẫu hệ thống phân tầng | Protocol estimand; planning và danh sách thứ tự chọn | `n0=(1.96CV/e)^2`; FPC có guard; k, start, seed | Sampling | seed tái lập; FPC guard; nhóm hiếm k=1 | V4 |
| 6 | Giữ đúng 10 cột bảng gốc | 10 cột đầu đúng thứ tự, sau đó trường truy vết | Site, ID, Type, Dir., tA, tB, L, Δt, V, QC | Raw CSV/XLSX | kiểm tra thứ tự cột | V4 + truy vết bổ sung |
| 7 | Mean, SD n-1, CV, P50, P85, CI mean, chênh lệch class | Tổng hợp tự động; quy tắc n=0/n=1 | Student-t; percentile bootstrap; Diff có dấu và Diff_abs | Site/Class summary | đối chiếu bộ số tính độc lập | V4 + giải quyết mâu thuẫn Diff |
| 8 | Bảng site đúng thứ tự | 16 cột V4 đầu tiên đúng thứ tự | Site…Diff.; thêm interval, trace, Diff_abs | Site summary | kiểm tra schema và giá trị | V4 + truy vết bổ sung |
| 9 | Luồng nhanh click, auto-jump, auto-save, logic check | Frame-step, phím tắt, cửa sổ pilot, SQLite, cảnh báo | pilot speed; warning speed; revision | Giao diện + history | thao tác thực tế và API | V4 + bổ sung concurrency guard |
| 10 | Validity, reliability, matching quality | Chọn audit có seed; che kết quả; đo lặp; matching review | bias, MAE, RMSE, Bland–Altman limits | Audit, Reliability | cặp dữ liệu biết trước | V4 |
| 11 | Liên hệ Kraidi và định nghĩa speed variation | Protocol snapshot ghi estimand và CV phân bố | estimand, CV | Protocol, báo cáo | kiểm tra field | V4 |
| 12 | Current speed tại historical crash site; site-change log | Nhật ký thay đổi giữ bằng chứng | feature, before, after, evidence | Site changes | form xuất được khi trống/có dữ liệu | V4 |
| 13 | SOP và khóa protocol | Điều kiện khóa bắt buộc; lịch sử phiên bản | protocol version/locked | Protocol, snapshot | chặn khóa khi thiếu site/L/sync/vạch | V4 + chi tiết triển khai |

## Chi tiết kỹ thuật bổ sung để triển khai

- Frame và PTS được giải mã bằng PyAV. Mỗi video được định danh bằng SHA-256 và sao chép vào kho cục bộ.
- SQLite lưu snapshot phiên và mọi phiên bản thao tác. `revision` ngăn hai tab ghi đè im lặng.
- Interval được gán theo mốc đầu vào. Frame index và interval bắt đầu từ 0 và được ghi trong data dictionary.
- Vạch ảo được lưu theo tọa độ tỷ lệ để giữ vị trí khi zoom.
- Bootstrap dùng thuật toán percentile, phân vị nội suy tuyến tính type 7, số lần và seed trong protocol.
- Truyền sai số gần đúng dùng `sqrt((uL/L)^2+(uT/dt)^2)`. Sensitivity dùng PTS thật của ±1 frame ở từng camera và các offset quan sát nhập trong sync.
- Excel có công thức Δt và V trên sheet Raw, đồng thời giữ các giá trị nguồn/hiệu chỉnh để kiểm toán.

## Nội dung chưa rõ hoặc cần quyết định trong protocol

- V4 gọi Diff. là “chênh lệch tuyệt đối”, nhưng phương trình (15) là `Mean_MC-Mean_Car`. Công cụ giữ `Diff.` có dấu và `Diff_abs` là độ lớn.
- V4 không quy định ngưỡng tốc độ đáng ngờ. `warning_speed` là cấu hình triển khai, chỉ cảnh báo và không tự loại.
- V4 không đặt ngưỡng đủ mẫu để tính P85. Công cụ không dùng công thức cỡ mẫu Mean để tuyên bố đủ mẫu P85; n=1 không xuất P85.
- V4 không xác định block bootstrap. Công cụ ghi rõ chưa triển khai và chỉ bật CI thường khi `iid_ci=true` theo protocol.
- Quy tắc giữ/loại cho từng QC phụ thuộc estimand. Công cụ tách cờ QC khỏi quyết định, yêu cầu lý do và người duyệt.
- Việc gộp toàn dòng sau lấy mẫu không tỷ lệ cần trọng số và xử lý không khớp được xác nhận. Công cụ để trống thống kê toàn dòng trong trạng thái đó.
- Khoảng tốc độ pilot, số bootstrap, audit fraction và seed là cấu hình kỹ thuật có thể thay đổi trước khi khóa protocol; không được coi là quy định khoa học của V4.
