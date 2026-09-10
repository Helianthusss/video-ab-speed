# Demo YOLO trên laptop

Mở mục **YOLO nhận diện phương tiện** trong tab Đo video. Chọn camera đã nhập video, thời gian bắt đầu tính theo video gốc, độ dài (mặc định 5 giây, tối đa 30 giây), ngưỡng tin cậy và bấm Chạy YOLO. Mỗi máy chủ xử lý một tác vụ tại một thời điểm. Chờ tiến độ hoàn tất rồi bấm Xem đoạn đã nhận diện, sau đó Phát video ở camera đó. Khung nhận diện hiển thị trên đúng frame đã xử lý, cả lúc phát và bước frame. Có thể tắt khung bằng ô Hiện khung YOLO. Tải JSON để xem nhãn, bbox chuẩn hóa, confidence, chỉ số frame và PTS gốc.

Chỉ những frame trong đoạn xử lý mới có kết quả. Chạy A và B lần lượt để có nhận diện cả hai camera. Kết quả gần nhất của trình duyệt được tải lại khi mở trang; chỉ hiển thị khi đúng phiên và video. Khung hiển thị không tự tạo bản ghi đo, không tự ghép ID A–B hay xác nhận vận tốc. Lượt phát hiện trên nhiều frame không phải số xe duy nhất. YOLO có thể bỏ sót xe che khuất hoặc nhầm loại; cần rà soát bằng video gốc.

Máy chạy Python phải bật, có Internet, không sleep. YOLO tự dùng CUDA nếu có, nếu không dùng CPU. Đây là suy luận weights, không huấn luyện; xử lý nền, chưa cam kết thời gian thực. Benchmark thử clip 2 giây/50 frame trên RTX 3050 Laptop: khoảng 15.8 giây (bao gồm lần suy luận khởi động trong tác vụ), 187 lượt phát hiện, không phải đánh giá độ chính xác.

## Cấu hình

- Cài `requirements-yolo.txt` trong venv hiện có; cần PyTorch tương thích thiết bị. Laptop hiện đã có torch 2.7.1+cu118 và ultralytics 8.4.143.
- Weights tin cậy: `models/yolo26n.pt`; có thể đặt đường dẫn bằng `AB_YOLO_WEIGHTS`. Không upload weights qua web. Model cần các nhãn car, motorcycle, truck, bus hoặc bicycle bằng tiếng Anh.
- `AB_YOLO_DEVICE=auto` mặc định; đặt `cpu` hoặc `0` để chọn thiết bị cụ thể.
- Tác vụ và JSON nằm trong `AB_OUTPUT_DIR/yolo`; lỗi chi tiết trong `worker.log`. Tiến trình con được giải phóng sau mỗi tác vụ; giới hạn thời gian 30 phút. Nếu máy bị tắt giữa tác vụ, chạy lại tác vụ sau khi khởi động web.
- Chạy server đúng **một worker**; khóa đồng thời hiện nằm trong một tiến trình. Không dùng nhiều worker/replica với cơ chế này.
- Không cần sửa hoặc thay tài liệu Word để dùng chức năng này.
