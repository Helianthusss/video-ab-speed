# Công cụ click video đo tốc độ hai camera A B

Ứng dụng phục vụ khảo sát tốc độ hành trình phương tiện giữa hai mặt cắt A–B. Người thao tác mở hai video, chọn chính xác từng frame, khớp cùng xe, ghi QC, quản lý lưu lượng và lấy mẫu, rồi xuất CSV, Excel, Word và PDF.

## Kiến trúc

- Backend: Flask 3.1.3 trên Python.
- Frontend: HTML, CSS và JavaScript thuần trong `video_ab/static/`; không có bước build frontend.
- Database: SQLite cục bộ tại `data/survey.sqlite` theo mặc định.
- Video storage: file được sao chép vào `data/media/<sha256>/`; database lưu mã SHA-256 của video trong JSON phiên khảo sát.
- Video import: giao diện upload video theo tiến độ, sau đó server lập chỉ mục frame ở nền và tự nạp lại phiên khi hoàn tất.
- Export: `outputs/<session-id>/` và gói ZIP.
- Authentication: Basic Auth qua `AB_USERNAME` / `AB_PASSWORD`; host ngoài localhost cần `AB_ALLOWED_HOST`. Mặc định chạy localhost.

## Môi trường đã kiểm tra

- Python 3.12.14.
- SQLite đi kèm Python.
- Windows: 31 test đạt sau chuẩn hóa; `Start.bat` dành cho Windows. `Start.command` giữ launcher macOS hiện có.
- Node.js không còn là dependency chạy ứng dụng.

## Cài đặt

```bash
git clone <PRIVATE_REPOSITORY_URL>
cd <REPOSITORY_DIRECTORY>
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Trên Windows PowerShell, kích hoạt bằng `.\.venv\Scripts\Activate.ps1`, hoặc chạy trực tiếp không cần kích hoạt:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m video_ab
```

Có thể bấm đúp `Start.bat`. Môi trường `.venv` phải được tạo trên Windows; không dùng lại môi trường sao chép từ macOS. Xem `docs/CODEBASE_OVERVIEW_VI.md` để hiểu các module và luồng xử lý.

## Biến môi trường

Sao chép `.env.example` thành `.env` nếu cần ghi lại cấu hình cục bộ. Ứng dụng không tự đọc `.env`; hãy export biến trong shell hoặc dùng công cụ quản lý môi trường của hệ điều hành.

- `AB_HOST`: địa chỉ bind, mặc định `127.0.0.1`.
- `AB_PORT`: cổng, mặc định `8765`.
- `AB_DATA_DIR`: thư mục database và media, mặc định `./data`.
- `AB_OUTPUT_DIR`: thư mục tệp xuất, mặc định `outputs/` ở gốc checkout.
- `AB_DEMO_DIR`: thư mục video demo, mặc định `demo/` ở gốc checkout.
- `AB_USERNAME`: tên đăng nhập khi chạy ngoài localhost.
- `AB_PASSWORD`: mật khẩu khi chạy ngoài localhost.
- `AB_ALLOWED_HOST`: domain được phép truy cập khi chạy qua domain/proxy, ví dụ `abspeed.utc2.edu.vn`.
- `AB_YOLO_WEIGHTS`: đường dẫn file weights YOLO trên máy chủ, mặc định `models/yolo26n.pt`.
- `AB_YOLO_DEVICE`: thiết bị chạy YOLO, dùng `cpu`, `0`, hoặc `auto`.

`.env`, database, video, file upload và output đều bị loại khỏi Git.

## Khởi tạo database

```bash
python scripts/init_db.py
```

Ứng dụng tự tạo hai bảng `sessions` và `history` khi mở kết nối database đầu tiên. `video_ab/schema.sql` là schema có thể kiểm tra và dùng để dựng database mới.

Tạo dữ liệu tổng hợp an toàn để thử:

```bash
python demo_build.py
```

Lệnh này tạo video tổng hợp và phiên `SYNTHETIC_KNOWN_ANSWER` trong thư mục runtime bị Git bỏ qua. Không tạo hoặc tải video công khai.

## Chạy development server

```bash
python app.py
```

Mở http://127.0.0.1:8765. Trên macOS có thể bấm đúp `Start.command` sau khi tạo `.venv`.

Để chạy một bản kiểm tra song song trên cổng khác:

```bash
AB_PORT=8766 python app.py
```

## Kiểm thử

Test tự tạo dữ liệu tổng hợp trong thư mục tạm và dọn sau khi chạy; không cần tạo demo thủ công.

```bash
python -m unittest discover -s tests -v
```

Lệnh cũ `python tests.py -q` vẫn được hỗ trợ.

## Phát triển package

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m video_ab
```

Package ứng dụng nằm trong `video_ab/`, công cụ trong `scripts/`, kiểm thử trong `tests/`. `app.py` chỉ giữ entry point tương thích. Xem [sơ đồ và luồng mã nguồn](docs/CODEBASE_OVERVIEW_VI.md).

## Dữ liệu và backup

Không commit `data/`, `demo/`, `outputs/`, database SQLite hoặc video khảo sát. Sao lưu đồng thời:

- `data/survey.sqlite`;
- toàn bộ `data/media/`;
- cấu hình môi trường dùng khi chạy.

Database lưu media ID, còn `index.json` trong kho media được phân giải lại theo thư mục hiện tại. Vì vậy có thể di chuyển một backup đầy đủ gồm database và media sang đường dẫn khác.

### Video khảo sát

Video không nằm trong repository này và không được commit. Repository chỉ chứa mã nguồn và tài liệu.

Video khảo sát được lưu riêng bên ngoài Git. Liên hệ tác giả để được cấp quyền truy cập.

Cách dùng: tải video về máy, mở ứng dụng ở `http://127.0.0.1:8765`, rồi nhập video qua nút chọn tệp của Camera A và Camera B. Ứng dụng tự băm SHA-256, sao chép vào `data/media/<hash>/` và lập chỉ mục PTS. Không cần đặt tệp vào thư mục nào thủ công.

Khi chọn video trên giao diện, ứng dụng hiển thị phần trăm upload. Sau khi upload xong, server tiếp tục chuẩn bị video ở nền: đọc PTS, lập chỉ mục frame và lưu metadata. Video dài vẫn cần chờ xử lý, nhưng trình duyệt không còn đứng im ở một request pending quá lâu. Khi xử lý xong, giao diện tự nạp lại phiên và hiển thị video.

Nên nhập video trên chính máy chạy ứng dụng hoặc dùng video đã nén hợp lý. Khi truy cập qua proxy, IIS/ARR, Cloudflare hoặc tunnel, giới hạn kích thước request và timeout của dịch vụ trung gian vẫn có thể ảnh hưởng video lớn. Để demo nhanh, nên dùng MP4 H.264, 720p, 25 FPS, dài khoảng 1-3 phút.

Video chứa hình ảnh người và phương tiện tại nơi công cộng. Cân nhắc phạm vi chia sẻ trước khi cấp quyền truy cập.

## Upload và triển khai

Hiện ứng dụng nhận hai loại upload:

- video A/B, được lưu cục bộ trong `data/media/` và được lập chỉ mục ở nền;
- snapshot JSON, được nhập thành một phiên mới.

Chưa có upload PDF, Word, Excel hoặc hồ sơ tổng quát. Cơ chế local storage phù hợp chạy một người trên máy cá nhân. Khi triển khai nhiều instance hoặc trên hạ tầng có filesystem tạm thời, cần thiết kế object storage và database dùng chung trước; không chỉ đổi đường dẫn.

### Triển khai sau IIS/ARR hoặc reverse proxy

Ứng dụng có thể chạy sau IIS/ARR, Nginx, Caddy hoặc một reverse proxy khác. Cần cấu hình:

- `AB_HOST=127.0.0.1` nếu proxy chuyển tiếp vào app nội bộ, hoặc `0.0.0.0` nếu container cần bind mọi interface.
- `AB_PORT` trùng cổng proxy chuyển tiếp.
- `AB_ALLOWED_HOST` đúng domain public, ví dụ `abspeed.utc2.edu.vn`.
- `AB_USERNAME` và `AB_PASSWORD` cho đăng nhập.
- Thư mục `AB_DATA_DIR` và `AB_OUTPUT_DIR` phải ghi được bởi user chạy app.
- Timeout của proxy nên đủ dài cho upload video và xử lý nền ban đầu. Với IIS/ARR, kiểm tra thêm giới hạn request body, upload timeout và application pool.

Nếu upload thành công nhưng video chờ lâu, đó thường là thời gian server đọc toàn bộ frame để lập chỉ mục. Nếu upload báo lỗi ngay, kiểm tra giới hạn dung lượng request của proxy. Nếu upload xong rồi báo lỗi video, kiểm tra codec/PTS; nên dùng MP4 H.264 có PTS tăng đúng.

## YOLO nhận diện phương tiện

YOLO là chức năng hỗ trợ rà soát nhanh, không thay thế thao tác chọn mốc A/B của người dùng. Trong tab **Đo video**, sau khi đã nhập đủ hai video và khóa vạch A, B, bấm **AI nhận diện xe A và B**. Phần mềm tự chạy Camera A rồi Camera B cho toàn bộ video.

Để demo nhanh, giao diện có **Chế độ AI**:

- `Nhanh - demo`: mặc định, xử lý thưa hình để giảm thời gian chờ.
- `Rất nhanh`: chờ ít hơn, dễ bỏ sót hơn.
- `Cân bằng`: chậm hơn nhưng theo dõi sát hơn.
- `Kỹ hơn`: xử lý từng hình, phù hợp khi cần rà soát kỹ và máy đủ mạnh.

Khi bấm **Phát video**, phần mềm chỉ ghi log lúc xe cắt qua vạch và đề xuất tốc độ theo thứ tự xe qua vạch. Kết quả AI là gợi ý để rà soát, vì tracker chưa chứng minh chắc chắn hai xe ở Camera A và B là cùng một xe.

Để bật YOLO trên máy chủ, cài thư viện bổ sung và tải weights:

```bash
python -m pip install -r requirements-yolo.txt
mkdir -p models
```

Trên Linux/macOS:

```bash
curl -L -o models/yolo26n.pt   https://github.com/Helianthusss/video-ab-speed/raw/main/models/yolo26n.pt
```

Trên Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path models
Invoke-WebRequest `
  -Uri "https://github.com/Helianthusss/video-ab-speed/raw/main/models/yolo26n.pt" `
  -OutFile "models/yolo26n.pt"
```

Sau khi tải, file weights nằm tại:

```text
models/yolo26n.pt
```

Hoặc đặt biến:

```bash
AB_YOLO_WEIGHTS=/duong/dan/toi/yolo26n.pt
AB_YOLO_DEVICE=cpu
```

Trên máy chủ có GPU NVIDIA và PyTorch CUDA phù hợp, có thể dùng:

```bash
AB_YOLO_DEVICE=0
```

Repository đang cung cấp sẵn weight demo `models/yolo26n.pt` để máy chủ có thể tải trực tiếp. Nếu sau này dùng weight lớn hơn hoặc nhiều phiên bản thử nghiệm, nên chuyển sang GitHub Release, Git LFS hoặc nơi lưu artifact riêng thay vì commit nhiều file `.pt` vào lịch sử Git.

## Tài liệu phát triển

- `docs/USER_GUIDE_VI.md`: hướng dẫn sử dụng từng bước bằng tiếng Việt.
- `docs/HUONG_DAN_SU_DUNG_CO_HINH_MINH_HOA.docx`: hướng dẫn Word có ảnh chụp màn hình, dành cho người mới sử dụng máy tính và chưa có kinh nghiệm nghiên cứu.
- `docs/2026_09_10_Huong_dan_su_dung_phan_mem_click_diem_bo_sung_YOLO.docx`: bản hướng dẫn Word được bổ sung phần YOLO và hướng dẫn nhanh cho bản hiện tại.
- `docs/YOLO_WEB.md`: ghi chú kỹ thuật về YOLO trên web.
- `PROJECT_MANIFEST.md`: kiến trúc, API, dữ liệu và các giới hạn.
- `AI_CONTEXT.md`: ngữ cảnh ngắn dành cho ChatGPT/Codex.
- `docs/METHOD_TRACEABILITY.md`: đối chiếu yêu cầu phương pháp.
- `docs/TEST_REPORT.md`: phạm vi kiểm thử chức năng khoa học.
