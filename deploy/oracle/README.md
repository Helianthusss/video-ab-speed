# Chạy trực tuyến trên máy ảo Oracle Cloud Always Free

Hướng dẫn dựng bản demo chạy 24/7, miễn phí, có HTTPS và địa chỉ cố định.

Oracle yêu cầu thẻ để xác minh danh tính nhưng không trừ tiền với tài nguyên Always Free.

## 1. Tạo máy ảo

Đăng ký tại <https://cloud.oracle.com>, chọn vùng gần Việt Nam như **Singapore** hoặc **Osaka**.

Vào **Compute → Instances → Create instance**:

| Mục | Chọn |
|---|---|
| Image | **Ubuntu 24.04** |
| Shape | **Ampere A1 (VM.Standard.A1.Flex)**, 2 OCPU, 12 GB |
| SSH keys | **Save private key** — tải file `.key` về và giữ kỹ |

Ghi lại **Public IP address** sau khi máy chạy.

Nếu báo hết tài nguyên, đổi sang vùng khác hoặc thử lại sau; suất Ampere miễn phí thường xuyên hết chỗ.

## 2. Mở cổng 80 và 443

Trong trang máy ảo, bấm tên **Virtual cloud network → Security Lists → Default Security List → Add Ingress Rules**.

Thêm hai luật, mỗi luật một dòng:

| Source CIDR | IP Protocol | Destination Port |
|---|---|---|
| `0.0.0.0/0` | TCP | `80` |
| `0.0.0.0/0` | TCP | `443` |

Bỏ bước này thì trình duyệt sẽ không vào được dù máy vẫn chạy.

## 3. Cài đặt

Kết nối vào máy, thay `<IP>` bằng địa chỉ thật:

```bash
ssh -i duong-dan-toi-file.key ubuntu@<IP>
```

Rồi chạy:

```bash
curl -fsSL https://raw.githubusercontent.com/Helianthusss/video-ab-speed/main/deploy/oracle/setup.sh | sudo bash
```

Lệnh này cài Python, tải mã nguồn, cài Caddy để tự xin chứng chỉ HTTPS, mở tường lửa của máy và tạo dịch vụ tự khởi động cùng máy.

## 4. Đưa video demo lên

Chạy trên **máy tính của bạn**, không phải trên máy ảo:

```bash
scp -i duong-dan-toi-file.key demo.mp4 ubuntu@<IP>:/home/ubuntu/demo.mp4
```

Rồi quay lại phiên SSH:

```bash
sudo bash /opt/video-ab/deploy/oracle/seed.sh /home/ubuntu/demo.mp4
```

Bước lập chỉ mục PTS mất vài phút tùy độ dài video.

## 5. Đặt tên miền và mật khẩu

```bash
sudo bash /opt/video-ab/deploy/oracle/configure.sh
```

Script hỏi ba thứ. Tên miền cứ nhấn Enter để lấy mặc định dạng `1-2-3-4.sslip.io` — dịch vụ này tự trỏ về IP máy bạn, miễn phí, không cần đăng ký. Muốn tên đẹp hơn thì tạo một tên miền con miễn phí ở <https://duckdns.org>, trỏ về IP máy, rồi nhập tên đó.

Mật khẩu nhập vào sẽ không hiện trên màn hình. Đừng dùng mật khẩu dễ đoán vì địa chỉ này công khai và cố định.

Xong bước này Caddy tự xin chứng chỉ Let's Encrypt trong khoảng một phút.

## 6. Kiểm tra

Mở địa chỉ script in ra. Nếu chưa vào được:

```bash
sudo systemctl status video-ab caddy
sudo journalctl -u video-ab -n 50 --no-pager
sudo journalctl -u caddy -n 50 --no-pager
```

| Triệu chứng | Nguyên nhân thường gặp |
|---|---|
| Trình duyệt không kết nối được | Chưa thêm luật cổng 80/443 ở bước 2 |
| Lỗi 400 | `AB_ALLOWED_HOST` khác tên miền đang mở; chạy lại bước 5 |
| Lỗi 503 | Thiếu tài khoản hoặc mật khẩu; chạy lại bước 5 |
| Lỗi chứng chỉ HTTPS | Cổng 80 chưa mở nên Let's Encrypt không xác minh được |

## Bảo trì

```bash
sudo systemctl restart video-ab     # khởi động lại phần mềm
sudo bash /opt/video-ab/deploy/oracle/setup.sh   # cập nhật mã nguồn mới nhất
```

Dữ liệu nằm ở `/opt/video-ab/data`. Đây là ổ đĩa thật nên phép đo trên máy ảo được giữ lại sau khi khởi động lại, khác với các nền tảng dùng đĩa tạm.

## Lưu ý về dữ liệu

Video demo sẽ nằm trên máy chủ công cộng có địa chỉ cố định, không còn ở laptop. Video có hình ảnh người và biển số xe nơi công cộng. Chỉ đưa lên đoạn thật sự cần cho demo, và đặt mật khẩu đủ mạnh.
