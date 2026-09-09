---
title: Khảo sát tốc độ A–B
emoji: 🚦
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
short_description: Đo tốc độ hành trình xe giữa hai mặt cắt A–B
---

# Khảo sát tốc độ A–B

Bản trình diễn trực tuyến của công cụ đo tốc độ hành trình từng phương tiện giữa hai mặt cắt A–B.

Mã nguồn: <https://github.com/Helianthusss/video-ab-speed>

## Cần đặt trước khi chạy

Trong **Settings** của Space, thêm ba biến:

| Tên | Loại | Giá trị |
|---|---|---|
| `AB_ALLOWED_HOST` | Variable | tên miền của Space, ví dụ `anhtd20-video-ab-speed.hf.space` |
| `AB_USERNAME` | Secret | tên đăng nhập |
| `AB_PASSWORD` | Secret | mật khẩu |

Thiếu `AB_ALLOWED_HOST` thì mọi truy cập trả về 400. Thiếu tài khoản hoặc mật khẩu thì trả về 503. Cả hai đều là chốt an toàn có sẵn, không phải lỗi.

## Dữ liệu trong bản demo

Space này chứa sẵn một đoạn video 2 phút và một phiên **Demo** đã nhập video, đã khóa hai vạch, đã xác nhận đồng bộ.

Phiên này **không chứa phép đo nào**. Vạch A và B chỉ là vị trí minh họa, không phải mặt cắt đã khảo sát, và khoảng cách `L` không phải số đo thực địa. Mục đích là để người xem tự bấm đo trực tiếp.

Không dùng bất kỳ số liệu nào sinh ra ở đây làm kết quả nghiên cứu.

## Giới hạn của bản trực tuyến

Space dùng ổ đĩa tạm. Mỗi lần khởi động lại, mọi thao tác trong phiên trước sẽ mất và Space trở về đúng trạng thái ban đầu. Space ngủ sau 48 giờ không có ai truy cập và cần khoảng một phút để thức dậy.

Không nhập video mới qua bản trực tuyến. Việc khảo sát thật phải chạy cục bộ theo hướng dẫn trong repository.
