# Demo YOLO trên laptop

Mở mục **YOLO nhận diện phương tiện** trong tab **Đo video**. Sau khi đã nhập đủ video Camera A, Camera B và khóa hai vạch, chọn **Chế độ AI** rồi bấm **AI nhận diện xe A và B**. Phần mềm tự chạy toàn bộ Camera A trước, sau đó Camera B. Mỗi máy chủ xử lý một tác vụ tại một thời điểm để tránh treo máy demo.

Các chế độ AI dùng bước nhảy hình để đổi giữa tốc độ và độ kỹ:

- **Rất nhanh**: đọc rất thưa hình, phù hợp thử giao diện.
- **Nhanh - demo**: mặc định, giảm thời gian chờ đáng kể so với xử lý từng hình.
- **Cân bằng**: theo dõi sát hơn, chờ lâu hơn.
- **Kỹ hơn**: xử lý từng hình, chậm nhất nhưng ít bỏ sót thời điểm hơn.

Sau khi AI chạy xong, bấm **Xem đoạn đã nhận diện**, rồi bấm **Phát video**. Nhật ký AI chỉ ghi khi xe cắt qua vạch. Nếu phần mềm ghép được một xe ở A với một xe ở B theo thứ tự và loại xe hợp lý, nhật ký sẽ hiện **Đề xuất tốc độ**. Đây là kết quả hỗ trợ rà soát, chưa phải kết quả đo chính thức; người dùng vẫn phải kiểm tra đúng cùng xe và có thể ghi mốc thủ công.

Khung AI trên video ưu tiên hiện xe đã qua vạch để tránh rối màn hình. Tùy chọn **Chỉ quét gần vạch** giúp YOLO tập trung vào vùng cần đo và chạy nhanh hơn; nếu video có xe bị che khuất hoặc vạch đặt sát mép hình, có thể tắt tùy chọn này để quét toàn khung. Có thể tắt bằng ô **Hiện xe đã qua vạch**. JSON kết quả lưu nhãn, bbox chuẩn hóa, độ chắc, chỉ số hình và thời gian video.

Máy chạy Python phải bật, có Internet, không sleep. YOLO tự dùng CUDA nếu có, nếu không dùng CPU. Đây là suy luận weights, không huấn luyện; xử lý nền, chưa cam kết thời gian thực. Video dài hoặc chế độ **Kỹ hơn** sẽ chờ lâu hơn.

## Cấu hình

- Cài `requirements-yolo.txt` trong venv hiện có; cần PyTorch tương thích thiết bị.
- Weights mặc định: `models/yolo26n.pt`; có thể đặt đường dẫn bằng `AB_YOLO_WEIGHTS`.
- `AB_YOLO_DEVICE=auto` mặc định; đặt `cpu` hoặc `0` để chọn thiết bị cụ thể.
- Tác vụ và JSON nằm trong `AB_OUTPUT_DIR/yolo`; lỗi chi tiết trong `worker.log`.
- Chạy server đúng **một worker**; khóa đồng thời hiện nằm trong một tiến trình. Không dùng nhiều worker/replica với cơ chế này.
